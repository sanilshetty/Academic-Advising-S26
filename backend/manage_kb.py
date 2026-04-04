import os
import shutil
import argparse
import subprocess
import sys

# Configuration
DATA_PATH = "data/raw_data"

def list_docs():
    """List all documents in the raw data directory."""
    if not os.path.exists(DATA_PATH):
        print(f"Directory {DATA_PATH} does not exist.")
        return

    files = os.listdir(DATA_PATH)
    if not files:
        print("No documents found in knowledge base.")
    else:
        print("\nDocuments in Knowledge Base:")
        for i, file in enumerate(files, 1):
            size = os.path.getsize(os.path.join(DATA_PATH, file)) / 1024
            print(f"{i}. {file} ({size:.2f} KB)")
    print()

def add_doc(file_path, ingest=False):
    """Add a new document to the knowledge base."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    filename = os.path.basename(file_path)
    dest_path = os.path.join(DATA_PATH, filename)
    
    shutil.copy2(file_path, dest_path)
    print(f"Successfully added '{filename}' to {DATA_PATH}")

    if ingest:
        reingest(reset=True)

def remove_doc(filename, ingest=False):
    """Remove a document from the knowledge base."""
    target_path = os.path.join(DATA_PATH, filename)
    
    if os.path.exists(target_path):
        os.remove(target_path)
        print(f"Successfully removed '{filename}'")
        if ingest:
            reingest(reset=True)
    else:
        print(f"Error: Document '{filename}' not found in {DATA_PATH}")

def reingest(reset=True):
    """Trigger the ingestion process."""
    print("Starting re-ingestion process...")
    cmd = [sys.executable, "ingest.py"]
    if reset:
        cmd.append("--reset")
    
    try:
        subprocess.run(cmd, check=True)
        print("Re-ingestion completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during ingestion: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage the RAG knowledge base documents.")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    subparsers.add_parser("list", help="List all documents in the knowledge base.")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a document to the knowledge base.")
    add_parser.add_argument("path", help="Path to the file to add.")
    add_parser.add_argument("--ingest", action="store_true", help="Automatically re-ingest after adding.")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a document from the knowledge base.")
    remove_parser.add_argument("filename", help="Name of the file to remove.")
    remove_parser.add_argument("--ingest", action="store_true", help="Automatically re-ingest after removing.")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Trigger the ingestion process.")
    ingest_parser.add_argument("--no-reset", action="store_false", dest="reset", help="Do not reset the DB before ingesting.")
    ingest_parser.set_defaults(reset=True)

    args = parser.parse_args()

    if args.command == "list":
        list_docs()
    elif args.command == "add":
        add_doc(args.path, ingest=args.ingest)
    elif args.command == "remove":
        remove_doc(args.filename, ingest=args.ingest)
    elif args.command == "ingest":
        reingest(reset=args.reset)
    else:
        parser.print_help()
