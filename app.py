# -*- coding: utf-8 -*-
"""
Author: Mihai Criveti
Description: Retrieverworks UI: Streamlit UI for Retrieval Augmented Generation
"""

import streamlit as st
import requests
import pandas as pd
from pathlib import Path

# Set API base URLs (update this if the FastAPI app is running on a different host or port)
UPLOAD_API_URL = "http://localhost:8080/api/document_upload"
LIST_API_URL = "http://localhost:8080/api/documents"

# Page Configuration
st.set_page_config(page_title="Document Management", layout="wide")

# Title
st.title("Document Management Application")

# Tabs for Upload and List
tab1, tab2 = st.tabs(["Upload Document", "List Documents"])

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
