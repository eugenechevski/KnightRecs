# Dockerfile for Flask app with scikit-surprise
# Base image: lightweight Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (gcc and build-essential needed for scikit-surprise)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Copy trained model and necessary data files
# Note: model.pkl must be trained before building the image
COPY model.pkl .
COPY trainset.pkl .
COPY ml-latest/movies.csv ./ml-latest/movies.csv

# Expose Flask port
EXPOSE 5000

# Run the Flask application
CMD ["python", "src/app.py"]
