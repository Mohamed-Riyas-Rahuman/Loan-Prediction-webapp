#!/bin/bash
# Initialize database tables on startup. 
# This command runs init_db() which creates tables if they don't exist.
python -c "from app import init_db; init_db()"

# Start the Gunicorn server, binding to the port provided by Render
# The format is app_file:flask_app_instance
gunicorn --bind 0.0.0.0:$PORT app:app