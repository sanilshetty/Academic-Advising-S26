import requests
import json
import time

url = "http://localhost:11434/api/generate"
data = {
    "model": "llama3",
    "prompt": "hi",
    "stream": False
}

print("Sending request to Ollama API...")
start = time.time()
try:
    response = requests.post(url, json=data)
    end = time.time()
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    print(f"Time taken: {end - start:.2f} seconds")
except Exception as e:
    print(f"Error: {e}")
