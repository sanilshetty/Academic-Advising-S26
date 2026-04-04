from langchain_ollama import ChatOllama
import time

print("Initializing ChatOllama...")
llm = ChatOllama(model="llama3", temperature=0)

print("Invoking model...")
start = time.time()
try:
    response = llm.invoke("Hello, who are you?")
    end = time.time()
    print(f"Response: {response.content}")
    print(f"Time taken: {end - start:.2f} seconds")
except Exception as e:
    print(f"Error: {e}")
