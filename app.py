
# stop words

# from nltk.corpus import stopwords
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from nltk.tokenize import TweetTokenizer
import nltk
from unicodedata import normalize
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import numpy as np
from decouple import config
import psycopg2
import string
import re
import os
import plotly_express as px
from urllib3.exceptions import ProtocolError
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import create_engine
import pandas as pd
import dash_table
from dash.dependencies import Output, Input, State
import dash_html_components as html
import dash_core_components as dcc
import dash
from datetime import timedelta

import visdcc

# nltk.download('stopwords')

DATABASE_URL = config('DATABASE_URL')

con = psycopg2.connect(DATABASE_URL, sslmode='require')

app_name = "Twitter Monitor Dashboard"

# CSS EXTERNAL FILE
external_stylesheets = [dbc.themes.BOOTSTRAP,
                        'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
                        'https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css',
                        "https://fonts.googleapis.com/css2?family=Squada+One&display=swap"]


scripts_jquery = [{'src': "https://code.jquery.com/jquery-3.4.1.min.js"}]


# Defining the instance of dash
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=scripts_jquery,
                meta_tags=[
                    {
                        "name": "viewport",
                        "content": "width=device-width, initial-scale=1, maximum-scale=1",
                    }
                ])

app.title = app_name

# server instance to run map when deploying
server = app.server

# Since I am adding callbacks to elements that don’t ~
# exist in the app.layout as they are spread throughout files
app.config.suppress_callback_exceptions = True
app.css.config.serve_locally = True


app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script type='text/javascript' src='https://platform-api.sharethis.com/js/sharethis.js#property=5e8113b5c213f90019450492&product=inline-share-buttons&cms=website' async='async'></script>
        <script src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


stop_words = {'hadn', "isn't", 'ma', "shouldn't", 'an', 'to', 'nor', 'why', "didn't", 'against',
              'haven', 'in', 'from', 'off', 'as', 'its', "should've", 'hasn', "you've", "hasn't", 'been', 'his',
              "that'll", 'not', 'after', 'all', 'mightn', 'again', 'll', "you'll", 'by', 'what', 'there', 'most',
              'this', 'ours', 't', 'further', 'should', 'wouldn', 'because', 'have', 'those', 'don', 'up', 'too',
              'o', 'these', 'does', 'down', "she's", 'itself', 'a', 'of', 'aren', 'she', 'now', 'weren', 'then',
              'own', 'but', 'through', 'who', 'than', 'needn', 'are', "needn't", 'yourselves', 'myself', 'while',
              'where', "won't", 'hers', "haven't", 'him', 'some', 'shan', 'above', 'be', 'at', 'their', 'if',
              "mustn't", 'only', 'on', 'more', 'being', 'no', 'them', 've', "weren't", "wasn't", "aren't",
              'here', 'shouldn', 'for', 'mustn', "you're", 'didn', 'under', 'did', 'such', 'between',
              'am', 'just', 'it', 'once', "hadn't", 'very', 'each', "mightn't", 'had', "shan't", 'we',
              'will', 'he', 'themselves', 'the', 'about', 'over', 'few', 'during', "couldn't", 'isn',
              'do', 'yours', 'below', "you'd", 'until', 'with', 'i', "don't", 'her', 'or', 'other',
              'same', 's', 'having', 'ourselves', 'and', 'before', 'any', 'your', 'our', 'ain', 'my',
              'is', 'when', 'yourself', 'both', 'was', 'herself', 'out', 're', 'himself', 'm', 'they',
              'won', 'theirs', 'doesn', 'you', "doesn't", 'which', 'couldn', 'so', 'y', 'how', 'whom',
              'has', 'doing', 'me', 'wasn', 'were', 'd', 'into', 'that', 'can', "wouldn't", "it's"}


def navbar(logo="/assets/logo-placeholder.png", height="35px",  appname="PlaceHolder Name"):

    navbar = dbc.Navbar(
        [dbc.Container(
            [
                dbc.Col(html.A(
                    # Use row and col to control vertical alignment of logo / brand
                        html.Div(
                            "trich.ai", className="trich-navbar white font-xl", ),
                        href="https://trich.ai",
                        ), width=4),
                dbc.Col(dbc.NavbarBrand(
                    appname, className="font-md text-white"),
                    className="text-right", width=8)], style={"maxWidth": "1140px"}),
         ],
        color="#393939", className="bottom32",  # className="bottom16",
        # style={'height': '100px', "borderBottom":".5px solid lightgrey", "padding":"18px 0px"}

        # dark=True,
    )

    return navbar


