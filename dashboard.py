import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import datetime

# Sample data
data = [
    {
        "timestamp": "2024-06-12 15:04:10",
        "cpu_usage_per_core": [11.9, 55, 74],
        "ram_total": 2058899456,
        "ram_used": 656138240,
        "ram_free": 1195724800,
        "ram_usage_percent": 41.9,
        "disk_total": 34688729088,
        "disk_used": 10793926656,
        "disk_free": 22283919360,
        "disk_usage_percent": 32.6,
        "swap_total": 2147479552,
        "swap_used": 260919296,
        "swap_free": 1886560256,
        "swap_usage_percent": 12.2,
        "uptime": 1713762386
    },
    {
        "timestamp": "2024-06-12 15:03:09",
        "cpu_usage_per_core": [47.1, 26.7, 6.7],
        "ram_total": 2058899456,
        "ram_used": 656105472,
        "ram_free": 1195749376,
        "ram_usage_percent": 41.9,
        "disk_total": 34688729088,
        "disk_used": 10793697280,
        "disk_free": 22284148736,
        "disk_usage_percent": 32.6,
        "swap_total": 2147479552,
        "swap_used": 260919296,
        "swap_free": 1886560256,
        "swap_usage_percent": 12.2,
        "uptime": 1713762386
    },
    {
        "timestamp": "2024-06-12 15:02:08",
        "cpu_usage_per_core": [7.5, 4.9, 62.6],
        "ram_total": 2058899456,
        "ram_used": 655466496,
        "ram_free": 1196400640,
        "ram_usage_percent": 41.9,
        "disk_total": 34688729088,
        "disk_used": 10793422848,
        "disk_free": 22284423168,
        "disk_usage_percent": 32.6,
        "swap_total": 2147479552,
        "swap_used": 260919296,
        "swap_free": 1886560256,
        "swap_usage_percent": 12.2,
        "uptime": 1713762386
    },
    {
        "timestamp": "2024-06-12 15:01:07",
        "cpu_usage_per_core": [2, 0, 2],
        "ram_total": 2058899456,
        "ram_used": 658165760,
        "ram_free": 1193697280,
        "ram_usage_percent": 42,
        "disk_total": 34688729088,
        "disk_used": 10793205760,
        "disk_free": 22284640256,
        "disk_usage_percent": 32.6,
        "swap_total": 2147479552,
        "swap_used": 260919296,
        "swap_free": 1886560256,
        "swap_usage_percent": 12.2,
        "uptime": 1713762386
    }
]

# Create DataFrame
df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Flatten nested lists
df_long = df.explode('cpu_usage_per_core').reset_index(drop=True).rename(columns={'cpu_usage_per_core': 'cpu_usage_core'})

# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("System Resource Usage"), className="mb-2")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='ram-usage-graph'), md=6),
        dbc.Col(dcc.Graph(id='storage-usage-graph'), md=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='cpu-usage-graph'), md=6),
        dbc.Col(dcc.Graph(id='swap-usage-graph'), md=6)
    ]),
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0
    )
])

@app.callback(
    Output('ram-usage-graph', 'figure'),
    Output('storage-usage-graph', 'figure'),
    Output('cpu-usage-graph', 'figure'),
    Output('swap-usage-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n):
    # Update timestamp with current time
    current_time = datetime.datetime.now()
    df['timestamp'] = df['timestamp'] + pd.to_timedelta((current_time - df['timestamp'].max()).total_seconds(), unit='s')

    # RAM Usage
    fig_ram = px.bar(df, x='timestamp', y=['ram_used', 'ram_free'], title='RAM Usage Over Time', labels={'value': 'Bytes'})

    # Storage Usage
    fig_storage = px.bar(df, x='timestamp', y=['disk_used', 'disk_free'], title='Storage Usage Over Time', labels={'value': 'Bytes'})

    # CPU Core Usage
    fig_cpu = px.line(df_long, x='timestamp', y='cpu_usage_core', title='CPU Core Usage Over Time', labels={'cpu_usage_core': 'CPU Usage (%)'})

    # Swap Usage
    fig_swap = px.line(df, x='timestamp', y=['swap_used', 'swap_free'], title='Swap Usage Over Time', labels={'value': 'Bytes'})

    return fig_ram, fig_storage, fig_cpu, fig_swap

if __name__ == '__main__':
    app.run_server(debug=True)
