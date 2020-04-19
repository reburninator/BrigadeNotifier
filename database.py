import mysql.connector
from mysql.connector import Error
import config


# This method connects to the database and returns the connection object to the caller
def connect_to_database():
    try:
        connection = mysql.connector.connect(host=config.dbconfig['hostname'], database=config.dbconfig['database'],
                                             user=config.dbconfig['user_id'], password=config.dbconfig['password'])

        if connection.is_connected():
            return connection

    except Error as e:
        print('Error connecting to MySQL', e)


# This gets a list of the subreddits to that are potential brigade victims
def get_target_subreddits(connection):
    target_subreddits = []
    query = "SELECT DISTINCT(target_subreddit_name) FROM target_subreddit;"

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            target_subreddits.append(row[0])
    except Error as e:
        print(e.msg)

    return target_subreddits


# This gets a list of the subreddits where brigades are thought to originate
def get_subreddits_to_watch(target_subreddit_name, connection):
    subreddits_to_watch = []
    query = "SELECT brigading_subreddit_name FROM subreddit_to_watch " \
            "WHERE target_subreddit_name = '%s';" % (target_subreddit_name)

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            subreddits_to_watch.append(row[0])
    except Error as e:
        print(e.msg)

    return subreddits_to_watch


# This gets a list of the users to notify of brigades by personal message
def get_users_to_notify(target_subreddit_name, connection):
    users_to_notify = []
    query = "SELECT user_to_notify " \
            "FROM notification_list " \
            "WHERE target_subreddit_name = '%s' " \
            "AND is_active = 1;" % target_subreddit_name

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            users_to_notify.append(row[0])
    except Error as e:
        print(e.msg)

    return users_to_notify


# This gets settings that tell the application what to do when handling brigade notifications
def get_target_subreddit_settings(target_subreddit_name, connection):
    target_subreddit_settings = []

    query = "SELECT perform_mod_actions, remove_brigade_posts, flair_brigade_users, " \
            "brigader_flair_text, brigader_flair_css_class " \
            "FROM target_subreddit " \
            "WHERE target_subreddit_name = '%s'; " % target_subreddit_name

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            perform_mod_actions = True if row[0] == 1 else False
            remove_brigade_posts = True if row[1] == 1 else False
            flair_brigade_users = True if row[2] == 1 else False
            brigader_flair_text = row[3]
            brigader_flair_css_class = row[4]

            target_subreddit_settings.append({'perform_mod_actions': perform_mod_actions,
                                              'remove_brigade_posts': remove_brigade_posts,
                                              'flair_brigade_users': flair_brigade_users,
                                              'brigader_flair_text': brigader_flair_text,
                                              'brigader_flair_css_class': brigader_flair_css_class})
    except Error as e:
        print(e.msg)

    return target_subreddit_settings[0]


# This keeps track of the notifications that have already been sent so mods don't get spammed multiple times
def update_brigade_history(target_subreddit_name, brigading_user, connection):
    query = "INSERT INTO brigade_history (target_subreddit_name, " \
                                         "brigading_subreddit_name, " \
                                         "brigading_username, " \
                                         "item_type, " \
                                         "item_permalink) " \
            "VALUES ('%s','%s','%s','%s','%s');" % (target_subreddit_name,
                                                    brigading_user['subreddit'],
                                                    brigading_user['author'],
                                                    brigading_user['type'],
                                                    brigading_user['permalink'])

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
    except Error as e:
        print(e.msg)


# This checks to see if a brigade has already been reported
def check_already_reported(subreddit_user, connection):
    already_reported = False
    query = "SELECT COUNT(*) FROM brigade_history WHERE item_permalink = '%s';" % subreddit_user['permalink']

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        record = records[0]
        number = record[0]

        if number > 0:
            already_reported = True

    except Error as e:
        print(e.msg)

    return already_reported


