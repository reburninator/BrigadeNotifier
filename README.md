# BrigadeNotifier
A reddit bot that watches for brigades and tells someone about them

# Dependencies
This is a python3 project that works with reddit and MySql. It was created and tested with python 3.8. It uses the PRAW python library for interacting with the reddit API. For the bot to run you need to install the following dependencies in your python environment:

pip install praw
pip install mysql-connector-python

Before the bot will run it needs a MySql database to connect to. Create your database and create a user that has the following database permissions:
* SELECT
* INSERT
* UPDATE
* DELETE
* CREATE
* ALTER
  * INDEX

Give your user with these permissions access to the database. This is the user the bot will use to connect to MySql

# Seeding data
For the bot to run you need to have a subreddit that you feel has been targeted for a brigade and a subreddit that you suspect is doing the brigading. Insert records using these templates to set the app up with that information:

INSERT INTO [SCHEMA_NAME].subreddit_to_watch (target_subreddit_name, brigading_subreddit_name) VALUES ('[TARGET_SUBREDDIT]', '[BRIGADING_SUBREDDIT]');

INSERT INTO [SCHEMA_NAME].target_subreddit (target_subreddit_name, perform_mod_actions, remove_brigade_posts, flair_brigade_users, brigader_flair_text)
values ('[TARGET_SUBREDDIT]', [0 or 1], [0 or 1], [0 or 1], '[FLAIR_TEXT]');

- SCHEMA_NAME is the name of the database schema you created above
- TARGET_SUBREDDIT is the name of the subreddit that's being brigaded
- BRIGADING_SUBREDDIT is the name of the subreddit that's doing the brigading
- FLAIR_TEXT is the text value that you want to set a user's flair to
- O or 1 are bit settings for bot actions. O is FALSE and 1 is TRUE

If perform_mod_actions is set to 0 then the bot will not attempt any actions that require moderator permissions. Set it to 0 if the reddit user running the bot does not have mod permissions in the subreddit that's being targeted by brigades.

If perform_mod_actions is set to 1 then the bot will remove posts from brigading users and flair them, depending on whether those settings are enabled.

Make sure you remove the open and close brackets from your queries before you run them.

# Setting up the reddit app to run the bot
In your reddit preferences select the apps tab create a new app with the following parameters:
- Name: BrigadeNotifier
- Type: Script
- Description: A bot to watch for brigades
- About URL: This can be any valid URL
- Redirect URI: This can be any valid URL

Once the app is added, make sure to add the account that will be running the bot to the list of developers. Otherwise the reddit API may refuse to let you perform some operations.

# Configuring the bot
The config.py file contains initial configurations for the bot. Here's the description of the configurations:

    redditconfig = {'client_id': '',        # set this to the client id of your reddit app
                    'client_secret': '',    # set this to the client secret of your reddit app
                    'user_id': '',          # set this to the user id of the reddit account that will run the app
                    'password': '',         # set this to the password of the reddit account that will run the app
                    'user_agent': 'BrigadeNotifier v0.1 by ReBurnInator'}

    dbconfig = {'hostname': '',             # set this to the server name or IP address of your database server
                'database': '',             # set this to the name of your database
                'user_id': '',              # set this to the user id of the database user account for the db connection
                'password': ''}             # set this to the password of the database user account for the db connection

    itemcounts = {'submissions': 10,        # set this to the number of submissions you want to search for brigades
                  'comments': 100}          # set this to the number of comments you want to search for brigades

    intervals = {'sleep': 30}               # set this to the number of seconds to sleep before the next search

# Running the bot
From the command line run:

python3 BrigadeNotifier.py
