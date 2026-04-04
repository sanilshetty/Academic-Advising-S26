# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Hugging Face exposes port 7860 by default for external web traffic
EXPOSE 7860

# Build the vector database on container launch, then start the FastAPI server
CMD ["sh", "-c", "python ingest.py && uvicorn server:app --host 0.0.0.0 --port 7860"]
