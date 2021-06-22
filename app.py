from flask import Flask, render_template, request, redirect
#from dotenv import load_dotenv
# import boto3
# from boto3.s3.connection import S3Connection #can't use dotenv in heroku....
import os
import re #string parsing
import requests #to download html data
import pandas as pd
import numpy as np
from bokeh.plotting import figure, output_file, save
from bokeh.io import output_notebook, push_notebook, show, save
from bokeh.resources import CDN
from bokeh.embed import file_html, components
from bokeh.models import (HoverTool)

app = Flask(__name__)
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True

@app.route('/', methods = ['POST', 'GET'])
def main_func():
    APIdata = get_url()
    API = clean_data(APIdata)

    bokeh_graph = plot_chart(API, "Daily High Plot")
    script, div = components(bokeh_graph)
    return render_template("General_attempt.html", the_div=div, the_script=script)

def clean_data(APIdata):
    metadata = APIdata.pop("Meta Data")
    print (metadata)
    #print(APIdata)
    #API = pd.DataFrame.from_dict(APIdata)
    API = (pd.json_normalize(APIdata['Time Series (5min)'])).T
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

#    load_dotenv()
#    API_KEY = os.environ['MY_API_KEY']
    API_KEY = '4PJK6E44KAP57MW0'## S3Connection(os.environ['MY_API_KEY'])
    if request.method == 'POST':
        stock = request.form.get("stock_tick")
        url_nm = ("https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=" +
          stock + "&interval=5min&apikey=" #request.form['stock_tick']
          + API_KEY )#convert_input(request.form[stock_tick]) +
            #+"+4PJK6E44KAP57MW0"
        print("we are at post", url_nm)
    else :
         url_nm = ("https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=GOOG" +
          "&interval=5min&apikey=" + API_KEY )
         print("we are at get", url_nm)

    r = requests.get(url_nm)
    APIdata = r.json()
    return APIdata

def plot_chart(API, title, hover_tool=None):
    hover = create_hover_tool()
    bokeh_graph = figure(title = title, x_axis_type='datetime', plot_height=600, plot_width = 600)

    y=API[API['statetxt']=='high'].value
    x=API[API['statetxt']=='high'].datetime

    tools = []
    if hover_tool:
        tools = [hover_tool,]

    bokeh_graph.line(x,y)
    bokeh_graph.xaxis.axis_label = "date/time of day"
    bokeh_graph.yaxis.axis_label = "Price ($)"
    bokeh_graph.toolbar.logo = None
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
    return HoverTool(tooltips=hover_html)

def index():
  return render_template('index.html')

@app.route('/about')
def about():
  return render_template('about.html')

if __name__ == '__main__':
   app.run(host = "localhost", debug=True)
