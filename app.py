from flask import Flask, render_template, request, redirect
#from dotenv import load_dotenv
# import boto3
import boto
#from boto3.s3.connection import S3Connection #can't use dotenv in heroku....
import os
import re #string parsing
import requests #to download html data
import pandas as pd
import numpy as np
from bokeh.plotting import figure, output_file, save
from bokeh.io import output_notebook, push_notebook, show, save
from bokeh.resources import CDN
from bokeh.embed import file_html, components
from bokeh.models import HoverTool, CrosshairTool
#HELLO
app = Flask(__name__)
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True

@app.route('/', methods = ['POST', 'GET'])
def main_func():
    # dropdown() #make the drop down
    # length = pickfromdropdown()
    #APIdata =
    API, stock = get_url() #clean_data(APIdata)

    type = get_type()

    if request.method == 'POST':
        titstr = "Stock Data For " + stock
    else:
        titstr = "Stock Data For IBM"

    bokeh_graph = plot_chart(API, titstr, type)
    script, div = components(bokeh_graph)
    return render_template("stock_price_app.html", the_div=div, the_script=script)

def get_type():
    if request.method == 'POST':
        type = request.form.get('type')
    else:
        type = 'high'
    return type

def clean_data(APIdata):
    metadata = APIdata.pop("Meta Data")

    metadatastr = 'Time Series (60min)'
    API = (pd.json_normalize(APIdata[ metadatastr ])).T
    API2= list((API).index)

    def conv_dt(fnx, dt):
      test= re.search("(\d+[-]\d+[-]\d+\s\d+[:]\d+[:]\d+)\.(\d+)\.\s(\w+)", fnx[dt])
      return test

    API['datetime']= pd.to_datetime([(conv_dt(API2,tm))[1] for tm in range(len(API2))])
    API['state'] = [(conv_dt(API2,tm))[2] for tm in range(len(API2))]
    API['statetxt'] = [(conv_dt(API2,tm))[3] for tm in range(len(API2))]

    API = API.reset_index(drop=True);
    API.rename(columns={0 :'value'}, inplace= True)
    API['value'] = pd.to_numeric(API['value'], downcast="float")
    return API

def get_url():
    print(request.method)
    API_KEY = '4PJK6E44KAP57MW0'# S3Connection(os.environ['MY_API_KEY']) #'4PJK6E44KAP57MW0'

    if request.method == 'POST':
        stock = request.form.get("stock_tick")
        length = 'TIME_SERIES_INTRADAY' #request.form.get('length')

        url_nm = ("https://www.alphavantage.co/query?function="+length+"&symbol=" +
          stock + "&interval=60min&outputsize=full&apikey=" #request.form['stock_tick']
          + API_KEY )
    else :
         url_nm = ("https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM" +
          "&interval=60min&outputsize=full&apikey=" + API_KEY )
         stock = 'IBM'

    r = requests.get(url_nm)
    APIdata = r.json()

    API = clean_data(APIdata)
    return API, stock

def plot_chart(API, title, type):
    bokeh_graph = figure(title = title, x_axis_type='datetime', plot_height=600, plot_width = 1000)

    y=API[API['statetxt']==type].value
    x=API[API['statetxt']==type].datetime

    # tools = []
    # if hover_tool:
    #     tools = [hover_tool,]

    bokeh_graph.line(x,y, line_color = 'red', line_width=2,  hover_line_color='darkgrey', legend_label=type)
    bokeh_graph.xaxis.axis_label = "Date/Time"
    bokeh_graph.xaxis.axis_label_text_font_size = "16pt"
    bokeh_graph.xaxis.major_label_text_font_size = "16pt"
    bokeh_graph.yaxis.major_label_text_font_size = "16pt"
    bokeh_graph.title.text_font_size = '20pt'
    if request.method == 'POST':
        if type == 'volume':
            yaxstr = "Num of Units for "+request.form.get("stock_tick")
        else:
            yaxstr = "Price ($) for "+request.form.get("stock_tick")
    else:
        yaxstr = "Price ($) for IBM"
    bokeh_graph.yaxis.axis_label = yaxstr
    bokeh_graph.yaxis.axis_label_text_font_size = "20pt"
    bokeh_graph.toolbar.logo = None
    bokeh_graph.add_tools(HoverTool(tooltips=[("Date", '@x{%F %H:00}'), (type, '@y')], formatters={'@x': 'datetime'}))
    #bokeh_graph.add_tools(CrosshairTool())
    hover = create_hover_tool()
    return bokeh_graph

def create_hover_tool():
    """Generates the HTML for the Bokeh's hover data tool on our graph."""
    hover_html = """
      <div>
        <span class="hover-tooltip">$x</span>
      </div>
      <div>
        <span class="hover-tooltip">@bugs bugs</span>
      </div>
      <div>
        <span class="hover-tooltip">$@costs{0.00}</span>
      </div>
    """
    return HoverTool(tooltips=[('date', '@x'), ('Value', '@y')],
          formatters={'@x' : 'datetime'})

def index():
  return render_template('index.html')

@app.route('/about')
def about():
  return render_template('about.html')

if __name__ == '__main__':
   app.run(host = "localhost", debug=True)
