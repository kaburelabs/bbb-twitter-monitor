import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
import dash_table
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from urllib3.exceptions import ProtocolError
import plotly_express as px
import os, re, string
import psycopg2
from decouple import config
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from unicodedata import normalize
import nltk
from nltk.tokenize import TweetTokenizer
from unicodedata import normalize
import dash_bootstrap_components as dbc


DATABASE_URL = config('DATABASE_URL')


con = psycopg2.connect(DATABASE_URL, sslmode='require')

app_name = "Trich Twitter Dashboard"

## CSS EXTERNAL FILE
external_stylesheets = [dbc.themes.BOOTSTRAP,
                        #'https://codepen.io/kaburelabs/pen/xxGRXWa.css', 
                        #"https://codepen.io/chriddyp/pen/brPBPO.css",
                        'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
                        'https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css']


scripts_jquery = [{'src':"https://code.jquery.com/jquery-3.4.1.min.js"}]


## Defining the instance of dash
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=scripts_jquery)

app.title = app_name

# server instance to run map when deploying
server = app.server

# Since I am adding callbacks to elements that don’t ~
# exist in the app.layout as they are spread throughout files
app.config.suppress_callback_exceptions = True

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script type='text/javascript' src='https://platform-api.sharethis.com/js/sharethis.js#property=5e8113b5c213f90019450492&product=inline-share-buttons&cms=website' async='async'></script>    
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

# # create a engine to the database
# engine = create_engine("sqlite:///historical.sqlite")
# # if the database does not exist
# if not database_exists(engine.url):
#     # create a new database
#     create_database(engine.url)


def create_header(some_string):
    header_style = {
        'background-color':'#3C4240',
        'padding': '1.5rem',
        'display':'inline-block',
        'width':'100%'
        
       # 'border-style': 'dotted'
    }
    logo_trich = html.Img(
                    src='/assets/fundo_transp-b.png',
                    className='three columns',
                    style={
                        'height': 'auto',
                        'width': '140px', # 'padding': 1
                        'float': 'right', #'position': 'relative'
                        'margin-right': '66px', #'border-style': 'dotted'
                        'display':'inline-block'})

    title = html.H1(children=some_string, className='eight columns',
                    style={'margin':'0 0 0 36px',
                           'color':'#ffffff', 'font-size':'35px'})

    header = html.Header(html.Div([title, logo_trich]), style=header_style)

    return header

def create_footer():
    p = html.P(
        children=[
            html.Span('Developed By: '),
            html.A('trich.ai | Data Intelligence Solutions', 
                   style={'text-decoration':'none', 'color':'#ffffff'},
                   href='https://trich.ai', target='_blank')
        ], style={'float':'right', 'margin-top':'8px', 
                  'font-size':'18px', 'color':'#ffffff' }
    )

    span_style = {'horizontal-align': 'right', 
                  'padding-left': '1rem', 
                  'font-size':'15px', 
                  'vertical-align':'middle'}

    kaggle = html.A(
        children=[
            html.I([], className='fab fa-kaggle'),
            html.Span('Kaggle', style=span_style)
        ], style={'text-decoration': 'none', 'color':'#ffffff', 'margin-right':'20px'},
        href="https://www.kaggle.com/kabure/kernels",
        target='_blank')

    mapbox = html.A(
        children=[
            html.I([], className='fab fa-python'),
            html.Span('Dash Plotly', style=span_style)
        ], style={'text-decoration': 'none', 'color':'#ffffff', 'margin-right':'20px'},
        href='https://plot.ly/dash/', target='_blank')

    font_awesome = html.A(
        children=[
            html.I([], className='fa fa-font-awesome'),
            html.Span('Font Awesome', style=span_style)
        ], style={'text-decoration': 'none', 'color':'#ffffff', 'margin-right':'20px'},
        href='http://fontawesome.io/', target='_blank')

    datatables = html.A(
        children=[
            html.I([], className='fa fa-github'),
            html.Span('trich.ai\n Github', style=span_style)
        ], style={'text-decoration': 'none', 'color':'#ffffff', 'margin-right':'20px'},
        href='https://github.com/kaburelabs/', target='_blank')

    ul1 = html.Div(
        children=[
            html.Li(mapbox, style={'display':'inline-block', 'color':'#ffffff'}),
            html.Li(font_awesome, style={'display':'inline-block', 'color':'#ffffff'}),
            html.Li(datatables, style={'display':'inline-block', 'color':'#ffffff'}),
            html.Li(kaggle, style={'display':'inline-block', 'color':'#ffffff'}),
        ],
        style={'list-style-type': 'none', 'font-size':'30px'},
    )

    hashtags = 'plotly,dash,trich.ai,bbb20,data, streaming'
    tweet = 'trich.ai Twitter Live Monitor, a cool dashboard with Plotly Dash!'
    twitter_href = 'https://twitter.com/intent/tweet?hashtags={}&text={}'\
        .format(hashtags, tweet)
    twitter = html.A(
        children=html.I(children=[], className='fa fa-twitter'),
        title='Tweet me!', href=twitter_href, target='_blank')

    # github = html.A(
    #     children=html.I(children=[], className='fa fa-github', style={'color':'black'}),
    #     title='Repo on GitHub',
    #     href='https://github.com/kaburelabs/Wine-Project-Dash', target='_blank')

    li_right_first = {'line-style-type': 'none', 'display': 'inline-block'}
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
            'font-size':'60px'
        }
    )
    div = html.Div([p, ul1, ul2])

    footer_style = {
        'font-size': '2.2rem',
        'background-color': '#3C4240',
        #'padding': '2.5rem',
        'margin-top': '5rem', 
        'display':'inline-block', 'padding':'16px 32px 8px'
    }
    footer = html.Footer(div, style=footer_style, className='twelve columns')
    return footer


