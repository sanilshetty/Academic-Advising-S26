import streamlit as st
import os
import shutil
from rag_pipeline import get_rag_chain, get_retriever
from ingest import create_vector_db
import pypdf

def extract_text_from_pdf(fileobj):
    try:
        reader = pypdf.PdfReader(fileobj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {e}"

st.set_page_config(page_title="Purdue CS CODO Advisor", layout="wide")

st.title("🚂 Purdue CS CODO Eligibility Advisor")
st.markdown("Automated eligibility checker for switching to Computer Science.")

# Sidebar for Setup/Data Management
with st.sidebar:
    st.header("Knowledge Base")
    
    # 1. File Uploader
    uploaded_files = st.file_uploader(
        "Upload Transcripts/Docs", 
        type=["pdf", "txt"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        save_btn = st.button("Save & Ingest Files")
        if save_btn:
            with st.spinner("Processing files..."):
                save_dir = "data/raw_data"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                    
                for uploaded_file in uploaded_files:
                    path = os.path.join(save_dir, uploaded_file.name)
                    with open(path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                # Trigger Ingestion
                status = create_vector_db(reset=True)
                st.success(status)
                st.cache_resource.clear() # Reset cache to reload new DB
                
    st.divider()
    
    st.header("Personal Student Data")
    user_transcript = st.file_uploader("Upload your personal transcript (PDF/TXT)", type=["pdf", "txt"])
    transcript_content = "No transcript uploaded yet."
    
    if user_transcript:
        if user_transcript.type == "application/pdf":
            with st.spinner("Reading transcript..."):
                transcript_content = extract_text_from_pdf(user_transcript)
        else:
            transcript_content = user_transcript.read().decode("utf-8")
        st.success("Transcript parsed successfully!")
        with st.expander("View parsed transcript"):
            st.text(transcript_content)

    st.divider()
    
    st.header("System Status")
    if os.path.exists("data/vectordb"):
        st.success("Vector Database Active")
    else:
        st.error("Vector Database Missing!")
        if st.button("Initialize DB"):
             status = create_vector_db()
             st.info(status)

# Initialize Pipeline
@st.cache_resource
def load_pipeline():
    try:
        return get_rag_chain()
    except Exception as e:
        return None

chain = load_pipeline()

if not chain:
    st.warning("Pipeline could not be initialized. Please check the sidebar status.")
else:
    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Paste your transcript summary or ask about eligibility..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing eligibility rules..."):
                try:
                    from langchain_core.messages import HumanMessage, AIMessage
                    import time
                    
                    # Convert session state messages to LangChain format
                    chat_history = []
                    for m in st.session_state.messages[:-1]: # Exclude the current prompt
                        if m["role"] == "user":
                            chat_history.append(HumanMessage(content=m["content"]))
                        else:
                            chat_history.append(AIMessage(content=m["content"]))
                    
                    start_time = time.time()
                    # Pass both chat_history and the current question
                    response = chain.invoke({
                        "chat_history": chat_history,
                        "question": prompt,
                        "transcript_data": transcript_content
                    })
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    st.markdown(response)
                    st.metric(label="Inference Latency", value=f"{duration:.4f} sec")
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error generating response: {e}")

# Debugging: View Retrieved Docs (Testing feature)
with st.expander("Debug: Test Retrieval"):
    test_query = st.text_input("Enter a query to see retrieved chunks")
    if test_query and os.path.exists("data/vectordb"):
        try:
            retriever = get_retriever()
            docs = retriever.invoke(test_query)
            for i, doc in enumerate(docs):
                st.write(f"**Chunk {i+1}** (Source: {doc.metadata.get('source', 'Unknown')})")
                st.code(doc.page_content)
                st.divider()
        except Exception as e:
            st.error(f"Error accessing retriever: {e}")
