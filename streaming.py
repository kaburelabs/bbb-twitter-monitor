from tweepy import OAuthHandler
from tweepy import API
from tweepy import Stream
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from urllib3.exceptions import ProtocolError
from slistener import SListener
import os
from decouple import config
# from key_secret import consumer_key, consumer_secret
# from key_secret import access_token, access_token_secret

api_key = config('API_KEY')
key_secret = config('KEY_SECRET')
access_token = config('ACCESS_TOKEN')
token_secret = config('TOKEN_SECRET')

# consumer key authentication
auth = OAuthHandler(api_key, key_secret)
# access key authentication
auth.set_access_token(access_token, token_secret)
# set up the API with the authentication handler
api = API(auth)
# instantiate the SListener object
listen = SListener(api)
# instantiate the stream object
stream = Stream(auth, listen)
# set up words to hear
# keywords_to_hear = ['#BBB20', "#BBB2020"]
keywords_to_hear = ['#covid19', "#covid-19", "#covid",  "#coronavirus"]

# create a engine to the database
engine = create_engine(config('DATABASE_URL'))
# engine = create_engine('postgresql://postgres:admin@localhost:5432/tweets')

DEVELOPER = config('DEVELOPER', default=False, cast=bool)

if DEVELOPER:
    # if the database does not exist
    if not database_exists(engine.url):
        # create a new database
        create_database(engine.url)


# begin collecting data
while True:
    # maintian connection unless interrupted
    try:
        stream.filter(track=keywords_to_hear)
    # reconnect automantically if error arise
    # due to unstable network connection
    except (ProtocolError, AttributeError):
        continue