app.layout = html.Div([
    html.Div(className="sharethis-inline-share-buttons"),
    create_header("Twitter Live Monitor"),

    html.Div([
    html.Div(
    [ 
    html.Div([dbc.Alert(
            [
                html.H2("Welcome to trich.ai Twitter Streaming WebApp!", className="alert-heading"),
                html.Div([
                    html.P([ "NOTE: The application auto updates the content every 30 seconds and as it is a free version of Heroku platform, sometimes it can 'sleep' and stop to collect the data."]),
                    html.P([ "As it's hosted in a free Heroku host and it can be a little slow or don't render correctly the components. "])
                    ], style={'fontSize':'18px'}
                ),
                html.Hr(),
                html.P(
                    "Feel free to contact us for a Proof of Concept (POC) for your brand, enterprise or even if you have interest in another WebApp types.",
                    className="mb-0", style={'fontSize':'14px'}
                ),
            ], style={'textAlign':'center'}, color='info', dismissable=True
        )
    ], className='row', style={'width':'60%','margin':'auto'}),
    html.Div([
        html.Div([html.H1("Big Brother Brazil 20 Live Monitor", style={'textAlign':'center'}),
                  html.P("Monitoramento utilizando dados extraídos do Twitter e que pretende resumir as informações que estão acontecendo no programa Big Brother Brasil 20 que é produzido pela Rede Globo de Televisão."),
                  html.P(["O monitor foi desenvolvido e é mantido pela ", 
                          html.A('trich.ai', href='https://trich.ai', target='_blank' ),  
                          " que visa proporcionar informação utilizando big data para obter insights."])
        ], className='row-m'),
        html.Div([
                html.Div([
                    html.Img(
                                src='/assets/Rede_Globo_logo.png',
                                style={
                                    'width':'100px', 
                                    'display':'inline-block',
                                    }
                                )
                        ], className='four columns', style={'textAlign':'center'}),
                html.Div([
                    html.Img(
                                src='/assets/89846551_1428521667330586_8342275172711006208_n.png',
                                style={
                                    'width':'200px', 
                                    'display':'inline-block'}
                                    )
                            ], className='four columns', style={'textAlign':'center'}),
                html.Div([ 
                    html.Img(
                                src='/assets/twitter_logo.svg',
                                style={
                                    'width': '85px', 
                                    'display':'inline-block', }
                                    )
                            ], className='four columns', style={'textAlign':'center'})
            ], className='row-m', style={'width':'80%', 'margin':'50px auto 15px'})
    ], className='row-m', style={'width':'80%', 'margin': '50px auto'}),

    html.Div(id='df-sharing', style={'display': 'none'}),
    html.Div([
        # dcc.Loading(loading_state={'is_loading':False}),
        html.Div([  

            #html.H4("TOP 20 most common words", style={'textAlign':'center','margin':}),
            dcc.Graph(id='tfidf-graph')
        ], className='five columns'),    
            html.Div(id='live-values', className='seven columns', # className='nine columns', 
                    style={ #'padding':'12px 48px', 'margin':'90px 0 18px',
                            'display':'inline-block', 'margin':'60px 0 0', 'backgroundColor':'rgb(43, 169, 224, 0.26)',
                    }),
            dcc.Interval(
                id='graph-update',
                interval=15*1000,
                n_intervals=0
            )
            #], className='six columns', style={ 'height': '350px', 'margin':'60px 0'}),
    ], className='row-m', style={'height':'500px', 'width':'80%', 'margin':'auto'}),


    html.Div([
            html.Div([
                html.H2("MAIN TWEETS FOR THIS MOMENT")
            ], className='row-m', style={'textAlign':'center'}),
            html.Div([
                html.Div([
                    html.P("MOST SHARED TWEETS NOW", style={'fontSize':'24px'}),
                    html.P("(Trends at this moment)", style={'fontSize':'18px'})
                ], className='six columns', style={'textAlign':'center', 'padding':'24px 35px 0'}),

                html.Div([
                    html.P("MOST RETWEETED TWEETS", style={'fontSize':'24px'}),
                    html.P("(More Long term tweets - not necessarily at this moment)", style={'fontSize':'18px'})
                ], className='six columns', style={'textAlign':'center', 'padding':'24px 35px 0'})
            ], className='row-m')
    ], className='row-m', style={'margin':'70px 0 12px'}),

    html.Div([
        html.Div(id='output-iframe-share', className='six columns', style={'height':'600px',  'overflowY':'auto', 'paddingRight':'36px'}),
        html.Div(id='output-iframe-rt', className='six columns', style={'height':'600px',  'overflowY':'auto', 'paddingLeft':'36px'})
    ], className='row-m', style={'textAlign':'center', 'marginBottom':'72px'}),
    
    # html.Div([
    #     html.Div([#html.P('TOP 25 MOST SHARED TWEETS', style={'padding':'.5rem', 'textAlign':'center'}), 
    #                 dash_table.DataTable(id='recommender-table', 
    #                                     columns=[{'name':i, 'id':i} for i in ['count',  'text', "# RT's"]],
    #                                     #page_size=5, 
    #                                     fixed_columns={'headers': True, 'data': 0},
    #                                     #style_as_list_view=True,
    #                                     fixed_rows={'headers': True, 'data': 0},  
    #                                     style_table={'maxHeight':'425px'}, 
    #                                     style_header={'fontWeight': 'bold', 'fontSize':'14px', 'textAlign':'center',},
    #                                     style_cell={"minWidth":"42px"},
    #                                     style_data_conditional=[
    #                                                 {
    #                                                 'if': {'row_index': 'odd'},
    #                                                 'backgroundColor': 'rgb(248, 248, 248)'
    #                                                  }
    #                                     ],       
    #                                     style_cell_conditional=[
    #                                         {'if': {'column_id': 'text'}, 'textAlign':'left',
    #                                                                       'width': '350px',
    #                                                                       'whiteSpace': 'normal', 'minHeight':'15px'},

    #                                         {'if': {'column_id': "# RT's"}, 'width': '20px'},
    #                                         {'if': {'column_id': "count"}, 'width': '20px'}
    #                                     ], 
    #                 )
    #             ], className='six columns'),

    #     html.Div([#html.P('TOP 25 MOST SHARED TWEETS', style={'padding':'.5rem', 'textAlign':'center'}), 
    #                 dash_table.DataTable(id='recommender-table2', 
    #                                     columns=[{'name':i, 'id':i} for i in ["# RT's", 'text', 'count']],
    #                                     #page_size=5, 
    #                                     fixed_columns={'headers': True, 'data': 0},
    #                                     #style_as_list_view=True,
    #                                     fixed_rows={'headers': True, 'data': 0},  
    #                                     style_table={'maxHeight':'425px'}, 
    #                                     style_header={'fontWeight': 'bold', 'fontSize':'14px', 'textAlign':'center',},
    #                                     style_cell={"minWidth":"42px"},
    #                                     style_data_conditional=[
    #                                                 {
    #                                                 'if': {'row_index': 'odd'},
    #                                                 'backgroundColor': 'rgb(248, 248, 248)'
    #                                                  }
    #                                     ],       
    #                                     style_cell_conditional=[
    #                                         {'if': {'column_id': 'text'}, 'textAlign':'left',
    #                                                                       'width': '350px',
    #                                                                       'whiteSpace': 'normal', 'minHeight':'15px'},

    #                                         {'if': {'column_id': "# RT's"}, 'width': '20px'},
    #                                         {'if': {'column_id': "count"}, 'width': '20px'}
    #                                     ], 
    #                 )
    #             ], className='six columns'),
    #         ], className='row-m', style={'height':'500px'}),

    html.Div([
        html.Div(["MOST IMPORTANT MENTIONS, HASHTAGS AND USERS"], className='Row-m', style={'textAlign':'center','fontSize':'30px', 'margin':'78px 0 0'}),
        # html.Div([
        #     html.P('Mais mencionados')
        # ], className='four columns', style={'textAlign':'center','fontSize':'24px'}),
        # html.Div([
        #     html.P('Principais ')
        # ], className='four columns', style={'textAlign':'center','fontSize':'24px'}),
        # html.Div([
        #     html.P('blablalbal balbalba lbalbalba')
        # ], className='four columns', style={'textAlign':'center','fontSize':'24px'})
    ], style={'marginTop':'36px'}),

    html.Div([
        
        # Menções, Hashtags e usuários mais ativos
        # time_inf = round(pd.Timedelta(df.created_at.max() - df.created_at.min()).seconds / 60)
        html.Div([           
                # <i class="fas fa-at"></i>
                html.Div([
                        html.I([], className='fa fa-at', style={'fontSize':'25px', 'fontWeight':'bold'}),
                        html.Span(' MOST IMPORTANT MENTIONS', style={'fontSize':'20px', 'font': 'sans-serif', 'fontWeight':'bold'})
                    ], style={'text-decoration': 'none', 'textAlign':'center', 'margin':'0 auto'}),
                dcc.Graph(id='graph-2')
            ], className='four columns', style={'display':'inline-block', 'margin':'0 auto'}),
        html.Div([         
                #<i class="fas fa-hashtag"></i>
                html.Div([
                        html.I([], className='fa fa-hashtag', style={'fontSize':'25px'}),
                        html.Span(' MOST IMPORTANT HASHTAGS', style={'fontSize':'20px', 'font': 'sans-serif', 'fontWeight':'bold'})
                    ], style={'text-decoration': 'none', 'textAlign':'center', 'margin':'0 auto'}),
                dcc.Graph(id='graph-3')
            ], className='four columns', style={'display':'inline-block', 'margin':'0 auto'},),
        html.Div([           
                #<i class="fas fa-comment-medical"></i>
                html.Div([
                        html.I([], className='fas fa-comment-medical', style={'fontSize':'25px'}),
                        html.Span(' MOST ACTIVE USERS', style={'fontSize':'20px', 'font': 'sans-serif', 'fontWeight':'bold'})
                    ], style={'text-decoration': 'none', 'textAlign':'center', 'margin':'0 auto'}),
                dcc.Graph(id='graph-4')
            ], className='four columns', style={'display':'inline-block', 'margin':'0 auto'},)
    ], className='row-m')
    ]),

    html.Div([
        html.Div([           
                dcc.Graph(id='graph-5')
            ], className='twelve columns'),
    ], className='row-m'),


    ], className='container'),
     create_footer()
], style={'overflow':'hidden'})