def create_footer():
    p = html.Div(
        children=[
            html.Span('Developed By: '),
            html.A('trich.ai | Data Intelligence Solutions',
                   style={'textDecoration': 'none', 'color': '#ffffff'},
                   href='https://trich.ai', target='_blank')
        ], style={'float': 'right', 'marginTop': '8px',
                  'fontSize': '18px', 'color': '#ffffff'}
    )

    span_style = {'horizontalAlign': 'right',
                  'paddingLeft': '1rem',
                  'fontSize': '15px',
                  'verticalAlign': 'middle'}

    kaggle = html.A(
        children=[
            html.I([], className='fab fa-kaggle'),
            html.Span('Kaggle', style=span_style)
        ], style={'textDecoration': 'none', 'color': '#ffffff', 'marginRight': '20px'},
        href="https://www.kaggle.com/kabure/kernels",
        target='_blank')

    mapbox = html.A(
        children=[
            html.I([], className='fab fa-python'),
            html.Span('Dash Plotly', style=span_style)
        ], style={'textDecoration': 'none', 'color': '#ffffff', 'marginRight': '20px'},
        href='https://plot.ly/dash/', target='_blank')

    font_awesome = html.A(
        children=[
            html.I([], className='fa fa-font-awesome'),
            html.Span('Font Awesome', style=span_style)
        ], style={'textDecoration': 'none', 'color': '#ffffff', 'marginRight': '20px'},
        href='http://fontawesome.io/', target='_blank')

    datatables = html.A(
        children=[
            html.I([], className='fa fa-github'),
            html.Span('trich.ai\n Github', style=span_style)
        ], style={'textDecoration': 'none', 'color': '#ffffff', 'marginRight': '20px'},
        href='https://github.com/kaburelabs/', target='_blank')

    ul1 = html.Div(
        children=[
            html.Li(mapbox, style={
                    'display': 'inline-block', 'color': '#ffffff'}),
            html.Li(font_awesome, style={
                    'display': 'inline-block', 'color': '#ffffff'}),
            html.Li(datatables, style={
                    'display': 'inline-block', 'color': '#ffffff'}),
            html.Li(kaggle, style={
                    'display': 'inline-block', 'color': '#ffffff'}),
        ],
        style={'listStyleType': 'none', 'fontSize': '30px'},
    )

    hashtags = 'plotly,dash,trich.ai,bbb20,data, streaming'
    tweet = 'trich.ai Twitter Live Monitor, a cool dashboard with Plotly Dash!'
    twitter_href = 'https://twitter.com/intent/tweet?hashtags={}&text={}'\
        .format(hashtags, tweet)
    twitter = html.A(
        children=html.I(children=[], className='fa fa-twitter'),
        title='Tweet me!', href=twitter_href, target='_blank')

    li_right_first = {'lineStyletype': 'none', 'display': 'inline-block'}
    li_right_others = {k: v for k, v in li_right_first.items()}
    li_right_others.update({'margin-left': '10px'})
    ul2 = html.Ul(
        children=[
            html.Li(twitter, style=li_right_first),
            # html.Li(github, style=li_right_others),
        ],
        style={
            'position': 'fixed',
            'right': '1.5rem',
            'bottom': '75px',
            'fontSize': '60px'
        }
    )
    div = html.Div([p, ul1, ul2])

    footer_style = {
        'fontSize': '2.2rem',
        'backgroundColor': '#3C4240',
        # 'padding': '2.5rem',
        'marginTop': '5rem',
        'display': 'inline-block', 'padding': '16px 32px 8px'
    }
    footer = html.Footer(div, style=footer_style, className='twelve columns')
    return footer


