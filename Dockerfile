# Use an official Python runtime as a parent image.
# Using a specific version (e.g., python:3.9-slim-buster) is recommended
# for consistency and security.
FROM python:3.9-slim-buster

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements.txt file into the container.
COPY requirements.txt .

# Install any specified Python dependencies.
# Using --no-cache-dir helps keep the image size small.
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code (including main.py, readlib.py, rss.yaml)
# into the container at /app.
COPY . .

# Expose the port that the application will listen on.
# Cloud Run automatically sets the PORT environment variable to 8080 by default.
# Your application *must* listen on this port.
EXPOSE 8080

# Define the command to run your application when the container starts.
# Gunicorn is a production-ready WSGI HTTP server, highly recommended for Flask apps.
# The 'main:app' part tells Gunicorn to look for a Flask application instance
# named 'app' inside the 'main.py' file.
# The --bind 0.0.0.0:${PORT} ensures Gunicorn listens on the correct host and port.
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "main:app"]