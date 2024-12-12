import os
from flask import Flask, render_template, request, redirect, jsonify
from pymongo import MongoClient
import time as t
import concurrent.futures

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient('mongodb://192.168.1.165:27017/')
db = client['test_ressource']
collection = db['test']

# Function to perform automatic insertion and calculate duration
def auto_insert_task(i):
    task_content = f"Automatic Task {i+1}"
    start_time = t.time()  # Record the start time

    try:
        result = collection.insert_one({'content': task_content})
        end_time = t.time()  # Record the end time
        duration = end_time - start_time  # Calculate the duration
        print(f"Inserted automatic task: {task_content}, Duration: {duration:.4f} seconds")
    except Exception as e:
        print(f'There was an issue adding your task: {e}')

# Automatically insert tasks when the app starts
def auto_insert_tasks():
    # Check if the tasks have already been inserted
    if not os.path.exists('tasks_inserted.txt'):
        start_time = t.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            k = 200000
            executor.map(auto_insert_task, range(k))
        end_time = t.time()
        total_duration = end_time - start_time
        print(f"Inserted {k} async tasks in {total_duration:.2f} seconds")

        # Create a file to indicate that the tasks have been inserted
        with open('tasks_inserted.txt', 'w') as f:
            f.write('Tasks have been inserted')
    else:
        print("Tasks have already been inserted.")

# Insert tasks in the database
auto_insert_tasks()

# Example route to get all items
@app.route('/items', methods=['GET'])
def get_items():
    items = list(collection.find())
    return jsonify(items)

# Example route to create a new item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    item_id = collection.insert_one(data).inserted_id
    return jsonify({'id': str(item_id)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