app.layout = html.Div([
    html.Div(className="sharethis-inline-share-buttons"),
    navbar(logo='/assets/fundo_transp-b.png', appname="Twitter Live Monitor"),

    html.Div([
        html.Div(
            [
                dbc.Row(
                    dbc.Col([dbc.Alert(
                        [
                            html.Div("Welcome to trich.ai Twitter Streaming WebApp!",
                                     className="font-xl bottom16"),
                            html.Div([
                                html.Div(
                                    ["NOTE: The application auto updates the content every 30 seconds and as it is a free version of Heroku platform, sometimes it can 'sleep' and stop to collect the data."]),
                                html.Div(
                                    ["As it's hosted in a free Heroku host and it can be a little slow or don't render correctly the components. "])
                            ], className="font-sm"
                            ),
                            html.Hr(),
                            html.Div(
                                "Feel free to contact us for a Proof of Concept (POC) for your brand, enterprise or even if you have interest in another WebApp types.",
                                className="font-md",
                            ),
                        ], className="text-center", color='info', dismissable=True
                    )
                    ], width=12), className="margin-auto bottom32"),

                dbc.Row([
                    dbc.Col([html.Div("COVID-19 Tweets Live Monitor", className="text-center font-xl"),
                             html.Div("This web app monitor some hashtags about the COVID-19 to \
                                 understand what's happening at this moment based on this subject.", className="font-md"),
                             html.Div(["This monitor is developed and maintained by ",
                                       html.A('trich.ai', href='https://trich.ai', style={"color": "blue"},
                                              target='_blank'),
                                       " that tries to bring some insights and understand about the subjects related to COVID-19"], className="font-md")
                             ], className="margin-auto bottom32", width={"size": 10, "offset": 1}),
                    dbc.Col(dbc.Row([

                            dbc.Col([
                                html.Img(
                                    src='/assets/Rede_Globo_logo.png',
                                    style={
                                        'width': '5vw'
                                    }
                                )
                            ], className='text-center', width=4),
                            dbc.Col([
                                html.Img(
                                    src='/assets/89846551_1428521667330586_8342275172711006208_n.png',
                                    style={
                                        'width': '200px'
                                    }
                                )
                            ], className='text-center', width=4),
                            dbc.Col([
                                html.Img(
                                    src='/assets/twitter_logo.svg',
                                    style={
                                        'width': '85px'
                                    }
                                )
                            ], className='text-center', width=4)
                            ], className="width-100"),
                            width={"size": 10, "offset": 1}, className="width-100")
                ], className="displayColor margin-auto padding32 bottom32"),

                html.Div(id='df-sharing', style={'display': 'none'}),
                dbc.Row([
                    # dcc.Loading(loading_state={'is_loading':False}),
                    dbc.Col(html.Div([

                        # html.H4("TOP 20 most common words", style={'textAlign':'center','margin':}),
                        dcc.Graph(id='tfidf-graph')
                    ]), width=5, className="width-100"),
                    dbc.Col(html.Div(id='live-values',  # className='nine columns',
                                     style={
                                         'margin': '60px 0 0',
                                     },
                                     className="width-100 displayTextBg"), width=7),
                    dcc.Interval(
                        id='graph-update',
                        interval=5*1000,
                        n_intervals=0
                    )
                    # ], className='six columns', style={ 'height': '350px', 'margin':'60px 0'}),
                ], style={'height': '500px'}, className="width-100 bottom32"),


                dbc.Row([
                    dbc.Col(
                        html.Div("MAIN TWEETS FOR THIS MOMENT"), className="text-center font-xl width-100", width=12),
                ], className="bottom32"),

                dbc.Row([
                    dbc.Col([html.Div([html.Div("MOST SHARED TWEETS NOW", className="font-lg text-center"),
                                       html.Div("(Trends at this moment)", className="font-sm text-center bottom16")],
                                      className="text-center"),
                             html.Div(id='output-iframe-share',
                                      style={'height': '750px',
                                             'overflowY': 'auto',
                                             'padding': "0 21px"},
                                      className="displayColor")],
                            width=6),

                    dbc.Col([html.Div([html.Div("MOST RETWEETED TWEETS", className="font-lg text-center"),
                                       html.Div("(More Long term tweets - not necessarily at this moment)", className="font-sm text-center bottom16")],
                                      className="text-center"),
                             html.Div(id='output-iframe-rt', style={'height': '750px',
                                                                    'overflowY': 'auto',
                                                                    'direction': 'rtl', 'padding': "0 21px"},
                                      className="displayColor")],
                            width=6)
                ], className="text-center bottom64"),

                dbc.Row([
                    dbc.Col(html.Div(["MOST IMPORTANT MENTIONS, HASHTAGS AND USERS"],
                                     className='text-center font-xl'), width=12),
                ], className="bottom32"),

                dbc.Row([

                    # Menções, Hashtags e usuários mais ativos
                    # time_inf = round(pd.Timedelta(df.created_at.max() - df.created_at.min()).seconds / 60)
                    dbc.Col([
                        # <i class="fas fa-at"></i>
                        html.Div([
                            html.I([],
                                   className='fa fa-at font-xl bold'),
                            html.Span(
                                ' MENTIONS', className="font-lg bold", style={'font': 'sans-serif'}),
                            html.Div('MOST IMPORTANT MENTIONS',
                                     className="font-xs")

                        ], style={'textDecoration': 'none'}, className='text-center margin-auto'),
                        dcc.Graph(id='graph-2')
                    ], width=4),

                    dbc.Col([
                        # <i class="fas fa-hashtag"></i>
                        html.Div([
                            html.I([], className='fa fa-hashtag font-xl'),
                            html.Span(
                                ' HASHTAGS', className="font-lg bold", style={'font': 'sans-serif'}),
                            html.Div("MOST IMPORTANT HASHTAGS",
                                     className="font-xs")
                        ], style={'textDecoration': 'none'}, className='text-center margin-auto'),
                        dcc.Graph(id='graph-3')
                    ], width=4),

                    dbc.Col([
                        # <i class="fas fa-comment-medical"></i>
                        html.Div([
                            html.I([], className="far fa-users bold font-xl"  # 'fas fa-comment-medical font-xl'
                                   ),
                            html.Span(
                                ' USERS', className="font-lg bold", style={'font': 'sans-serif'}),
                            html.Div("MOST ACTIVE USERS", className="font-xs")
                        ], style={'textDecoration': 'none'}, className='text-center margin-auto'),
                        dcc.Graph(id='graph-4')
                    ], width=4)

                ], className="bottom32")
            ]),

        dbc.Row([
            dbc.Col(html.Div([
                dcc.Graph(id='graph-5')
            ], className="width-100"), width=12),
        ]),


    ], className='container'),
    create_footer()
], style={'overflow': 'hidden'})


