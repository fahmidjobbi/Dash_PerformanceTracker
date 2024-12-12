from flask import Flask, render_template, request, redirect, jsonify, g
from pymongo import MongoClient
import time as t
import schedule
import threading
import requests
from bson import ObjectId

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['test_ressource']
collection = db['test2']
request_log_collection = db['request_log']
metrics_collection = db['metrics']

# Helper function to convert MongoDB documents to JSON serializable format
def convert_to_json_serializable(doc):
    if isinstance(doc, list):
        return [convert_to_json_serializable(d) for d in doc]
    elif isinstance(doc, dict):
        return {k: convert_to_json_serializable(v) for k, v in doc.items()}
    elif isinstance(doc, ObjectId):
        return str(doc)
    return doc

# Log each request
@app.before_request
def log_request():
    g.start_time = t.time()
    request_log = {
        'path': request.path,
        'method': request.method,
        'timestamp': g.start_time
    }
    request_log_collection.insert_one(request_log)

@app.after_request
def log_response(response):
    if hasattr(g, 'start_time'):
        duration = t.time() - g.start_time
        request_log_collection.update_one(
            {'timestamp': g.start_time},
            {'$set': {'duration': duration}}
        )
    return response

# Function to perform periodic insertion
def periodic_insert():
    try:
        record = {
            'timestamp': t.strftime('%Y-%m-%d %H:%M:%S', t.localtime()),
            'type': 1
        }
        collection.insert_one(record)
        print(f"Inserted record: {record}")
    except Exception as e:
        print(f'There was an issue adding your task: {e}')

# Function to count requests in the last 5 minutes and save the result
def count_requests_last_5_minutes():
    try:
        current_time = t.time()
        five_minutes_ago = current_time - 5 * 60
        count = request_log_collection.count_documents({'timestamp': {'$gte': five_minutes_ago}})
        result = {
            'timestamp': t.strftime('%Y-%m-%d %H:%M:%S', t.localtime(current_time)),
            'request_count': count
        }
        collection.insert_one(result)
        print(f"Inserted count record: {result}")
    except Exception as e:
        print(f'There was an issue counting requests: {e}')

# Function to calculate and log metrics every 10 minutes
def log_metrics():
    try:
        current_time = t.time()
        ten_minutes_ago = current_time - 10 * 60
        requests = list(request_log_collection.find({'timestamp': {'$gte': ten_minutes_ago}}))
        total_requests = len(requests)
        total_duration = sum(request['duration'] for request in requests if 'duration' in request)
        
        metrics = {
            'timestamp': t.strftime('%Y-%m-%d %H:%M:%S', t.localtime(current_time)),
            'total_requests': total_requests,
            'total_duration': total_duration,
            'average_duration': total_duration / total_requests if total_requests > 0 else 0
        }
        metrics_collection.insert_one(metrics)
        print(f"Inserted metrics record: {metrics}")
    except Exception as e:
        print(f'There was an issue logging metrics: {e}')

# Function to run scheduled tasks
def run_schedule():
    while not should_stop:
        schedule.run_pending()
        t.sleep(1)

# Schedule the periodic insert task and the request count task
schedule.every(1).minutes.do(periodic_insert)
schedule.every(5).minutes.do(count_requests_last_5_minutes)
schedule.every(10).minutes.do(log_metrics)

# Function to send GET and POST requests automatically
def send_get_request():
    try:
        response = requests.get('http://127.0.0.1:5000/items')
        if response.status_code == 200:
            print('GET request successful.')
        else:
            print(f'GET request failed with status code {response.status_code}.')
    except Exception as e:
        print(f'An error occurred: {e}')

def send_post_request():
    try:
        data = {'name': 'example_item', 'value': 'example_value'}
        response = requests.post('http://127.0.0.1:5000/items', json=data)
        if response.status_code == 200:
            print('POST request successful.')
        else:
            print(f'POST request failed with status code {response.status_code}.')
    except Exception as e:
        print(f'An error occurred: {e}')

def auto_run_requests():
    while not should_stop:
        send_get_request()
        t.sleep(1)  # Wait for 1 second before sending the next request
        send_post_request()
        t.sleep(1)  # Wait for 1 second before sending the next request

# Define a flag to indicate that the script should stop
should_stop = False

# Start the scheduling thread
schedule_thread = threading.Thread(target=run_schedule)
schedule_thread.start()

# Start the auto-request thread
auto_request_thread = threading.Thread(target=auto_run_requests)
auto_request_thread.start()

# Example route to get all items
@app.route('/items', methods=['GET'])
def get_items():
    items = list(collection.find())
    items = convert_to_json_serializable(items)  # Convert items to JSON serializable format
    return jsonify(items)

# Example route to create a new item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    item_id = collection.insert_one(data).inserted_id
    return jsonify({'id': str(item_id)})

if __name__ == '__main__':
    try:
        app.run(debug=True, host='127.0.0.1', port=5000)
    finally:
        # Stop the scheduling thread
        should_stop = True
        schedule_thread.join()

        # Stop the auto-request thread
        should_stop = True
        auto_request_thread.join()
