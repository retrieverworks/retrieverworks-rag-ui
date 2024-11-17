# -*- coding: utf-8 -*-
"""
Author: Mihai Criveti
Description: Retrieverworks UI: Streamlit UI for Retrieval Augmented Generation
"""

import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import json

# Set API base URLs
UPLOAD_API_URL = "http://localhost:8080/api/document_upload"
LIST_API_URL = "http://localhost:8080/api/documents"
RAG_BASE_URL = "http://localhost:8080/api/rag"

# Page Configuration
st.set_page_config(page_title="Retrieverworks", layout="wide")

# Title
st.title("Retrieverworks: Document Management & RAG")

# Tabs for different operations
tab1, tab2, tab3 = st.tabs(["Upload Document", "List Documents", "RAG Operations"])

with tab1:
    st.header("Upload a Document")

    # File Upload Widget
    uploaded_file = st.file_uploader("Choose a document to upload", type=["pdf", "docx", "txt", "xlsx"])

    # Description Input
    description = st.text_input("Description (Optional)", placeholder="Enter a brief description of the document")

    if st.button("Upload Document"):
        if uploaded_file is not None:
            try:
                # Prepare the file and description for upload
                with st.spinner("Uploading..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {"description": description}

                    # Send POST request to FastAPI document upload endpoint
                    response = requests.post(UPLOAD_API_URL, files=files, data=data)

                    # Check response status
                    if response.status_code == 200:
                        st.success("Document uploaded successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Failed to upload document. Status: {response.status_code}")
                        st.text(response.text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Please select a document to upload.")

with tab2:
    st.header("List of Uploaded Documents")

    if st.button("Refresh List"):
        try:
            with st.spinner("Fetching document list..."):
                # Send GET request to fetch the list of uploaded documents
                response = requests.get(LIST_API_URL)

                if response.status_code == 200:
                    documents = response.json()

                    if documents:
                        # Convert JSON to DataFrame for display
                        df = pd.DataFrame(documents)
                        st.dataframe(
                            df[
                                [
                                    "filename",
                                    "stored_filename",
                                    "content_type",
                                    "size",
                                    "timestamp",
                                    "path",
                                    "description",
                                ]
                            ],
                            use_container_width=True,
                        )
                    else:
                        st.info("No documents uploaded yet.")
                else:
                    st.error(f"Failed to fetch documents. Status: {response.status_code}")
                    st.text(response.text)

        except Exception as e:
            st.error(f"An error occurred: {e}")

with tab3:
    st.header("RAG Operations")
    
    # Create columns for different operations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Text Processing")
        
        # Text input for splitting
        text_input = st.text_area("Enter text to split", height=150)
        chunk_size = st.number_input("Chunk size", min_value=100, max_value=2000, value=500, step=100)
        
        if st.button("Split Text"):
            if text_input:
                try:
                    response = requests.post(
                        f"{RAG_BASE_URL}/split",
                        json={"text": text_input, "chunk_size": chunk_size}
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Split into {result['chunk_count']} chunks")
                        for i, chunk in enumerate(result['chunks'], 1):
                            with st.expander(f"Chunk {i}"):
                                st.text(chunk)
                    else:
                        st.error("Failed to split text")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter some text to split")
    
    with col2:
        st.subheader("PDF Processing")
        
        # PDF upload for conversion
        pdf_file = st.file_uploader("Upload PDF for conversion", type=["pdf"])
        
        if st.button("Convert PDF"):
            if pdf_file:
                try:
                    files = {"file": pdf_file}
                    response = requests.post(f"{RAG_BASE_URL}/convert/pdf", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Extracted {result['character_count']} characters")
                        with st.expander("View extracted text"):
                            st.text(result['text'])
                    else:
                        st.error("Failed to convert PDF")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please upload a PDF file")
    
    st.divider()
    
    # Vector operations section
    st.subheader("Vector Operations")
    
    # Text chunks for embedding
    chunks_input = st.text_area("Enter text chunks (one per line)", height=150)
    
    if st.button("Generate Embeddings"):
        if chunks_input:
            chunks = [chunk.strip() for chunk in chunks_input.split('\n') if chunk.strip()]
            try:
                response = requests.post(f"{RAG_BASE_URL}/embed", json=chunks)
                if response.status_code == 200:
                    result = response.json()
                    st.success(result['message'])
                    st.json(result)
                else:
                    st.error("Failed to generate embeddings")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please enter text chunks")
    
    st.divider()
    
    # Query section
    st.subheader("Query Documents")
    
    # Create three columns for query configuration
    query_col1, query_col2, query_col3 = st.columns(3)
    
    with query_col1:
        llm_backend = st.selectbox(
            "LLM Backend",
            ["ollama", "chatgpt", "fakellm"],
            help="Select the LLM backend to use"
        )
    
    with query_col2:
        if llm_backend == "ollama":
            model_name = st.text_input("Model name", "phi3.5:latest")
        elif llm_backend == "chatgpt":
            model_name = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4"])
        else:
            model_name = None
    
    with query_col3:
        max_results = st.number_input("Max context results", min_value=1, max_value=10, value=3)
    
    query_input = st.text_area("Enter your query", height=100)
    
    if st.button("Submit Query"):
        if query_input:
            try:
                query_data = {
                    "query": query_input,
                    "llm_backend": llm_backend,
                    "max_results": max_results
                }
                if model_name:
                    query_data["model_name"] = model_name
                
                with st.spinner("Processing query..."):
                    response = requests.post(f"{RAG_BASE_URL}/query", json=query_data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Query processed successfully")
                        
                        # Display answer
                        st.markdown("### Answer")
                        st.write(result['answer'])
                        
                        # Display context
                        with st.expander("View context chunks"):
                            for i, context in enumerate(result['context'], 1):
                                st.markdown(f"**Chunk {i}:**")
                                st.text(context)
                        
                        # Display backend info
                        st.markdown("### Backend Information")
                        st.json({
                            "llm_backend": result['llm_backend'],
                            "model_name": result['model_name']
                        })
                    else:
                        st.error("Failed to process query")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please enter a query")