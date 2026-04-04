import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from typing import List

# Custom implementation to bypass import error
class SimpleMultiQueryRetriever(BaseRetriever):
    retriever: BaseRetriever
    llm_chain: object 

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        # Generate varied queries
        # The chain returns a string, we split by lines
        response = self.llm_chain.invoke({"question": query})
        if isinstance(response, str):
            queries = [line.strip() for line in response.split("\n") if line.strip()]
        else:
            queries = [query] # Fallback
            
        # Retrieve docs for each query
        all_docs = []
        seen_content = set()
        
        # Include original query as fallback
        queries.append(query)
        
        for q in queries:
            # Clean up query (remove numbering like "1. ")
            clean_q = q.lstrip("0123456789. -")
            if not clean_q: continue
            
            docs = self.retriever.invoke(clean_q)
            for doc in docs:
                if doc.page_content not in seen_content:
                    seen_content.add(doc.page_content)
                    all_docs.append(doc)
                    
        return all_docs

# from langchain.retrievers.multi_query import MultiQueryRetriever (Removed due to import error)
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from langchain_groq import ChatGroq

load_dotenv()

DB_PATH = "data/vectordb"

# Groq Configuration
# Default: Fast & Cheap (llama-3.1-8b-instant)
# Assessment: Powerful (llama-3.3-70b-versatile)
GROQ_MODEL_FAST = "llama-3.1-8b-instant"
GROQ_MODEL_SMART = "llama-3.3-70b-versatile"

def get_retriever():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Vector DB not found at {DB_PATH}. Run ingest.py first.")
        
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embedding_function)
    
    # Base retriever with MMR
    base_retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 20}
    )
    
    return base_retriever

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def get_rag_chain():
    retriever = get_retriever()
    
    # Use Groq for inference
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
        
    llm = ChatGroq(
        model=GROQ_MODEL_FAST, 
        temperature=0,
        max_retries=3,
        api_key=api_key
    )

    # 1. Contextualize Question Chain
    # This re-writes the user's question to be standalone if they refer to previous history.
    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is."""
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ]
    )
    contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()

    # 2. Answer Chain
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ]
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # DEBUG FUNCTIONS
    import time
    def log_retrival_start(standalone_question):
        print(f"\n[DEBUG] 🚀 Contextualized Question: '{standalone_question}'")
        print("[DEBUG] ⏳ Querying Vector DB...")
        return standalone_question

    def log_retrieved(docs):
        print(f"[DEBUG] ✅ Retrieved {len(docs)} documents.")
        return docs

    def log_prompt(prompt_value):
        print("\n" + "="*50)
        print("[DEBUG] 📨 FINAL PROMPT SENT TO LLM:")
        print("="*50)
        # Print the system message (which is the first message in the prompt)
        messages = prompt_value.to_messages()
        if messages:
             print(messages[0].content)
        print("="*50 + "\n")
        return prompt_value

    # Constructing the full chain
    def contextualized_question(input_dict):
        if input_dict.get("chat_history"):
            return contextualize_q_chain
        else:
            return input_dict["question"]

    rag_chain = (
        RunnablePassthrough.assign(
            transcript_data=lambda x: x.get("transcript_data", "No transcript provided.")
        )
        | RunnablePassthrough.assign(
            context=(
                contextualize_q_chain 
                | log_retrival_start 
                | retriever 
                | log_retrieved 
                | format_docs
            )
        )
        | qa_prompt
        | log_prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

if __name__ == "__main__":
    try:
        print(f"Initializing RAG Pipeline with Groq model: {GROQ_MODEL_FAST}...")
        chain = get_rag_chain()
        print("RAG Pipeline initialized successfully.")
    except Exception as e:
        print(f"Error initializing pipeline: {e}")
