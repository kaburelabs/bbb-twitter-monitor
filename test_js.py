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
from dash.exceptions import PreventUpdate
import visdcc


# DATABASE_URL = config('DATABASE_URL')

# con = psycopg2.connect(DATABASE_URL, sslmode='require')

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

# app.index_string = """<!DOCTYPE html>
# <html>
#     <head>
#         {%metas%}
#         <title>{%title%}</title>
#         {%favicon%}
#         {%css%}
        
#         <script type='text/javascript' src='https://platform-api.sharethis.com/js/sharethis.js#property=5e8113b5c213f90019450492&product=inline-share-buttons&cms=website' async='async'></script>    
#         <script src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
#     </head>
#     <body>
#         {%app_entry%}
#         <footer>
#             {%config%}
#             {%scripts%}
#             {%renderer%}
#         </footer>
#     </body>
# </html>"""

# app.scripts.config.serve_locally = True
# app.css.config.serve_locally = True

import visdcc

def generate_html_table_from_df(df, id):
    Thead = html.Thead(
        [html.Tr([html.Th(col) for col in df.columns])]
    )
    Tbody = html.Tbody(
        [html.Tr(
            [html.Td( df.iloc[i, j], id = '{}_{}_{}'.format(id, i, j) ) for j in range(len(df.columns))]
         ) for i in range(len(df))]
    )
    return html.Table([Thead, Tbody], id = id, className = "display")

df = pd.DataFrame({'name': ['Jacky', 'Mei', 'Jay', 'Sandy', 'Jerry', 'Jimmy', 'Jeff',
                            'Jacky', 'Mei', 'Jay', 'Sandy', 'Jerry', 'Jimmy', 'Jeff',
                            'Jacky', 'Mei', 'Jay', 'Sandy', 'Jerry', 'Jimmy', 'Jeff'],
                   'age': [18, 71, 14, 56, 22, 28, 15,
                           18, 71, 14, 56, 22, 28, 15,
                           18, 71, 14, 56, 22, 28, 15]}, columns = ['name', 'age'])

app.layout = html.Div([
    html.Button('Add mousemove event', id = 'button'),
    visdcc.Run_js(id = 'javascript', run = "$('#datatable').DataTable()"),
    html.Br(),
    html.Div(
        generate_html_table_from_df(df, id = 'datatable'), 
        style = {'width': '40%'}
    ),
    html.Div(id = 'output_div')
])
           
@app.callback(
    Output('javascript', 'run'),
    [Input('button', 'n_clicks')])
def myfun(x): 
    if x is None: return ''
    return '''
    var target = $('#datatable')[0]
    target.addEventListener('mousemove', function(evt) {
        setProps({ 
            'event': {'x':evt.x, 
                      'y':evt.y }
        })
        console.log(evt)
    })
    console.log(this)
    '''

@app.callback(
    Output('output_div', 'children'),
    [Input('javascript', 'event')])
def myfun(x): 
    return str(x)  



if __name__ == '__main__':
    app.run_server(debug=True)






