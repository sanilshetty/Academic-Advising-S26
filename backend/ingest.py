import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import shutil

# Load environment variables
load_dotenv()

# Configuration
DATA_PATH = "data/raw_data"
DB_PATH = "data/vectordb"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

def create_vector_db(reset=False):
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if reset and os.path.exists(DB_PATH):
        print(f"Resetting database at {DB_PATH}...")
        try:
            # Try to delete using Chroma API first ( cleaner)
            db = Chroma(persist_directory=DB_PATH, embedding_function=embedding_function)
            db.delete_collection()
            print("Collection deleted via API.")
        except Exception as e:
            print(f"API reset failed: {e}. Attempting manual file deletion...")
            import shutil
            import time
            
            # Simple retry logic for Windows file locks
            for i in range(3):
                try:
                    shutil.rmtree(DB_PATH)
                    print("Database directory removed.")
                    break
                except Exception as ex:
                    if i < 2:
                        print(f"Retry {i+1} failed. Is the app running? Waiting...")
                        time.sleep(2)
                    else:
                        return f"Error: Could not reset database. Please close any applications (like Streamlit) using it. Details: {ex}"
        
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        return "Created data directory. Please add files."

    # Load Documents
    print("Loading documents...")
    documents = []
    
    # Load PDFs
    pdf_loader = DirectoryLoader(DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    documents.extend(pdf_loader.load())
    
    # Load Text files (for testing)
    txt_loader = DirectoryLoader(DATA_PATH, glob="*.txt", loader_cls=TextLoader)
    documents.extend(txt_loader.load())
    
    if not documents:
        return "No files found to ingest."

    # Split Documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)

    # Create/Update Vector Store
    # Initialize Chroma (persistent)
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=DB_PATH
    )
    
    return f"Success! Indexed {len(documents)} documents ({len(chunks)} chunks)."

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest documents into the vector database.")
    parser.add_argument("--reset", action="store_true", help="Reset the database before ingesting.")
    args = parser.parse_args()
    
    result = create_vector_db(reset=args.reset)
    print(result)