# This will create the initial database when the application starts up. If the tables do not exist
# in the target database they will be created. NOTE: You must insert data into the subreddit_to_watch and
# target_subreddit tables before running the application. It will run, but it won't do anything. If you add
# a new table to the application, add it here and it will automatically be created.
#
# This application was written to work with MySql, so if you use a different database application you may
# need to modify the queries to work with your choice of database
def create_database_tables():
    connection = connect_to_database()
    tables_created = False

    # Subreddits to Watch: these are the subreddits that you want to watch for brigades
    # target_subreddit_name: this is the subreddit that has been targeted by brigaders
    # brigading_subreddit_name: this is the subreddit where brigades originate from
    # is_mod: if the user running the script is not a mod of the subreddit being targeted then
    #         the bot needs to know so it doesn't try to perform mod actions
    #         0 = False, 1 = True
    query = "CREATE TABLE IF NOT EXISTS %s.subreddit_to_watch ( " \
            "subreddits_to_watch_id int NOT NULL AUTO_INCREMENT, " \
            "target_subreddit_name varchar(45) NOT NULL, " \
            "brigading_subreddit_name varchar(45) NOT NULL, " \
            "added_on datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, " \
            "PRIMARY KEY (subreddits_to_watch_id) " \
            ");" % config.dbconfig['database']

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        tables_created = True
    except Error as e:
        print(e.msg)

    # Target subreddit: These are the subreddits being targeted. This allows for options
    #                   to be set at the subreddit level, like whether to perform mod
    #                   actions on the things it finds
    # target_subreddit_name: this is the subreddit that has been targeted by brigaders
    # perform_mod_actions: determine whether to

    query = "CREATE TABLE IF NOT EXISTS %s.target_subreddit (" \
            "target_subreddit_id INT NOT NULL AUTO_INCREMENT, " \
            "target_subreddit_name VARCHAR(45) NOT NULL, " \
            "perform_mod_actions INT NOT NULL DEFAULT 1, " \
            "remove_brigade_posts INT NOT NULL DEFAULT 1, " \
            "flair_brigade_users INT NOT NULL DEFAULT 1, " \
            "brigader_flair_text VARCHAR(25) NULL, " \
            "brigader_flair_css_class VARCHAR (200) NULL, " \
            "created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, " \
            "PRIMARY KEY (target_subreddit_id)" \
            ");" % config.dbconfig['database']

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        tables_created = True
    except Error as e:
        print(e.msg)

    # Brigade History: Keeps track of brigades that have been reported to a subreddit so
    #                  so that they aren't reported again.
    # target_subreddit_name: this is the subreddit that has been targeted by brigaders
    # brigading_subreddit_name: this is the subreddit where brigades originate from
    # brigading_username: this is the name of the reddit user who linked to the target subreddit
    # item_type: Comment or Submission
    # item_permalink: link to the brigading user's submission or comment
    query = "CREATE TABLE IF NOT EXISTS %s.brigade_history ( " \
            "brigade_watchlist_id int NOT NULL AUTO_INCREMENT, " \
            "target_subreddit_name varchar(45) NOT NULL, " \
            "brigading_subreddit_name varchar(45) NOT NULL, " \
            "brigading_username varchar(25) NOT NULL, " \
            "item_type varchar(15) NOT NULL, " \
            "item_permalink varchar(200) NOT NULL, " \
            "added_on datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, " \
            "PRIMARY KEY (brigade_watchlist_id) " \
            "); " % config.dbconfig['database']

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        tables_created = True
    except Error as e:
        print(e.msg)

    # Notification list: If a user is in this list then they'll receive brigade
    #                    notifications via PM in addition to the modmail
    # target_subreddit_name: this is the subreddit that has been targeted by brigaders
    # user_to_notify: the user who receives the PM notification
    # is_active: allows notifications to be turned off for a user. 0 = off, 1 = on
    query = "CREATE TABLE IF NOT EXISTS %s.notification_list ( " \
            "notification_list_id INT NOT NULL AUTO_INCREMENT, " \
            "target_subreddit_name VARCHAR(45) NOT NULL, " \
            "user_to_notify VARCHAR(25) NOT NULL, " \
            "is_active INT NOT NULL DEFAULT 1, " \
            "created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, " \
            "PRIMARY KEY (notification_list_id) " \
            "); " % config.dbconfig['database']

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        tables_created = True
    except Error as e:
        print(e.msg)

    connection.close()
    return tables_created