import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from pymongo import MongoClient
import datetime

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017/"  # Change this if your MongoDB server is running on a different host/port
DB_NAME = "test_ressource"
COLLECTION_NAME = "ram"
logo = '/assets/logo-deeperincode.svg'

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# OCR extracted details
company_name = "Deeperincode"
address = "19 Mayıs Mah. Turaboğlu Sk. No:4 Kapı No:2 Kadıköy / ISTANBUL"
email = "info@deeperincode.com"
phone = "0850 532 4865"

# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/styles.css'])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src=logo, style={'height': '120px', 'width': '120px'}), width='auto'),
        dbc.Col(html.H1("System Resource Usage", className="mb-2", style={
            'display': 'inline-block',
            'verticalAlign': 'middle',
            'color': '#003366',  # Marine blue color
            'padding-top': '30px'  # Adjust as needed to align with logo
        }))
    ]),
    dbc.Row([
        dbc.Col(dcc.DatePickerRange(
            id='date-range-picker',
            start_date=datetime.date.today() - datetime.timedelta(hours=2),
            end_date=datetime.date.today(),
            display_format='YYYY-MM-DD',
            clearable=True
        ), width=4),
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='start-hour',
                    type='number',
                    min=0,
                    max=23,
                    value=0,
                    style={'width': '50px'}
                ), width=2),
                dbc.Col(dcc.Input(
                    id='start-minute',
                    type='number',
                    min=0,
                    max=59,
                    value=0,
                    style={'width': '50px'}
                ), width=2),
                dbc.Col(html.Label('Start Time'), width=2),
            ]),
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='end-hour',
                    type='number',
                    min=0,
                    max=23,
                    value=23,
                    style={'width': '50px'}
                ), width=2),
                dbc.Col(dcc.Input(
                    id='end-minute',
                    type='number',
                    min=0,
                    max=59,
                    value=59,
                    style={'width': '50px'}
                ), width=2),
                dbc.Col(html.Label('End Time'), width=2),
            ]),
        ], width=8),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='ram-usage-graph', style={'overflowX': 'scroll'}), md=6),
        dbc.Col(dcc.Graph(id='storage-usage-graph', style={'overflowX': 'scroll'}), md=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='cpu-usage-graph', style={'overflowX': 'scroll'}), md=6),
        dbc.Col(dcc.Graph(id='swap-usage-graph', style={'overflowX': 'scroll'}), md=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='core-selector',
            options=[],
            multi=True,
            placeholder="Select CPU Cores"
        ), md=6)
    ]),
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0
    ),

    dbc.Row([
        dbc.Col(
            html.Div([
                html.P("Contact us:", className="contact-title"),
            ], className="contact-card"),
            width=12
        )
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4(company_name, className="card-title"),
                    html.P(address, className="card-text"),
                    html.P(f"Email: {email}", className="card-text"),
                    html.P(f"Phone: {phone}", className="card-text")
                ])
            )
        )
    ])
])


def fetch_data_from_mongodb():
    data = list(collection.find())
    for item in data:
        item['_id'] = str(item['_id'])  # Convert ObjectId to string if needed
    return pd.DataFrame(data)

@app.callback(
    Output('ram-usage-graph', 'figure'),
    Output('storage-usage-graph', 'figure'),
    Output('cpu-usage-graph', 'figure'),
    Output('swap-usage-graph', 'figure'),
    Output('core-selector', 'options'),
    Input('date-range-picker', 'start_date'),
    Input('date-range-picker', 'end_date'),
    Input('start-hour', 'value'),
    Input('start-minute', 'value'),
    Input('end-hour', 'value'),
    Input('end-minute', 'value'),
    Input('interval-component', 'n_intervals'),
    Input('core-selector', 'value')
)
def update_graph(start_date, end_date, start_hour, start_minute, end_hour, end_minute, n, selected_cores):
    df = fetch_data_from_mongodb()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Filter data based on selected date and time range
    if start_date and end_date:
        start_datetime = pd.to_datetime(start_date) + datetime.timedelta(hours=start_hour, minutes=start_minute)
        end_datetime = pd.to_datetime(end_date) + datetime.timedelta(hours=end_hour, minutes=end_minute)
        df = df[(df['timestamp'] >= start_datetime) & (df['timestamp'] <= end_datetime)]
    else:
        df = df[(df['timestamp'] >= (datetime.datetime.now() - datetime.timedelta(hours=2)))]

    # Flatten nested lists for CPU usage
    df_long = df.explode('cpu_usage_per_core').reset_index(drop=True)
    df_long['core'] = df_long.groupby(['timestamp']).cumcount()
    df_long.rename(columns={'cpu_usage_per_core': 'cpu_usage_core'}, inplace=True)

    # Get unique cores
    unique_cores = df_long['core'].unique().tolist()
    core_options = [{'label': f'Core {i}', 'value': i} for i in unique_cores]

    # Filter data based on selected cores
    if selected_cores:
        df_long = df_long[df_long['core'].isin(selected_cores)]

    # RAM Usage
    fig_ram = px.bar(df, x='timestamp', y=['ram_used', 'ram_free'], title='RAM Usage Over Time', labels={'value': 'Bytes'})
    fig_ram.update_layout(xaxis={'rangeslider': {'visible': True}})

    # Storage Usage
    fig_storage = px.bar(df, x='timestamp', y=['disk_used', 'disk_free'], title='Storage Usage Over Time', labels={'value': 'Bytes'})
    fig_storage.update_layout(xaxis={'rangeslider': {'visible': True}})

    # CPU Core Usage
    fig_cpu = px.line(df_long, x='timestamp', y='cpu_usage_core', color='core', title='CPU Core Usage Over Time', labels={'cpu_usage_core': 'CPU Usage (%)'})
    fig_cpu.update_layout(xaxis={'rangeslider': {'visible': True}})

    # Swap Usage
    fig_swap = px.line(df, x='timestamp', y=['swap_used', 'swap_free'], title='Swap Usage Over Time', labels={'value': 'Bytes'})
    fig_swap.update_layout(xaxis={'rangeslider': {'visible': True}})

    return fig_ram, fig_storage, fig_cpu, fig_swap, core_options

if __name__ == '__main__':
    app.run_server(debug=True)
