import time
import os
import sys

# Add project root to sys.path to import rag_pipeline
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from rag_pipeline import get_rag_chain
except ImportError:
    print("Error: Could not import rag_pipeline. Make sure you are running this from the project root or tests directory.")
    sys.exit(1)

def test_groq_latency():
    print("Initializing RAG Pipeline with Groq...")
    try:
        chain = get_rag_chain()
    except Exception as e:
        print(f"Failed to initialize pipeline: {e}")
        return

    query = "What requirements are needed for CODO into CS?"
    print(f"Testing Latency with Query: '{query}'")
    
    start_time = time.time()
    try:
        response = chain.invoke(query)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nResponse: {response[:100]}...")
        print(f"\n⏱️ Time to First Token (Total Latency): {duration:.4f} seconds")
        
        if duration < 1.0:
            print("✅ SUCCESS: Latency is under 1 second!")
        else:
            print("⚠️ WARNING: Latency is over 1 second.")
            
    except Exception as e:
        print(f"Inference failed: {e}")

if __name__ == "__main__":
    test_groq_latency()
