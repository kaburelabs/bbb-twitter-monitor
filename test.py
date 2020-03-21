import datetime

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output

# pip install pyorbital
from pyorbital.orbital import Orbital
satellite = Orbital('TERRA')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    html.Div([
        html.H4('TERRA Satellite Live Feed'),
        html.Div(id='live-update-text'),
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )
    ])
)


@app.callback(Output('live-update-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_metrics(n):
    lon, lat, alt = satellite.get_lonlatalt(datetime.datetime.now())
    style = {'padding': '5px', 'fontSize': '16px'}
    return [
        html.Span('Longitude: {0:.2f}'.format(lon), style=style),
        html.Span('Latitude: {0:.2f}'.format(lat), style=style),
        html.Span('Altitude: {0:0.2f}'.format(alt), style=style)
    ]


# Multiple components can update everytime interval gets fired.
@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    satellite = Orbital('TERRA')
    data = {
        'time': [],
        'Latitude': [],
        'Longitude': [],
        'Altitude': []
    }

    # Collect some data
    for i in range(180):
        time = datetime.datetime.now() - datetime.timedelta(seconds=i*20)
        lon, lat, alt = satellite.get_lonlatalt(
            time
        )
        data['Longitude'].append(lon)
        data['Latitude'].append(lat)
        data['Altitude'].append(alt)
        data['time'].append(time)

    # Create the graph with subplots
    fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2)
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 10
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}

    fig.append_trace({
        'x': data['time'],
        'y': data['Altitude'],
        'name': 'Altitude',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 1, 1)
    fig.append_trace({
        'x': data['Longitude'],
        'y': data['Latitude'],
        'text': data['time'],
        'name': 'Longitude vs Latitude',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 2, 1)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)




# import packages
from tweepy.streaming import StreamListener
import json
import pandas as pd
from sqlalchemy import create_engine

# inherit from StreamListener class
class SListener(StreamListener):
    # initialize the API and a counter for the number of tweets collected
    def __init__(self, api = None, fprefix = 'streamer'):
        self.api = api or API()
        # instantiate a counter
        self.cnt = 0
        # create a engine to the database
        self.engine = create_engine('sqlite:///tweets.sqlite')


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
            if "RT @alexandrismos: Marcela e Ivy foram gor" in status_data['extended_tweet']['full_text']:
                print('extend RT', status_data['extended_tweet'])  
        if 'retweeted_status' in status_data and 'extended_tweet' in status_data['retweeted_status']:
            full_text_list.append(status_data['retweeted_status']['extended_tweet']['full_text'])
            retweet_share = status_data['retweeted_status']['retweet_count']
            retweet_like = status_data['retweeted_status']['favorite_count']
            retweet_reply = status_data['retweeted_status']['reply_count'] 
            orig_post_user_ret = status_data['retweeted_status']['user']['screen_name']
            retweet_id = status_data['retweeted_status']['id_str']
   
        if 'quoted_status' in status_data and 'extended_tweet' in status_data['quoted_status']:
            full_text_list.append(status_data['quoted_status']['extended_tweet']['full_text'])
            quot_share = status_data['quoted_status']['retweet_count']
            quot_like = status_data['quoted_status']['favorite_count']
            quot_reply = status_data['quoted_status']['reply_count'] 
            orig_post_user = status_data['quoted_status']['user']['screen_name']
            quote_post_id = status_data['quoted_status']['id_str'] 
            if "RT @alexandrismos: Marcela e Ivy foram gor" in status_data['quoted_status']['extended_tweet']['full_text']:
                print('quoted RT', status_data['quoted_status'])
            ### https://twitter.com/i/web/status/{id_str}   

            #print(orig_post_user)
            # print('Quoted: ',status_data['quoted_status']['user'])
            # print('Quoted: ', status_data['quoted_status'])
            #print('quoted: ',status_data['quoted_status']['favorite_count'])
            #print(status_data)


        # only retain the longest candidate
        full_text = max(full_text_list, key=len)
        
        if ("RT @" in full_text) and (orig_post_user_ret == None) and ('retweeted_status' in status_data):
            orig_post_user_ret = status_data['retweeted_status']['user']['screen_name']
            retweet_share = status_data['retweeted_status']['retweet_count']
            retweet_like = status_data['retweeted_status']['favorite_count']
            retweet_reply = status_data['retweeted_status']['reply_count'] 
            orig_post_user_ret = status_data['retweeted_status']['user']['screen_name']
            retweet_id = status_data['retweeted_status']['id_str']

        if ("RT @" in full_text) and (orig_post_user_ret == None) and ('retweeted_status' not in status_data):
            print(status_data)
   
        tweet = {
            'created_at': status_data['created_at'],
            'id_user': status_data['user']['screen_name'],
            'text': full_text,
            'lang': status_data['lang'],
            'location':status_data['user']['location'],

            'retweet_user': orig_post_user_ret,

            'retweet_shares': retweet_share,
            'retweet_likes':  retweet_like, 
            'retweet_reply':  retweet_reply,     
            'retweet_url': retweet_id,
        
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
        print("Writing tweet # {} to the database".format(self.cnt))
        # print("Tweet Created at: {}".format(tweet['created_at']))
        # print(tweet)
        #f
        # print("User Profile: {}".format(tweet['user']))
        #print(tweet)
        # convert into dataframe
        df = pd.DataFrame(tweet, index=[0])

        #print("df")
        # convert string of time into date time obejct
        df['created_at'] = pd.to_datetime(df.created_at)

        # push tweet into database
        df.to_sql('tweet', con=self.engine, if_exists='append')

        with self.engine.connect() as con:
            con.execute("""
                        DELETE FROM tweet
                        WHERE created_at IN(
                            SELECT created_at
                                FROM(
                                    SELECT created_at, strftime('%s','now') - strftime('%s',created_at) AS time_passed
                                    FROM tweet
                                    WHERE time_passed >= 120))""")