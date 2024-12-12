import os
from flask import Flask, render_template, request, redirect
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import time as t  # Renamed the time module to t
import concurrent.futures

from config import get_settings

app = Flask(__name__)
CORS(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'yv7%Ff6L%23vfE4G&fv3'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable CSRF protection for simplicity

jwt = JWTManager(app)

settings, config = get_settings()

# Port configuration
port = settings.get('port')

# Function to get MySQL connection
def get_db_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**config)
    except Error as e:
        print(f"Error: {e}")
    return connection

# Function to perform automatic insertion and calculate duration
def auto_insert_task(i):
    task_content = f"Automatic Task {i+1}"
    start_time = t.time()  # Record the start time

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO todo (content) VALUES (%s)", (task_content,))
            connection.commit()

            end_time = t.time()  # Record the end time
            duration = end_time - start_time  # Calculate the duration
            print(f"Inserted automatic task: {task_content}, Duration: {duration:.4f} seconds")
        except Error as e:
            connection.rollback()
            print(f'There was an issue adding your task: {e}')
        finally:
            cursor.close()
            connection.close()

# Automatically insert tasks when the app starts
def auto_insert_tasks():
    # Check if the tasks have already been inserted
    if not os.path.exists('tasks_inserted.txt'):
        start_time = t.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            k = 10000
            executor.map(auto_insert_task, range(k))
        end_time = t.time()
        total_duration = end_time - start_time
        print(f"Inserted {k} async tasks in {total_duration:.2f} seconds")

        # Create a file to indicate that the tasks have been inserted
        with open('tasks_inserted.txt', 'w') as f:
            f.write('Tasks have been inserted')
    else:
        print("Tasks have already been inserted.")

# Insert tasks in the table
auto_insert_tasks()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=port)
