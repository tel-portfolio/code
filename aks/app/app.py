from flask import Flask, request, jsonify
import os

# This is the line Flask is looking for!
# It creates an instance of the Flask application.
app = Flask(__name__)

# Add a basic route so it does something
@app.route('/')
def home():
    # Read the welcome message from an environment variable (for Day 3)
    # We use a default "Hello, World!" for now
    message = os.environ.get('WELCOME_MESSAGE', 'Hello from your Python App!')
    return jsonify(message=message)

# Health check endpoint for Day 15
@app.route('/healthz')
def healthz():
    return jsonify(status="ok"), 200

# This block is what the `CMD ["python", "app.py"]` command will run
if __name__ == '__main__':
    # We run on 0.0.0.0 to make it accessible outside the container
    app.run(host='0.0.0.0', port=5000)

