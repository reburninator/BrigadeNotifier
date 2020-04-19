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