def calc_tweet_metrics(df):
    total_tweets = len(df)
    unique_texts = df['text'].nunique()
    unique_texts_perc = round(df['text'].nunique() / len(df) * 100, 2)
    unique_users = df['id_user'].nunique()
    top_20_posts_perc = round((df.text.value_counts().reset_index().rename(
        columns={'text': 'total', 'index': 'text'})[: 20].total.sum() / len(df)) * 100, 2)
    top_20_posts = df.text.value_counts().reset_index().rename(
        columns={'text': 'total', 'index': 'text'})[: 20].total.sum()
    df_dup = df.drop_duplicates('text', keep='last').sort_values(
        'retweet_shares', ascending=False)
    zero_tweets = len(df_dup[df_dup['retweet_user'].isin(
        [None]) & df_dup['quoted_user'].isin([None])])
    zero_retweets_perc = round(zero_tweets / len(df) * 100, 2)
    time_inf = round(pd.Timedelta(df.created_at.max() -
                                  df.created_at.min()).seconds / 60)
    # print(df.created_at.max(), df.created_at.min())
    return [total_tweets, unique_texts, unique_texts_perc, unique_users,
            top_20_posts, top_20_posts_perc, zero_tweets, zero_retweets_perc, time_inf]


def calc_last_most_tweeted(df):
    tweets_list = df.text.value_counts().reset_index().rename(columns={'text': 'total',
                                                                       'index': 'text'})[: 20].reset_index().drop('index', axis=1)

    return tweets_list


def remove_punct(text):
    text = text.lower()
    text = "".join([char for char in text if char not in string.punctuation])
    text = re.sub('[0-9]+', '', text)
    return text


def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


def remove_URL(text):
    url = re.compile(r'https?://\S+|www\.\S+')
    return url.sub(r'', text)


def remove_at(text):
    clean = re.sub(r'@[A-Za-z0-9]+', '', text)
    return clean


@ app.callback(Output('df-sharing', 'children'),
               [Input('graph-update', 'n_intervals')])
def _update_div1(val_1):

    df = pd.read_sql_query("SELECT * from tweet", con)

    return df.to_json(date_format='iso', orient='split')


@ app.callback(Output('live-values', 'children'),
               [Input('df-sharing', 'children')])
