# Use the official Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the operator code to the container
COPY operator.py .

# Run the operator script
CMD ["kopf", "run", "--standalone", "--verbose", "operator.py"]
