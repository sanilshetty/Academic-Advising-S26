from rag_pipeline import get_retriever
import warnings
warnings.filterwarnings("ignore")

try:
    retriever = get_retriever()
    # To see what's in the DB, we can just search for something generic or access the Chroma API directly.
    # Since we don't have direct access to the `db` object from here (it's inside get_retriever),
    # let's reconstruct the vector store access or just doing a broad search.
    
    print("\n--- Querying Vector DB for 'John Doe' ---")
    docs = retriever.invoke("John Doe")
    for doc in docs:
        print(f"\n[Source: {doc.metadata.get('source', 'Unknown')}]")
        print(doc.page_content[:300] + "...") # Preview

    print("\n\n--- Querying Vector DB for 'CS CODO' ---")
    docs = retriever.invoke("CS CODO requirements")
    for doc in docs:
        print(f"\n[Source: {doc.metadata.get('source', 'Unknown')}]")
        print(doc.page_content[:300] + "...") # Preview

except Exception as e:
    print(f"Error inspecting DB: {e}")
