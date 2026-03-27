FROM python:3.10-slim

# Install nodejs to build the React frontend
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python backend dependencies first (caching optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Build the React frontend
# Setting VITE_API_URL empty ensures network requests are sent to the same domain (relative paths)
RUN cd frontend && npm install && VITE_API_URL="" npm run build

# Create vector database folder to prevent permissions issues
RUN mkdir -p data/vectordb && chmod -R 777 data

# Hugging Face Spaces expects services on port 7860
EXPOSE 7860

# Start the FastAPI server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
