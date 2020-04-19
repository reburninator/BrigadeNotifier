import time
import praw
import database
import config

reddit = praw.Reddit(client_id=config.redditconfig['client_id'],
                     client_secret=config.redditconfig['client_secret'],
                     password=config.redditconfig['password'],
                     user_agent=config.redditconfig['user_agent'],
                     username=config.redditconfig['user_id'])


def main():
    if database.create_database_tables():
        print('Database tables have been created for application')

    while True:
        connection = database.connect_to_database()
        target_subreddits = database.get_target_subreddits(connection)

        for target_subreddit in target_subreddits:
            subreddits_to_watch = database.get_subreddits_to_watch(target_subreddit, connection)

            for subreddit_to_watch in subreddits_to_watch:
                brigading_users = get_brigading_users(subreddit_to_watch)

                for brigading_user in brigading_users:
                    look_for_brigade_activity(target_subreddit, brigading_user, connection)

        connection.close()
        print('sleeping')
        time.sleep(config.intervals['sleep'])


def get_brigading_users(subreddit_name):
    subreddit_users = []
    subreddit = reddit.subreddit(subreddit_name)

    print('Getting users for ' + subreddit_name)

    try:
        for submission in subreddit.new(limit=config.itemcounts['submissions']):
            subreddit_users.append({'author': submission.author.name, 'permalink': 'https://www.reddit.com' + submission.permalink,
                                    'type': 'Submission', 'subreddit': subreddit_name, 'thing': submission.id,
                                    'url': submission.url, 'title': submission.title, 'body': ''})
    except:
        print('Error retrieving submissions for %s' % (subreddit_name))

    try:
        for comment in subreddit.comments(limit=config.itemcounts['comments']):
            subreddit_users.append({'author': comment.author.name, 'permalink': 'https://www.reddit.com' + comment.permalink,
                                    'type': 'Comment', 'subreddit': subreddit_name, 'thing': comment.id,
                                    'url': '', 'title': '', 'body': comment.body})
    except:
        print('Error retrieving comments for %s' % (subreddit_name))

    return subreddit_users


def look_for_brigade_activity(target_subreddit, brigading_user, connection):
    search_pattern = 'r/' + target_subreddit + '/comments/' # This looks for direct links for targeted harassment

    if brigading_user['type'] == 'Submission' and \
        (search_pattern in brigading_user['url'] or search_pattern in brigading_user['title']):
            print("Brigade submission found: " + brigading_user['permalink'] + ' - ' + brigading_user['url'])
            first_split = brigading_user['url'].split(search_pattern,1)[1]
            submission_id = first_split.split('/',1)[0]
            handle_brigade(target_subreddit, brigading_user, submission_id, connection)

    if brigading_user['type'] == 'Comment' and search_pattern in brigading_user['body']:
        print("Brigade comment found: " + brigading_user['permalink'] + ' - ' + brigading_user['body'])
        first_split = brigading_user['body'].split(search_pattern,1)[1]
        submission_id = first_split.split('/',1)[0]
        handle_brigade(target_subreddit, brigading_user, submission_id, connection)

    return True


def handle_brigade(target_subreddit, brigading_user, submission_id, connection):
    if database.check_already_reported(brigading_user, connection):
        print("Already reported")
        return

    moderation_settings = database.get_target_subreddit_settings(target_subreddit, connection)

    target_submission = reddit.submission(submission_id)
    cringe_sub_username = brigading_user['author']
    this_submission_username = target_submission.author.name

    message = 'Someone has linked to this subreddit from r/' + \
              brigading_user['subreddit'] + '. \n\n u/' + cringe_sub_username + \
              ' posted this [' + brigading_user['type'] + '](' + brigading_user['permalink'] + ')'

    # Include the text of the comment if the brigade link was posted in a comment
    if brigading_user['type'] == 'Comment':
        message = message + '\n\n>' + brigading_user['body']

    # Sometimes users will make a malicious post in the target subreddit and then link to it in the
    # brigading subreddit. This checks to see if the person who linked to a post is also the person who
    # posted it and, if so, will remove the post if that's the desired behavior
    if moderation_settings['perform_mod_actions'] and moderation_settings['remove_brigade_posts']:
        if cringe_sub_username == this_submission_username:
            target_submission.mod.remove(spam=False, mod_note='Brigading from ' + brigading_user['subreddit'], reason_id=None)
            message = message + '\n\nThe user linked to their own submission in this subreddit, so the submission has been removed.'

    # Checks to see if the user should receive a flair in the subreddit that's being targeted. This helps
    # the mods quickly identify problem users.
    if moderation_settings['perform_mod_actions'] and moderation_settings['flair_brigade_users']:
        reddit.subreddit(target_subreddit).flair.set(cringe_sub_username,
                                                     text=moderation_settings['brigader_flair_text'],
                                                     css_class=moderation_settings['brigader_flair_css_class'])

    # Send a PM to the individual reddit users who should get brigade notifications
    users_to_notify = database.get_users_to_notify(target_subreddit, connection)
    for user_to_notify in users_to_notify:
        reddit.redditor(user_to_notify).message('Possible brigade notification', message)

    # Send modmail to the brigaded subreddit. If the user this script is running as is a mod of the sub
    # then make sure the user DOES NOT have mail perms, otherwise reddit will send it to the moderator
    # discussions list.
    reddit.subreddit(target_subreddit).message('Possible brigade notification', message)
    database.update_brigade_history(target_subreddit, brigading_user, connection)

    print('Brigade reported')


if __name__ == '__main__':
    main()