def calc_tweet_metrics(df):
    total_tweets = len(df)
    unique_texts = df['text'].nunique()
    unique_texts_perc = round(df['text'].nunique() / len(df) *100,2)
    unique_users = df['id_user'].nunique()
    top_20_posts_perc = round((df.text.value_counts().reset_index().rename(columns={'text':'total', 'index':'text'})[:20].total.sum() / len(df)) * 100,2)
    top_20_posts = df.text.value_counts().reset_index().rename(columns={'text':'total', 'index':'text'})[:20].total.sum()
    df_dup = df.drop_duplicates('text', keep='last').sort_values('retweet_shares', ascending=False)
    zero_tweets = len(df_dup[df_dup['retweet_user'].isin([None]) & df_dup['quoted_user'].isin([None])])
    zero_retweets_perc = round(zero_tweets / len(df) * 100,2)
    time_inf = round(pd.Timedelta(df.created_at.max() - df.created_at.min()).seconds / 60)
    # print(df.created_at.max(), df.created_at.min())
    return [total_tweets, unique_texts, unique_texts_perc, unique_users, 
            top_20_posts, top_20_posts_perc, zero_tweets, zero_retweets_perc, time_inf]

def calc_last_most_tweeted(df):
    tweets_list = df.text.value_counts().reset_index().rename(columns={'text':'total',
                                                                       'index':'text'})[:20].reset_index().drop('index', axis=1)

    return tweets_list

