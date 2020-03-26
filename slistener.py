# import packages
from tweepy.streaming import StreamListener
import json
import pandas as pd
from sqlalchemy import create_engine
from datetime import timedelta
import os
from sqlalchemy import text
import datetime
from sqlalchemy import text
from decouple import config


PGHOST="ec2-3-91-112-166.compute-1.amazonaws.com"
PGDATABASE="d20nasndbdf4ji"
PGUSER="wcfuxixmvpozqs"
PGPASSWORD="14e6ab5baf1c583230cfaecd28fc9a1bd3fabdb25d4231a763767bedfeba831a"

DATABASE_URL = config('DATABASE_URL')

# inherit from StreamListener class
class SListener(StreamListener):
    # initialize the API and a counter for the number of tweets collected
    def __init__(self, api = None, fprefix = 'streamer'):
        self.api = api or API()
        # instantiate a counter
        self.cnt = 0
        # create a engine to the database

        self.engine = create_engine(config('DATABASE_URL'))

    # for each tweet streamed
    def on_status(self, status): 
        # increment the counter
        self.cnt += 1
        # parse the status object into JSON
        status_json = json.dumps(status._json)
        # convert the JSON string into dictionary
        status_data = json.loads(status_json)   


        # initialize a list of potential full-text
        full_text_list = [status_data['text']]
        ret_count = 0
        like_count = 0
        reply_count = 0
        orig_post_user = None
        retweet_orig_id_q = None
        retweet_link = None
        orig_post_user_ret = None
        retweet_share =None
        retweet_like = None
        retweet_reply = None     
        quot_share = None
        quot_like = None
        quot_reply = None
        quote_post_id = None
        retweet_id = None

        #print(status_data)
        # print(f"User Id: {status_data['user']['screen_name']}")
        # print(f"Verified: {status_data['user']['verified']}, Language: {status_data['lang']}")        
        # add full-text field from all sources into the list

        if 'extended_tweet' in status_data:
            full_text_list.append(status_data['extended_tweet']['full_text'])

        if 'retweeted_status' in status_data and 'extended_tweet' in status_data['retweeted_status']:
            full_text_list.append(status_data['retweeted_status']['extended_tweet']['full_text'])
            retweet_share = status_data['retweeted_status']['retweet_count']
            retweet_like = status_data['retweeted_status']['favorite_count']
            retweet_reply = status_data['retweeted_status']['reply_count'] 
            orig_post_user_ret = status_data['retweeted_status']['user']['screen_name']
            retweet_id = status_data['retweeted_status']['id_str']
            ### https://twitter.com/Rudysb1hotmail2/status/{retweet_id}

        if 'retweeted_status' in status_data and 'extended_tweet' not in status_data['retweeted_status']:
            full_text_list.append(status_data['retweeted_status']['text'])
            retweet_text = status_data['retweeted_status']['text']
            retweet_share = status_data['retweeted_status']['retweet_count']
            retweet_like = status_data['retweeted_status']['favorite_count']
            retweet_reply = status_data['retweeted_status']['reply_count'] 
            orig_post_user_ret = status_data['retweeted_status']['user']['screen_name']
            retweet_id = status_data['retweeted_status']['id_str']

            ### https://twitter.com/Rudysb1hotmail2/status/{retweet_id}   
        if 'quoted_status' in status_data and 'extended_tweet' in status_data['quoted_status']:
            full_text_list.append(status_data['quoted_status']['extended_tweet']['full_text'])
            quot_share = status_data['quoted_status']['retweet_count']
            quot_like = status_data['quoted_status']['favorite_count']
            quot_reply = status_data['quoted_status']['reply_count'] 
            orig_post_user = status_data['quoted_status']['user']['screen_name']
            quote_post_id = status_data['quoted_status']['id_str'] 

        if 'quoted_status' in status_data and 'extended_tweet' not in status_data['quoted_status']:
            full_text_list.append(status_data['quoted_status']['text'])
            quot_share = status_data['quoted_status']['retweet_count']
            quot_like = status_data['quoted_status']['favorite_count']
            quot_reply = status_data['quoted_status']['reply_count'] 
            orig_post_user = status_data['quoted_status']['user']['screen_name']
            quote_post_id = status_data['quoted_status']['id_str'] 

            ### https://twitter.com/i/web/status/{id_str}   

            #print(orig_post_user)
            # print('Quoted: ',status_data['quoted_status']['user'])
            # print('Quoted: ', status_data['quoted_status'])
            #print('quoted: ',status_data['quoted_status']['favorite_count'])
            #print(status_data)
        # print("#####")
        # print(full_text_list)
        # print("#####")
        # only retain the longest candidate
        full_text = max(full_text_list, key=len)


        if ("RT @" in full_text) and (orig_post_user_ret == None) and ('retweeted_status' in status_data):
            orig_post_user_ret = status_data['retweeted_status']['user']['screen_name']
            retweet_share = status_data['retweeted_status']['retweet_count']
            retweet_like = status_data['retweeted_status']['favorite_count']
            retweet_reply = status_data['retweeted_status']['reply_count'] 
            orig_post_user_ret = status_data['retweeted_status']['user']['screen_name']
            retweet_id = status_data['retweeted_status']['id_str']
            #print("RT sem retweet", status_data)
   
        # if (orig_post_user_ret == None) and (orig_post_user == None):
        #     print(orig_post_user_ret, orig_post_user)
        #     print(status_data)         

        def is_RT(tweet):
            if 'retweeted_status' not in tweet:
                return False      
            else:
                return True

        def is_Quote_of(tweet):
            if 'quoted_status' not in tweet:
                return False      
            else:
                return True

        def reckondevice(tweet):
            if 'iPhone' in tweet['source'] or ('iOS' in tweet['source']):
                return 'iPhone'
            elif 'Android' in tweet['source']:
                return 'Android'
            elif 'Mobile' in tweet['source'] or ('App' in tweet['source']):
                return 'Mobile device'
            elif 'Mac' in tweet['source']:
                return 'Mac'
            elif 'Windows' in tweet['source']:
                return 'Windows'
            elif 'Bot' in tweet['source']:
                return 'Bot'
            elif 'Web' in tweet['source']:
                return 'Web'
            elif 'Instagram' in tweet['source']:
                return 'Instagram'
            elif 'Blackberry' in tweet['source']:
                return 'Blackberry'
            elif 'iPad' in tweet['source']:
                return 'iPad'
            elif 'Foursquare' in tweet['source']:
                return 'Foursquare'
            else:
                return '-'

        #Create a function to see if the tweet is a reply to a tweet of #another user, if so return said user. 
        def is_Reply_to(tweet):
            if ('in_reply_to_screen_name' not in tweet and 'retweeted' in tweet):
                return False      
            else:
                #print('reply tweet', tweet, 'bla', orig_post_user_ret)
                return tweet['in_reply_to_screen_name']


        tweet = {
            'created_at': status_data['created_at'],
            'tweet_id': status_data['id_str'],
            'id_user': status_data['user']['screen_name'],
            'text': full_text,
            'lang': status_data['lang'],
            'location':status_data['user']['location'],
            'device': reckondevice(status_data),
            'reply': is_Reply_to(status_data),


            'is_RT': is_RT(status_data),
            'retweet_user': orig_post_user_ret,
            'retweet_shares': retweet_share,
            'retweet_likes':  retweet_like, 
            'retweet_reply':  retweet_reply,     
            'retweet_url': retweet_id,

            'is_quote': is_Quote_of(status_data),        
            'quoted_user': orig_post_user,
            'quoted_shares': quot_share,
            'quoted_likes':  quot_like, 
            'quoted_reply':  quot_reply,   
            'orig_tweet_quoted': quote_post_id

        }

        # if 'RT @' not in full_text:
        #     print('with no @', status_data)
        #     print(tweet)
        # else:
        #     pass

        # uncomment the following to display tweets in the console
        if self.cnt % 2 == 0:
            print("Writing tweet # {} to the database".format(self.cnt))
        # print("Tweet Created at: {}".format(tweet['created_at']))
        # print(tweet)
        #f
        # print("User Profile: {}".format(tweet['user']))
        #print(tweet)
        # convert into dataframe
        df = pd.DataFrame(tweet, index=[0])

        #print("df")
        from datetime import timedelta
        # convert string of time into date time obejct
        df['created_at'] = pd.to_datetime(df.created_at) 
        print(df)
        # push tweet into database
        df.to_sql('tweet', con=self.engine, if_exists='append', index=False)
        
        task = """
                DELETE FROM tweet
                WHERE created_at IN(
                    SELECT created_at
                        FROM(
                            SELECT created_at
                            FROM tweet
                            WHERE ((DATE_PART('day', now()::timestamp - created_at::timestamp) * 24 
                                                + DATE_PART('hour', now()::timestamp - created_at::timestamp)) * 60 
                                                + DATE_PART('minute', now()::timestamp - created_at::timestamp)) * 60 
                                                + DATE_PART('second', now()::timestamp - created_at::timestamp) > 360) AS tweet_del) """
        

        # d = addresses_table.delete().where(addresses_table.c.retired == 1)
        # d.execute()
        with self.engine.connect() as con:
            # con.execute(task)
            con.execute(text(task))