# Use a lightweight official Python image as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# 1. Copy *only* the requirements file first
# (This caches dependencies and speeds up future builds)
COPY requirements.txt .

# 2. Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your application code into the image
COPY . .

# NOTE: We are NOT adding a CMD or ENTRYPOINT here.
# Why? Because we will use this ONE image to run
# THREE different commands (uvicorn, celery, streamlit)
# which we will specify in the docker-compose.yml file.