def remove_punct(text):
    text = text.lower()
    text  = "".join([char for char in text if char not in string.punctuation])
    text = re.sub('[0-9]+', '', text)
    return text

def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII') 

def remove_URL(text):
    url = re.compile(r'https?://\S+|www\.\S+')
    return url.sub(r'',text)

def remove_at(text):
    clean = re.sub(r'@[A-Za-z0-9]+','', text)
    return clean


@app.callback(Output('df-sharing', 'children'),
              [Input('graph-update', 'n_intervals')])
def _update_div1(val_1):

    df = pd.read_sql_query("SELECT * from tweet", con)
    return df.to_json(date_format='iso', orient='split')

@app.callback(Output('live-values', 'children'),
              [Input('df-sharing', 'children')])
def _update_div1(df):
    df_ = pd.read_json(df, orient='split')
    df_.created_at = pd.to_datetime(df_.created_at)
    total_tweets, unique_texts, unique_texts_perc, unique_users, \
        top_20_posts, top_20_posts_perc, zero_retweets, zero_retweets_perc, time_inf = calc_tweet_metrics(df_)
    #df = df.sort_values('created_at')
    return html.Div([
        html.Div([
            html.Div([
                html.H5(style={'textAlign':'center','padding':'.1rem',
                                'fontSize':'22px'}, className='title',
                                    children=[f"Information to the last {time_inf} minutes"])
                ], className='row-m'),   
            html.Div(
                children=[
                    html.Div([
                        html.Div([
                            html.I([], className='far fa-comment-dots', style={'fontSize':'40px', 
                                                                               'width':'80%',
                                                                               'margin':'0 auto'}),
                                    # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                                ], style={'text-decoration': 'none', 'width':'80%', 'margin':'0 auto', 'textAlign':'center'}),
                            html.H3(id='display-6', style={'textAlign':'center','fontWeight':'bold','color':'#3C4240'},
                                    children=[html.P(style={'padding':'.5rem'},
                                                     children=total_tweets)]
                                        ), 
                            html.H5(style={'textAlign':'center','color':'#3C4240','padding':'.1rem'},
                                            children="Total Tweets")                                        
                                    ], className='six columns', style={'display':'inline-block'}),

                        html.Div(
                            children=[
                            html.Div([
                                    html.I([], className='far fa-user', style={'fontSize':'40px', 'width':'80%', 'margin':'0 auto'}),
                                    # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                                ], style={'text-decoration': 'none', 'width':'80%', 'margin':'0 auto', 'textAlign':'center'}),
                                html.H3(id='display-8', style={'textAlign':'center',
                                        'fontWeight':'bold','color':'#3C4240'},
                                        children=[html.P(style={'padding':'.5rem'},
                                                        children=unique_users)]),
                                                        # <i class="fas fa-users"></i>
                                html.H5(style={'textAlign':'center','color':'#3C4240','padding':'.1rem'},
                                                children="Unique Users")                                        
                                        ], className='six columns', style={'display':'inline-block'}),
                                        ], className='row-m', style={'width':'60%', 'margin':'auto'}),
                ] ),
           html.Div([
                        html.Div(
                            children=[
                            html.Div([
                                html.I([], className='fas fa-retweet', style={'fontSize':'40px', 'width':'80%', 'margin':'0 auto'}),
                                # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                                ], style={'text-decoration': 'none', 'width':'80%', 'margin':'0 auto', 'textAlign':'center'}),
                                html.H3(id='display-7', style={'textAlign':'center',
                                            'fontWeight':'bold','color':'#3C4240'},
                                        children=[html.P(style={'padding':'.1rem'},
                                                        children=f"{unique_texts_perc}%")]),
                                                        # <i class="fas fa-retweet"></i>
                                # html.P(f"({unique_texts})", style={'textAlign':'center'}),
                                html.H5(style={'textAlign':'center','color':'#3C4240','padding':'.1rem'},
                                                children="Unique tweets")                                        
                                        ], className='four columns', style={'display':'inline-block'}),
                        html.Div(
                            children=[
                            html.Div([
                                html.I([], className='fas fa-paragraph', style={'fontSize':'40px', 'width':'80%', 'margin':'0 auto'}),
                                # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                                ], style={'text-decoration': 'none', 'width':'80%', 'margin':'0 auto', 'textAlign':'center'}),
                                html.H3(id='display-5', style={'textAlign':'center',
                                            'fontWeight':'bold','color':'#3C4240'},
                                            children=[html.P(style={'padding':'.1rem'},
                                                            children=f"{zero_retweets_perc}%")]),
                                # html.P(f"({zero_retweets})", style={'textAlign':'center'}),
                                html.H5(style={'textAlign':'center','color':'#3C4240','padding':'.1rem'},
                                                children="(No RT or Quote)")                   
               
                                        ], className='four columns', style={'display':'inline-block'}),
                        html.Div(
                            children=[
                            html.Div([
                                html.I([], className='fas fa-fire-alt', style={'fontSize':'40px', 'width':'80%', 'margin':'0 auto'}),
                                # html.Span(' Total tweets', style={'fontSize':'21px', 'font': 'sans-serif', 'fontWeight':'bold'})
                                ], style={'text-decoration': 'none', 'width':'80%', 'margin':'0 auto', 'textAlign':'center'}),
                                html.H3(id='display-9', style={'textAlign':'center',
                                            'fontWeight':'bold','color':'#3C4240'},
                                            children=[html.P(style={'padding':'.1rem'},
                                                            children=f"{top_20_posts_perc}%")]),
                                #html.P(f"({top_20_posts_perc}%)", style={'textAlign':'center'}),
                                html.H5(style={'textAlign':'center','color':'#3C4240','padding':'.1rem'},
                                                children="Top 20 posts")                                        
                                        ], className='four columns', style={'display':'inline-block'}),
                        ])       
                                    
                    ])
                    

def resume_tweets(df, type='share'):

    list_twt = []

    for i in list(range(30)):

        user = df['id_user'].to_list()[i]
        tweet = int(df['tweet_id'].to_list()[i])
        is_rt = df['is_RT'].to_list()[i]
        # if df_princ['retweet_user'].to_list()[i] != None:
        #     rt_user = df_princ['retweet_user'].to_list()[i]
        #     rt_tweet = int(df_princ['retweet_url'].to_list()[i])
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
            text = f"#{i+1} Most Shared - Total Shares: {df['count'].to_list()[i]}"
        else: 
            text = f"#{i+1} Most Retweeted - Total Shares: {df['count'].to_list()[i]}"

        list_twt.append(html.Div([#html.P(f"{i+1} is RT ({is_rt}) - TEXT {df_princ['text'].to_list()[i]}"),
                                    html.P([text # | Link: {link}"
                                            ], style={'textAlign':'center', 'fontWeight':'bold', 'fontSize':'18px'}),
                                    html.Iframe(src=f"https://twitframe.com/show?url={link}", 
                                                id='tweet_', 
                                                style={'width':'100%',
                                                        'minHeight':'250px', 
                                                        'maxHeight':'700px',
                                                        #'position':'relative',
                                                        #'height':'100%',
                                                        'border':'0', 'conversation':'None',
                                                        'frameborder':'0',
                                                        #'theme':'dark'
                                                    })
                                    ], style={'width':'100%', 'margin':'24px 0'}
                                ))
    return list_twt

@app.callback([Output('output-iframe-share', 'children'),
               Output('output-iframe-rt', 'children')],
              [Input('df-sharing', 'children')])    
def _update_div1(df):
    df_ = pd.read_json(df, orient='split')
    # time.sleep(30)
    shared_tweets_list = []
    rt_tweets_list = []
    cols = ['text', 'id_user', 'tweet_id', 'is_RT', 'retweet_user', 
            'quote_url', 'retweeted_url', 'count']

    df_['count'] = df_.groupby(["text"])["tweet_id"].transform("count")
    df_princ = df_.drop_duplicates('text', keep='first').sort_values('count', ascending=False)[cols]
    df_princ1 = df_.drop_duplicates('text', keep='last').sort_values('retweet_shares', ascending=False)[cols].rename(columns={'retweet_shares':"# RT's"})

    # print(df_princ.columns)
    # df = df_[df_.index.isin(df_.text.drop_duplicates(keep='last').index)].sort_values('retweet_likes', ascending=False)[:20]

    shared_tweets_list = resume_tweets(df_princ)
    rt_tweets_list = resume_tweets(df_princ1, type='rt')

    return [shared_tweets_list, rt_tweets_list]
    

@app.callback([Output('recommender-table', 'data'),
               Output('recommender-table2', 'data')],
              [Input('df-sharing', 'children')])    
def _update_div1(df):
    df_ = pd.read_json(df, orient='split')
    #df = pd.read_sql_query("SELECT text from tweet", con)
    df_['count'] = df_.groupby(["text"])["created_at"].transform("count")
    df_princ = df_.drop_duplicates('text', keep='last').sort_values('count', ascending=False)[['count', 'text', 'retweet_shares']].rename(columns={'retweet_shares':"# RT's"})
    df_princ1 = df_.drop_duplicates('text', keep='last').sort_values('retweet_shares', ascending=False)[['retweet_shares', 'text', 'count']].rename(columns={'retweet_shares':"# RT's"})

    return [df_princ[:40].to_dict('rows'), df_princ1[(df_princ1['count'] >= 15) & (df_princ1["# RT's"])][:40].to_dict('rows')]
    

def creating_hist():
    hist_vals = pd.DataFrame(data=[], columns=['created_at', 'index'])

    return hist_vals
    

hist_vals = pd.DataFrame(data=[], columns=['created_at', 'index'])


from datetime import timedelta
@app.callback(Output('graph-5', 'figure'),
              [Input('df-sharing', 'children')])
def _update_div1(df):


    global hist_vals

    df_ = pd.read_json(df, orient='split')
    # df_.drop('index', axis=1, inplace=True)
    df_.created_at = pd.to_datetime(df_.created_at)
    df_.set_index('created_at', inplace=True)   

    hist_vals = hist_vals.append(df_.resample('1min').count()['index'].sort_index(ascending=False).reset_index()[1:-1].to_dict('row'))
    hist_vals = hist_vals.reset_index().drop('level_0', axis=1)
    hist_vals = hist_vals.sort_values('created_at', ascending=False).drop_duplicates('created_at', keep='last')

    fig = px.line(hist_vals[:72], x='created_at', y='index',
                   title='The count of tweets for each minute')

    fig.update_layout(xaxis=dict(title='Date/Minutes'), yaxis=dict(title='Count Total'), title_x=.5)

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
    text_nopunct = "".join([char.lower() for char in text_nonum if char not in punct]) 
#     print(text_nopunct)
    text_accents = normalize('NFKD', text_nopunct).encode('ASCII', 'ignore').decode('ASCII')
    # substitute multiple whitespace with single whitespace
    # Also, removes leading and trailing whitespaces
    text_no_doublespace = re.sub('\s+', ' ', text_accents).strip()
    
    return text_no_doublespace


def strip_links(text):
    link_regex    = re.compile('((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)', re.DOTALL)
    links         = re.findall(link_regex, text)
    for link in links:
        text = text.replace(link[0], ', ')    
    return text

def strip_all_entities(text):
    entity_prefixes = ['@','#']
    for separator in  string.punctuation:
        if separator not in entity_prefixes :
            text = text.replace(separator,' ')
    words = []
    for word in text.split():
        word = word.strip()
        if word:
            if word[0] not in entity_prefixes:
                words.append(word)
    return ' '.join(words)

@app.callback(Output('tfidf-graph', 'figure'),
              [Input('df-sharing', 'children'),
               Input('graph-update', 'n_intervals')])
def _update_tfidf(data, val2):

    df_ = pd.read_json(data, orient='split')
    text_cleaned = df_.text.apply(strip_all_entities)      
    text_cleaned = text_cleaned.apply(strip_links)      

    text_cleaned = df_.text.apply(clean_text)
    tt = TweetTokenizer()

    vectorizer = TfidfVectorizer(ngram_range = (1,3), min_df=5,
                                stop_words=['bbb', 'redebbb', 'do', 'rt', 'festabbb', 'que', 'da', 'em', 'com', 'esse',
                                            'eu', 'nao', 'de', 'no', 'pra', 'pro', 'uma', 'so', 'dos', 'ele',
                                            'ele', 'se','um', 'ta', 'vai', 'na', 'essa', 'me', 'meu', 'faz',
                                            'ja', 'ela', 'to', 'mais', 'mas', 'tem', 'por', 'quem', 'para',
                                            'os', 'as', 'ser', 'ver', 'isso', 'como', 'quando','comecar',
                                            'ai', 'ate', 'foi', 'voce', 'hoje', 'gente', 'muito', 'fazer',
                                            'pq', 'agora', 'falando', 'casa', 'vamos', 'tudo', 'quero', 'eles',
                                            'dois', 'ter', 'minha', 'dia', 'esta', 'sobre', 'cara', 'aqui',
                                            'ou', 'todo', 'vou', 'mesmo', 'dele', 'pelo', 'nem', 'nunca', 'cinema',
                                            'video', 'ao', 'voces', 'ne', 'ainda', 'ne', 'pode', 'sabe', 'deus', 
                                            'bigbrotherbrasil', 'realityshow', 'tv', 'via', 'entretenimento',
                                            'reality', 'personalidade', 'pt', 'tirei', 'comeca', 'comecou', 
                                            'logo', 'edicao', 'alguem', 'amo', 'nada', 'mundo', 'vem', 'sair',
                                            'jogo', 'estamos', 'era', 'podio', 'dela', 'forte', 'ninguem',
                                            'nosso', 'depois', 'assim', 'sua', 'nos', 'bem', 'pela', 'ficar', 
                                            'te', 'amizade', 'vendo', 'coisa', 'pessoa', 'tao', 'sem', 'falar',
                                            'quer', 'fica', 'fala', 'das', 'desse', 'hora', 'porque', 'pessoas',
                                            'sempre', 'jantando', 'bbbb', 'sempre', 'mal', 'vc', 'mim', 'fazendo',
                                            'falou', 'mulher', 'mano', 'dessa', 'amor', 'disse', 'fez', 'seu', 'homem',
                                            'la', 'vez', 'merda', 'aguento', 'vt', 'festas', 'melhor','sao',
                                            'queria', 'sim', 'finalmente', 'programa', 'mae', 'entrou', 'obrigada',
                                            'amei', 'tanto', 'demais', 'menos', 'chorando', 'bbbo', 'vergonha', 
                                            'momento', 'algum', 'favorito', 'momento', 'fui', 'estao', 'bom', 
                                            'sendo', 'todos', 'diz', 'alguma', 'mulheres', 'todos', 'cardapio', 
                                            'meninas', 'machista', 'cabelo', 'teve', 'caralho', 'assunto', 'vcs',
                                            'viado', 'eliminar', 'acha', 'cozinha', 'ia', 'apoio', 'tombo', 
                                            'queen', 'tocando', 'musicas', 'dancando', 'playlist', 'magica', 
                                            'linda', 'toda', 'acho', 'escolheu', 'historia', 'conversa', 'passar',
                                            'estava', 'mao', 'horarios', 'kkkk', 'kkk', 'pau', 'cu', 'buceta',
                                            'dar','muita', 'deixado', 'cresce', 'tinha', 'empatia', 'todas', 'coisas',
                                            'agredir', 'competir', 'coisas', 'kkkkkkkkkkkkkkkkkkkkkkkk', 'celular',
                                            'achar', 'vingadores', 'presente', 'deu', 'ar', 'tirar', 'disso', 'cogita',
                                            'conseguiu', 'pulou', 'saiu', 'cuidados', 'medidas', 'prevencao', 'lavar',
                                            'maos', 'problema', 'ruim', 'dai', 'pegou', 'barata', 'achou', 'virus', 'nossa',
                                            'senhora', 'anos', 'vezes', 'asno', 'mil','sou', 'medico', 'cobraram', 'prefiro', 
                                            'morrer', 'favelado', 'machuca', 'entao', 'fosse', 'qualquer', 'sai', 'horas', 
                                            'tenho', 'merito', 'tanta', 'futebol', 'fechar', 'nocao', 'olhos', 'diante', 'videos', 
                                            'incrivel', 'ansiosos', 'forca', 'parabens', 'quanto', 'esses', 'tbm', 'parece', 'torcer',
                                            'feed', 'mandando', 'samba', 'feliz', 'deve', 'porra', 'whatsapp', 'estar', 'imagina', 
                                            'propria', 'merece', 'opiniao', 'vida', 'imagine', 'importa', 'nesse', 'quarentena', 
                                            'poderiam', 'almoco', 'dialogos', 'passa', 'sei', 'nesse', 'mexendo', 'ein', 'totalmente',
                                            'quarto', 'tentar', 'levar', 'junto', 'mesma', 'tambem', 'povo', 'fav', 'planejando',
                                            'link', 'meta', 'iniciado', 'existe', 'tipos', 'camisa', 'fora', 'brasil', 'votem',
                                            'foco', 'enviem', 'parar', 'total', 'jogadores', 'gshow', 'termino', 'feat', 'pano', 'disseobrigada',
                                            'chao', 'doar', 'votarem', 
                                            ], max_features=25,
                             )

    #X2 = vectorizer.fit_transform(df_train.loc[(df_train.country == country_var)]['description']) 
    X2 = vectorizer.fit_transform(text_cleaned) 
    
    features = (vectorizer.get_feature_names()) 
    scores = (X2.toarray()) 

    # Getting top ranking features 
    sums = X2.sum(axis = 0) 
    data1 = [] 

    for col, term in enumerate(features): 
        data1.append( (term, sums[0, col] )) 

    ranking = pd.DataFrame(data1, columns = ['term','rank']) 
    words = (ranking.sort_values('rank', ascending = False))[:20]

    fig = px.bar(words, y='term', x='rank',
                 title='TOP 20 - Important Words', orientation='h')
    fig.update_layout(autosize=False, title_x=.5, height=500, template='none' )
    fig.update_yaxes(categoryorder='total ascending', title='')
    fig.update_xaxes(title='Rank of the Word')

    return fig



def hastag_counts(df):
    hashtags = []
    hashtag_pattern = re.compile(r'\B#\w*[a-zA-Z]+\w*')
    hashtag_matches = list(df.drop_duplicates('text', keep='last')['text'].apply(hashtag_pattern.findall))
    hashtag_dict = {}
    for match in hashtag_matches:
        for singlematch in match:
            if singlematch not in hashtag_dict.keys():
                hashtag_dict[singlematch] = 1
            else:
                hashtag_dict[singlematch] = hashtag_dict[singlematch]+1

    hashtag_ordered_list =sorted(hashtag_dict.items(), key=lambda x:x[1])
    hashtag_ordered_list = hashtag_ordered_list[::-1]
    hashtag_ordered_list = [words for words in hashtag_ordered_list if np.array(words)[0] not in ['#BBB', '#bbb', '#Redebbb', 'festaBbb20', 
                                                                                                  '#RedeBBB', '#redebbb', '#bbbb20',
                                                                                                  '#BBBB', "#BBB20", "#bbb20", 
                                                                                                  '#bbb2020', '#BBBB20', '#Bbb20',
                                                                                                  '#REDEBBB', "#bbb202O", '#redeBBB',
                                                                                                  '#RedeBBB20', '#BBB2O', '#BBB2O2O',
                                                                                                  '#BBB2O20', '#bbbb20', '#BBBB2O0',
                                                                                                  '#RedeBBBB20', '#BBBB200', '#BBBB2000',
                                                                                                  '#BBB20aovivo', '#BB', '#B', '#BBB2020',
                                                                                                  '#BBb20', '#RedeBBBB',  '#BBBB2O20', '#BBB20Aovivo', 
                                                                                                  '#tv', '#bigBrotherBrasil', '#reality', '#realityShow']]
    #Separating the hashtags and their values into two different lists
    tags_bbb = pd.DataFrame(np.array(hashtag_ordered_list), columns=['#Tags', '#Num'])
    
    return tags_bbb

def user_counts(df):
    #Going to see who are the users who have tweeted or retweeted the #most and see how
    #Likely it is that they are bots
    usertweets = df.groupby('id_user')
    #Taking the top 25 tweeting users
    top_users = usertweets.count()['text'].sort_values(ascending = False)[:25]
    top_users_dict = top_users.to_dict()
    user_ordered_dict =sorted(top_users_dict.items(), key=lambda x:x[1])
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

    mentions_ordered_list =sorted(mentions_dict.items(), key=lambda x:x[1])
    mentions_ordered_list = mentions_ordered_list[::-1]
    mentions_ordered_list = [words for words in mentions_ordered_list]
    mentions_bbb = pd.DataFrame(np.array(mentions_ordered_list), columns=['@mentions', '#Num'])
    
    return mentions_bbb


@app.callback(Output('graph-2', 'figure'),
              [Input('df-sharing', 'children')])
def _update_div1(df):

    df_ = pd.read_json(df, orient='split')

    fig = px.bar(mention_count(df_)[:20], y='@mentions', x='#Num', orientation='h')

    fig.update_yaxes(categoryorder='total ascending', title='')
    fig.update_layout(margin=dict(t=30, 
                                  pad=1), autosize=False, title_x=.5)
    return fig 

@app.callback(Output('graph-3', 'figure'),
              [Input('df-sharing', 'children')])
def _update_div1(df):

    df_ = pd.read_json(df, orient='split')

    fig = px.bar(hastag_counts(df_)[:20], y='#Tags', x='#Num', 
                 orientation='h')
    fig.update_yaxes(categoryorder='total ascending', title='')
    fig.update_layout(margin=dict(t=30, 
                                  pad=1), title_x=.5)
    return fig
    


@app.callback(Output('graph-4', 'figure'),
              [Input('df-sharing', 'children')])
def _update_div1(df):

    df_ = pd.read_json(df, orient='split')

    fig = px.bar(user_counts(df_)[:20], y='@user', x='#Num', orientation='h')
    fig.update_yaxes(categoryorder='total ascending', title='')
    fig.update_layout(margin=dict(t=30, 
                                  pad=3), autosize=False, title_x=.5)
    return fig
    

if __name__ == '__main__':
    app.run_server(debug=True)






