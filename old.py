from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import time
import concurrent.futures

# Create a Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Avoid overhead from tracking modifications
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

# Use a context manager to create the tables within the Flask application context
with app.app_context():
    db.create_all()

    # Function to perform automatic insertion and calculate duration
    def auto_insert_task(i):
        task_content = f"Automatic Task {i+1}"
        start_time = time.time()  # Record the start time
        
        new_task = Todo(content=task_content)
        try:
            db.session.add(new_task)
            db.session.commit()
            
            end_time = time.time()  # Record the end time
            duration = end_time - start_time  # Calculate the duration
            print(f"Inserted automatic task: {new_task.content}, Duration: {duration:.4f} seconds, ID: {new_task.id}")
        except Exception as e:
            db.session.rollback()
            print(f'There was an issue adding your task: {e}')

    # Automatically insert tasks when the app starts
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        k=20000
        executor.map(auto_insert_task, range(k))
    end_time = time.time()
    total_duration = end_time - start_time
    print(f"Inserted {k} async tasks in {total_duration:.2f} seconds")

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['task']
        
        start_time = time.time()  # Record the start time
        
        new_task = Todo(content=task_content)
        try:
            db.session.add(new_task)
            db.session.commit()
            
            end_time = time.time()  # Record the end time
            duration = end_time - start_time  # Calculate the duration
            print(f"Inserted task: {new_task.content}, Duration: {duration:.4f} seconds, ID: {new_task.id}")
            
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            return f'There was an issue adding your task: {e}'
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', tasks=tasks)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
