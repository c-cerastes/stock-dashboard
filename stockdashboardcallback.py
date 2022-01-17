
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import yfinance as yf
from bs4 import BeautifulSoup


app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        "Ticker: ",
        dcc.Input(id='ticker-input', value='TSLA', type='text')
    ]),
    html.Div([
        "Macro Trends URL: ",
        dcc.Input(id='url-input', value='https://www.macrotrends.net/stocks/charts/TSLA/tesla/revenue', type='text')
    ]),
    dcc.Graph(id='thefigure'),
])

# get the company ticker and the macro trends URL
# companyticker = input('Please enter the company ticker:\n')
# trendsurl = input('Please enter the macro trends URL:\n')

#callback
@app.callback(Output('thefigure','figure'),Input('ticker-input','value'),Input('url-input','value'))
def graphitall(companyticker,trendsurl):
    # extracting the historical stock data using yahoo finance package and assign it to a dataframe
    company = yf.Ticker(companyticker)
    companydata = pd.DataFrame(company.history(period="max"))
    companydata.reset_index(inplace=True)

    # extracting the quarterly revenue data from macro trends URL page
    try:
        htmlpagetext = requests.get(trendsurl).text #attempts to get the request
    except:
        print("Invalid URL. Please enter another (make sure you're on macro trends and have the stock revenue page pulled up!")
    soup = BeautifulSoup(htmlpagetext, 'html5lib') # parses html data using the html5lib
    yearlytable = soup.find_all("tbody")[1] #gets the second instance of tbody on the page
    revenue_data = pd.DataFrame(columns=['quarter','revenue']) #initializing the revenue dataframe
    for row in yearlytable.find_all('tr'): #for every row in the first instance of tbody
        allthecols = row.find_all('td') #get a lost of all the columns
        year = allthecols[0].text #first item in the list to year
        revenue = allthecols[1].text #second item in the list to revenue
        #append values to the dataframe
        revenue_data = revenue_data.append({'quarter':year,'revenue':revenue},ignore_index=True)
    revenue_data['revenue']=revenue_data['revenue'].str.replace(',|\$','',regex=True)#prepares the data so it cam be converted into int better
    revenue_data.dropna(inplace=True)#drops rows with NaN values
    revenue_data=revenue_data[revenue_data['revenue']!='']#drops rows with empty strings in revenue col

    def generategraph(companydata,revenue_data,companyticker): #graphing function definition
        fig = make_subplots(
            rows=2, cols=1,shared_xaxes=True,subplot_titles=(companyticker+" Historical Share Price (USD)",trendsurl+" Historical Revenue (Millions)"),vertical_spacing=0.2
        )
        fig.add_trace(
            go.Scatter(
                x=pd.to_datetime(companydata['Date'],infer_datetime_format=True),
                y=companydata['Close'].astype("float"),
                name=companyticker+' Share Price (USD)'
            ),row=1,col=1
        )
        fig.add_trace(
            go.Bar(
                x=pd.to_datetime(revenue_data['quarter'],infer_datetime_format=True),
                y=revenue_data['revenue'].astype("int"),
                name=trendsurl+' Revenue (Millions)'
            ),row=2,col=1
        )
        fig.update_xaxes(title_text="Date",row=2,col=1)
        fig.update_yaxes(title_text="Share Price (USD)",row=1,col=1)
        fig.update_yaxes(title_text="Revenue (Millions USD)",row=2,col=1)
        fig.update_layout(showlegend=False,title="Share Price and Revenue",height=900)
        return fig
    return generategraph(companydata,revenue_data,companyticker) #calling the graphing function

app.run_server(debug=True)