def _update_div1(df):
    df_ = pd.read_json(df, orient='split')
    df_.created_at = pd.to_datetime(df_.created_at)
    total_tweets, unique_texts, unique_texts_perc, unique_users, \
        top_20_posts, top_20_posts_perc, zero_retweets, zero_retweets_perc, time_inf = calc_tweet_metrics(
            df_)
    # df = df.sort_values('created_at')
    return html.Div([
        html.Div([
            dbc.Row([
                dbc.Col(html.Div(
                    [f"Tweets on the last {time_inf} minutes"], className="text-center font-xl"), width=12)
            ]),
            dbc.Row(
                [
                    dbc.Col([
                        html.Div([
                            html.I([], className='far fa-comment-dots'),
                            # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                        ], style={'textDecoration': 'none'}, className="font-xl text-center bold"),

                        html.Div(id='display-6',
                                 children=[html.Div(total_tweets)], className="font-lg text-center bold"
                                 ),
                        html.Div(
                            children="Total Tweets", className="font-md text-center")
                    ], width={"size": 4, "offset": 2}),

                    dbc.Col([
                            html.Div([
                                html.I([], className='far fa-user'),
                                # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                            ], style={'textDecoration': 'none'}, className="font-xl text-center bold"),
                            html.Div(id='display-8',
                                     children=[html.Div(unique_users)], className="font-lg text-center bold"),
                            # <i class="fas fa-users"></i>
                            html.Div(
                                children="Unique Users", className="font-md text-center")
                            ], width={"size": 4, "offset": 0}),
                ],  className="margin-auto"),
        ]),
        dbc.Row([
            dbc.Col([
                    html.Div([
                        html.I([], className='fas fa-retweet'),
                        # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                    ], style={'textDecoration': 'none'}, className="font-xl text-center bold"),
                    html.Div(id='display-7',
                             children=[html.Div(f"{unique_texts_perc}%")], className="font-lg text-center bold"),
                    # <i class="fas fa-retweet"></i>
                    # html.Div(f"({unique_texts})", style={'textAlign':'center'}),
                    html.Div(
                        children="Unique tweets", className="font-md text-center")
                    ], width=4),
            dbc.Col([
                    html.Div([
                        html.I([], className='fas fa-paragraph'),
                        # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                    ], style={'textDecoration': 'none'}, className="font-xl text-center bold"),
                    html.Div(id='display-5',
                             children=[html.Div(f"{zero_retweets_perc}%")], className="font-lg text-center bold"),
                    # html.Div(f"({zero_retweets})", style={'textAlign':'center'}),
                    html.Div(
                        children="(No RT or Quote)", className="font-md text-center")

                    ], width=4),
            dbc.Col([
                    html.Div([
                        html.I([], className='fas fa-fire-alt'),
                        # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                    ], style={'textDecoration': 'none'}, className="font-xl text-center bold"),
                    html.Div(id='display-9',
                             children=[html.Div(f"{top_20_posts_perc}%")], className="font-lg text-center bold"),
                    # html.Div(f"({top_20_posts_perc}%)", style={'textAlign':'center'}),
                    html.Div(
                        children="Top 20 posts", className="font-md text-center")
                    ], width=4),
        ])

    ], className="padding32")


def resume_tweets(df, type='share'):

    list_twt = []

    for i in list(range(30)):

        user = df['id_user'].to_list()[i]
        tweet = int(df['tweet_id'].to_list()[i])
        is_rt = df['is_RT'].to_list()[i]

        link = df['retweeted_url'].to_list()[i]

        if link == None:
            link = df['quote_url'].to_list()[i]
        else:
            pass

        if link == None:
            link = "https://twitter.com/{user}/status/{tweet}"
        else:
            pass

        if type == 'share':
            text = f"#{i+1} Most Shared - Total Shares: {df['count'].to_list()[i]} "
        else:
            text = f"#{i+1} Most Retweeted - Total Shares: {df['count'].to_list()[i]}"
        # print(link)
        list_twt.append(html.Div([html.Div(f"{text}", style={'textAlign': 'center', 'fontWeight': 'bold', "direction": "ltr",
                                                             'fontSize': '18px'}),
                                  html.Blockquote(
                                      html.A(href=link), className="twitter-tweet", style={'width': "498px"}),
                                  visdcc.Run_js(id="javascript2",
                                                run="twttr.widgets.load()")],
                                 style={"margin": "48px 0"}))

    list_twt.append(visdcc.Run_js(id="javascript",
                                  run="twttr.widgets.load()"))

    return list_twt


@ app.callback([Output('output-iframe-share', 'children'),
                Output('output-iframe-rt', 'children')],
               [Input('df-sharing', 'children'),
                Input('graph-update', 'n_intervals')])
def _update_div1(df, n_val):

    df_ = pd.read_json(df, orient='split')
    # time.sleep(30)
    shared_tweets_list = []
    rt_tweets_list = []
    cols = ['text', 'id_user', 'tweet_id',
            'is_RT', 'retweet_user',
            'quote_url', 'retweeted_url', 'count']

    df_['count'] = df_.groupby(["text"])["tweet_id"].transform("count")
    df_princ = df_.drop_duplicates('text', keep='first').sort_values(
        'count', ascending=False)[cols]
    df_princ1 = df_.drop_duplicates('text', keep='last').sort_values(
        'retweet_shares', ascending=False)[cols].rename(columns={'retweet_shares': "# RT's"})

    # print(df_princ.columns)
    # df = df_[df_.index.isin(df_.text.drop_duplicates(keep='last').index)].sort_values('retweet_likes', ascending=False)[:20]

    shared_tweets_list = resume_tweets(df_princ)
    rt_tweets_list = resume_tweets(df_princ1, type='rt')

    return [shared_tweets_list, rt_tweets_list]


@ app.callback([Output('recommender-table', 'data'),
                Output('recommender-table2', 'data')],
               [Input('df-sharing', 'children')])
def _update_div1(df):
    df_ = pd.read_json(df, orient='split')
    # df = pd.read_sql_query("SELECT text from tweet", con)
    df_['count'] = df_.groupby(["text"])["created_at"].transform("count")
    df_princ = df_.drop_duplicates('text', keep='last').sort_values('count', ascending=False)[
        ['count', 'text', 'retweet_shares']].rename(columns={'retweet_shares': "# RT's"})
    df_princ1 = df_.drop_duplicates('text', keep='last').sort_values('retweet_shares', ascending=False)[
        ['retweet_shares', 'text', 'count']].rename(columns={'retweet_shares': "# RT's"})

    return [df_princ[:40].to_dict('rows'), df_princ1[(df_princ1['count'] >= 15) & (df_princ1["# RT's"])][:40].to_dict('rows')]


def creating_hist():
    hist_vals = pd.DataFrame(data=[], columns=['created_at', 'index'])

    return hist_vals


hist_vals = pd.DataFrame(data=[], columns=['created_at', 'index'])


@ app.callback(Output('graph-5', 'figure'),
               [Input('df-sharing', 'children')])
def _update_div1(df):

    global hist_vals

    df_ = pd.read_json(df, orient='split')
    # df_.drop('index', axis=1, inplace=True)
    df_.created_at = pd.to_datetime(df_.created_at)
    df_.set_index('created_at', inplace=True)

    hist_vals = hist_vals.append(df_.resample('1min').count()['index'].sort_index(
        ascending=False).reset_index()[1:-1].to_dict('row'))
    hist_vals = hist_vals.reset_index().drop('level_0', axis=1)
    hist_vals = hist_vals.sort_values(
        'created_at', ascending=False).drop_duplicates('created_at', keep='last')

    fig = px.line(hist_vals[:72], x='created_at', y='index',
                  title='The count of tweets for each minute')

    fig.update_layout(xaxis=dict(title='Date/Minutes'),
                      yaxis=dict(title='Count Total'), title_x=.5,
                      margin=dict(r=0))

    return fig


punct = [i for i in string.punctuation if i not in ['#', '@']]


def clean_text(text):

    # Removing links
    text_strip_links = strip_links(text)

    # Removing HashTags
    text_strip_hash = strip_all_entities(text_strip_links)

    # remove numbers
    text_nonum = re.sub(r'\d+', '', text_strip_hash)
#     print(text_nonum)

    # remove punctuations and convert characters to lower case
    text_nopunct = "".join([char.lower()
                            for char in text_nonum if char not in punct])
#     print(text_nopunct)
    text_accents = normalize('NFKD', text_nopunct).encode(
        'ASCII', 'ignore').decode('ASCII')
    # substitute multiple whitespace with single whitespace
    # Also, removes leading and trailing whitespaces
    text_no_doublespace = re.sub('\s+', ' ', text_accents).strip()

    return text_no_doublespace


def strip_links(text):
    link_regex = re.compile(
        '((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)', re.DOTALL)
    links = re.findall(link_regex, text)
    for link in links:
        text = text.replace(link[0], ', ')
    return text


def strip_all_entities(text):
    entity_prefixes = ['@', '#']
    for separator in string.punctuation:
        if separator not in entity_prefixes:
            text = text.replace(separator, ' ')
    words = []
    for word in text.split():
        word = word.strip()
        if word:
            if word[0] not in entity_prefixes:
                words.append(word)
    return ' '.join(words)


new_stopwords = ['rt', 'en', 'la', 'el', 'amp', 'para', 'de',
                 'del', 'con', 'las', 'al', 'le', 'una', 'si',
                 'un', 'et', 'pour', 'por', 'los', 'es', 'para',
                 'es', 'des', 'se', 'que', 'su', 'mas', 'ya', 'lo',
                 'ni', 'coronavirus', ]


@ app.callback(Output('tfidf-graph', 'figure'),
               [Input('df-sharing', 'children'),
                Input('graph-update', 'n_intervals')])
def _update_tfidf(data, val2):

    df_ = pd.read_json(data, orient='split')
    text_cleaned = df_.text.apply(strip_all_entities)
    text_cleaned = text_cleaned.apply(strip_links)

    text_cleaned = df_.text.apply(clean_text)
    tt = TweetTokenizer()

    new_stopwords_list = stop_words.union(new_stopwords)

    vectorizer = TfidfVectorizer(ngram_range=(1, 3), min_df=15, max_df=150,
                                 stop_words=new_stopwords_list,
                                 #  [
                                 #              'bbb', 'redebbb', 'do', 'rt', 'festabbb', 'que', 'da', 'em', 'com', 'esse',
                                 #              'eu', 'nao', 'de', 'no', 'pra', 'pro', 'uma', 'so', 'dos', 'ele',
                                 #              'ele', 'se', 'um', 'ta', 'vai', 'na', 'essa', 'me', 'meu', 'faz',
                                 #              'ja', 'ela', 'to', 'mais', 'mas', 'tem', 'por', 'quem', 'para',
                                 #              'os', 'as', 'ser', 'ver', 'isso', 'como', 'quando', 'comecar',
                                 #              'ai', 'ate', 'foi', 'voce', 'hoje', 'gente', 'muito', 'fazer',
                                 #              'pq', 'agora', 'falando', 'casa', 'vamos', 'tudo', 'quero', 'eles',
                                 #              'dois', 'ter', 'minha', 'dia', 'esta', 'sobre', 'cara', 'aqui',
                                 #              'ou', 'todo', 'vou', 'mesmo', 'dele', 'pelo', 'nem', 'nunca', 'cinema',
                                 #              'video', 'ao', 'voces', 'ne', 'ainda', 'ne', 'pode', 'sabe', 'deus',
                                 #              'bigbrotherbrasil', 'realityshow', 'tv', 'via', 'entretenimento',
                                 #              'reality', 'personalidade', 'pt', 'tirei', 'comeca', 'comecou',
                                 #              'logo', 'edicao', 'alguem', 'amo', 'nada', 'mundo', 'vem', 'sair',
                                 #              'jogo', 'estamos', 'era', 'podio', 'dela', 'forte', 'ninguem',
                                 #              'nosso', 'depois', 'assim', 'sua', 'nos', 'bem', 'pela', 'ficar',
                                 #              'te', 'amizade', 'vendo', 'coisa', 'pessoa', 'tao', 'sem', 'falar',
                                 #              'quer', 'fica', 'fala', 'das', 'desse', 'hora', 'porque', 'pessoas',
                                 #              'sempre', 'jantando', 'bbbb', 'sempre', 'mal', 'vc', 'mim', 'fazendo',
                                 #              'falou', 'mulher', 'mano', 'dessa', 'amor', 'disse', 'fez', 'seu', 'homem',
                                 #              'la', 'vez', 'merda', 'aguento', 'vt', 'festas', 'melhor', 'sao',
                                 #              'queria', 'sim', 'finalmente', 'programa', 'mae', 'entrou', 'obrigada',
                                 #              'amei', 'tanto', 'demais', 'menos', 'chorando', 'bbbo', 'vergonha',
                                 #              'momento', 'algum', 'favorito', 'momento', 'fui', 'estao', 'bom',
                                 #              'sendo', 'todos', 'diz', 'alguma', 'mulheres', 'todos', 'cardapio',
                                 #              'meninas', 'machista', 'cabelo', 'teve', 'caralho', 'assunto', 'vcs',
                                 #              'viado', 'eliminar', 'acha', 'cozinha', 'ia', 'apoio', 'tombo',
                                 #              'queen', 'tocando', 'musicas', 'dancando', 'playlist', 'magica',
                                 #              'linda', 'toda', 'acho', 'escolheu', 'historia', 'conversa', 'passar',
                                 #              'estava', 'mao', 'horarios', 'kkkk', 'kkk', 'pau', 'cu', 'buceta',
                                 #              'dar', 'muita', 'deixado', 'cresce', 'tinha', 'empatia', 'todas', 'coisas',
                                 #              'agredir', 'competir', 'coisas', 'kkkkkkkkkkkkkkkkkkkkkkkk', 'celular',
                                 #              'achar', 'vingadores', 'presente', 'deu', 'ar', 'tirar', 'disso', 'cogita',
                                 #              'conseguiu', 'pulou', 'saiu', 'cuidados', 'medidas', 'prevencao', 'lavar',
                                 #              'maos', 'problema', 'ruim', 'dai', 'pegou', 'barata', 'achou', 'virus', 'nossa',
                                 #              'senhora', 'anos', 'vezes', 'asno', 'mil', 'sou', 'medico', 'cobraram', 'prefiro',
                                 #              'morrer', 'favelado', 'machuca', 'entao', 'fosse', 'qualquer', 'sai', 'horas',
                                 #              'tenho', 'merito', 'tanta', 'futebol', 'fechar', 'nocao', 'olhos', 'diante', 'videos',
                                 #              'incrivel', 'ansiosos', 'forca', 'parabens', 'quanto', 'esses', 'tbm', 'parece', 'torcer',
                                 #              'feed', 'mandando', 'samba', 'feliz', 'deve', 'porra', 'whatsapp', 'estar', 'imagina',
                                 #              'propria', 'merece', 'opiniao', 'vida', 'imagine', 'importa', 'nesse', 'quarentena',
                                 #              'poderiam', 'almoco', 'dialogos', 'passa', 'sei', 'nesse', 'mexendo', 'ein', 'totalmente',
                                 #              'quarto', 'tentar', 'levar', 'junto', 'mesma', 'tambem', 'povo', 'fav', 'planejando',
                                 #              'link', 'meta', 'iniciado', 'existe', 'tipos', 'camisa', 'fora', 'brasil', 'votem',
                                 #              'foco', 'enviem', 'parar', 'total', 'jogadores', 'gshow', 'termino', 'feat', 'pano', 'disseobrigada',
                                 #              'chao', 'doar', 'votarem', 'extremamente', 'proximo', 'torcendo',   'indo',
                                 #              'nas', 'olha', 'jeito', 'quase', 'gt', 'suporto', 'indo', 'menina', 'costas', 'debochada', 'multirao',
                                 #              'lt', 'gratuito', 'desculpa', 'forcada', 'insuportavel', 'projetinho', 'desabafei', 'leve',
                                 #              'cruzes', 'trinta', 'meio', 'espalhar', 'xexelenta', 'meio', 'seus', 'choro', 'rolou', 'risada',
                                 #              'aperte', 'comentarios', 'temia', 'furacao', 'comentar', 'choro', 'confira',
                                 #              ],
                                 max_features=25,
                                 )

    # X2 = vectorizer.fit_transform(df_train.loc[(df_train.country == country_var)]['description'])
    X2 = vectorizer.fit_transform(text_cleaned)

    features = (vectorizer.get_feature_names())
    scores = (X2.toarray())

    # Getting top ranking features
    sums = X2.sum(axis=0)
    data1 = []

    for col, term in enumerate(features):
        data1.append((term, sums[0, col]))

    ranking = pd.DataFrame(data1, columns=['term', 'rank'])
    words = (ranking.sort_values('rank', ascending=False))[:20]

    fig = px.bar(words, y='term', x='rank',
                 title='TOP 20 - Important Words', orientation='h')
    fig.update_layout(autosize=False, title_x=.5, height=500,
                      template='none', margin=dict(r=0))
    fig.update_yaxes(categoryorder='total ascending', title='')
    fig.update_xaxes(title='Rank of the Word')

    return fig


def hastag_counts(df):
    hashtags = []
    hashtag_pattern = re.compile(r'\B#\w*[a-zA-Z]+\w*')
    hashtag_matches = list(df.drop_duplicates('text', keep='last')[
        'text'].apply(hashtag_pattern.findall))
    hashtag_dict = {}
    for match in hashtag_matches:
        for singlematch in match:
            if singlematch not in hashtag_dict.keys():
                hashtag_dict[singlematch] = 1
            else:
                hashtag_dict[singlematch] = hashtag_dict[singlematch]+1

    hashtag_ordered_list = sorted(hashtag_dict.items(), key=lambda x: x[1])
    hashtag_ordered_list = hashtag_ordered_list[::-1]
    hashtag_ordered_list = [words for words in hashtag_ordered_list if np.array(words)[0] not in [
        "#COVID__19", "#Covid_19", "#covid", "#Covid", "#CoronaVirus", "#COVIDー19",
        "#COVID", "#Coronavirus", "#covid19", "#Covid19", "#coronavirus", "#COVID19", "CoronavirusPandemic",

        #   '#BBB', '#bbb', '#Redebbb', 'festaBbb20',
        #   '#RedeBBB', '#redebbb', '#bbbb20',
        #   '#BBBB', "#BBB20", "#bbb20",
        #   '#bbb2020', '#BBBB20', '#Bbb20',
        #   '#REDEBBB', "#bbb202O", '#redeBBB',
        #   '#RedeBBB20', '#BBB2O', '#BBB2O2O',
        #   '#BBB2O20', '#bbbb20', '#BBBB2O0',
        #   '#RedeBBBB20', '#BBBB200', '#BBBB2000',
        #   '#BBB20aovivo', '#BB', '#B', '#BBB2020',
        #   '#BBb20', '#RedeBBBB',  '#BBBB2O20', '#BBB20Aovivo',
        #   '#tv', '#bigBrotherBrasil', '#reality', '#realityShow'
    ]]

    # Separating the hashtags and their values into two different lists
    tags_bbb = pd.DataFrame(
        np.array(hashtag_ordered_list), columns=['#Tags', '#Num'])

    return tags_bbb


def user_counts(df):
    # Going to see who are the users who have tweeted or retweeted the #most and see how
    # Likely it is that they are bots
    usertweets = df.groupby('id_user')
    # Taking the top 25 tweeting users
    top_users = usertweets.count()['text'].sort_values(ascending=False)[:25]
    top_users_dict = top_users.to_dict()
    user_ordered_dict = sorted(top_users_dict.items(), key=lambda x: x[1])
    user_ordered_dict = user_ordered_dict[::-1]
    users_count = [user for user in user_ordered_dict]
    users_bbb = pd.DataFrame(np.array(users_count), columns=['@user', '#Num'])

    return users_bbb


def mention_count(df):
    mentions = []
    mention_pattern = re.compile(r"@[a-zA-Z_]+")
    mention_matches = list(df['text'].apply(mention_pattern.findall))
    mentions_dict = {}
    for match in mention_matches:
        for singlematch in match:
            if singlematch not in mentions_dict.keys():
                mentions_dict[singlematch] = 1
            else:
                mentions_dict[singlematch] = mentions_dict[singlematch]+1

    mentions_ordered_list = sorted(mentions_dict.items(), key=lambda x: x[1])
    mentions_ordered_list = mentions_ordered_list[::-1]
    mentions_ordered_list = [words for words in mentions_ordered_list]
    mentions_bbb = pd.DataFrame(
        np.array(mentions_ordered_list), columns=['@mentions', '#Num'])

    return mentions_bbb


@ app.callback(Output('graph-2', 'figure'),
               [Input('df-sharing', 'children')])
def _update_div1(df):

    df_ = pd.read_json(df, orient='split')

    fig = px.bar(mention_count(df_)[:20],
                 y='@mentions', x='#Num', orientation='h')

    fig.update_yaxes(categoryorder='total ascending', title='')
    fig.update_layout(margin=dict(t=30, r=0, b=0,
                                  pad=1), autosize=False, title_x=.5)
    return fig


@ app.callback(Output('graph-3', 'figure'),
               [Input('df-sharing', 'children')])
def _update_div1(df):

    df_ = pd.read_json(df, orient='split')

    fig = px.bar(hastag_counts(df_)[:20], y='#Tags', x='#Num',
                 orientation='h')
    fig.update_yaxes(categoryorder='total ascending', title='')
    fig.update_layout(margin=dict(t=30, r=0, b=0,
                                  pad=1), title_x=.5)
    return fig


@ app.callback(Output('graph-4', 'figure'),
               [Input('df-sharing', 'children')])
def _update_div1(df):

    df_ = pd.read_json(df, orient='split')

    fig = px.bar(user_counts(df_)[:20], y='@user', x='#Num', orientation='h')
    fig.update_yaxes(categoryorder='total ascending', title='')
    fig.update_layout(margin=dict(t=30, r=0, b=0,
                                  pad=3), autosize=False, title_x=.5)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
