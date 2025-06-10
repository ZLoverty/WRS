# Use an official Python runtime as a parent image.
# Using a specific version (e.g., python:3.9-slim-buster) is recommended
# for consistency and security.
FROM python:3.9-slim-buster

# Install build dependencies that are often required by Python packages with C extensions.
# apt-get update refreshes the package lists.
# build-essential provides essential compilation tools (gcc, make, etc.).
# These are removed at the end of the command to keep the final image size small.
# You might need to add other libraries here if specific packages require them
# (e.g., libpq-dev for PostgreSQL drivers, libffi-dev, etc.).
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements.txt file into the container.
COPY requirements.txt .

# Install any specified Python dependencies.
# Using --no-cache-dir helps keep the image size small.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container.
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
