#!/usr/bin/env python3
"""
Enhanced Reliance GRN Parser with Google Drive Integration
Combines local PDF upload and Google Drive processing workflows
"""

import streamlit as st
import pandas as pd
import re
import fitz
from io import BytesIO
from collections import defaultdict
import time
import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Google API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Streamlit Config
st.set_page_config(
    page_title="Reliance GRN Parser Pro+",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📦"
)

# Enhanced CSS for Modern UI
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global Styles */
.main {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.stApp {
    background: transparent;
}

/* Header Styling */
.main-header {
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(25px);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    text-align: center;
}

.main-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.main-subtitle {
    font-size: 1.2rem;
    color: #64748b;
    font-weight: 400;
    margin-bottom: 0;
}

/* Card Styling */
.glass-card {
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    margin-bottom: 2rem;
}

.upload-zone {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border: 2px dashed #667eea;
    border-radius: 16px;
    padding: 3rem 2rem;
    text-align: center;
    transition: all 0.3s ease;
}

.upload-zone:hover {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
}

/* Metrics Cards */
.metrics-container {
    display: flex;
    gap: 1rem;
    margin: 2rem 0;
}

.metric-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    flex: 1;
    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
    background: rgba(255, 255, 255, 0.98);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    display: block;
}

.metric-label {
    color: #64748b;
    font-size: 0.9rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Workflow Buttons */
.workflow-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 1rem 2rem;
    font-weight: 600;
    font-size: 1.1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    width: 100%;
    margin: 0.5rem 0;
}

.workflow-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    background: linear-gradient(135deg, #5a67d8 0%, #6b5b95 100%);
}

/* Drive workflow button */
.drive-btn {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
}

.drive-btn:hover {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4) !important;
}

/* Combined workflow button */
.combined-btn {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
    box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3) !important;
}

.combined-btn:hover {
    background: linear-gradient(135deg, #d97706 0%, #b45309 100%) !important;
    box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4) !important;
}

/* Progress Bar */
.stProgress .st-bo {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
}

/* Animation Classes */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-fade-in {
    animation: fadeInUp 0.6s ease-out;
}

/* Responsive Design */
@media (max-width: 768px) {
    .main-title {
        font-size: 2rem;
    }
    
    .metrics-container {
        flex-direction: column;
    }
    
    .metric-card {
        margin-bottom: 1rem;
    }
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

class RelianceGRNProcessor:
    def __init__(self):
        self.drive_service = None
        self.drive_scopes = ['https://www.googleapis.com/auth/drive.readonly']
    
    def authenticate_from_secrets(self, progress_bar, status_text):
        """Authenticate using Streamlit secrets with web-based OAuth flow"""
        try:
            status_text.text("Authenticating with Google Drive...")
            progress_bar.progress(10)
            
            # Check for existing token in session state
            if 'oauth_token' in st.session_state:
                try:
                    creds = Credentials.from_authorized_user_info(st.session_state.oauth_token, self.drive_scopes)
                    if creds and creds.valid:
                        progress_bar.progress(50)
                        self.drive_service = build('drive', 'v3', credentials=creds)
                        progress_bar.progress(100)
                        status_text.text("Authentication successful!")
                        return True
                except Exception as e:
                    st.info(f"Cached token invalid, requesting new authentication: {str(e)}")
            
            # Use Streamlit secrets for OAuth
            if "google" in st.secrets and "credentials_json" in st.secrets["google"]:
                creds_data = json.loads(st.secrets["google"]["credentials_json"])
                
                # Configure for web application
                flow = Flow.from_client_config(
                    client_config=creds_data,
                    scopes=self.drive_scopes,
                    redirect_uri="https://milkbasket-grn.streamlit.app/"  # Update this with your actual URL
                )
                
                # Generate authorization URL
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                # Check for callback code
                query_params = st.query_params
                if "code" in query_params:
                    try:
                        code = query_params["code"]
                        flow.fetch_token(code=code)
                        creds = flow.credentials
                        
                        # Save credentials in session state
                        st.session_state.oauth_token = json.loads(creds.to_json())
                        
                        progress_bar.progress(50)
                        self.drive_service = build('drive', 'v3', credentials=creds)
                        progress_bar.progress(100)
                        status_text.text("Authentication successful!")
                        
                        # Clear the code from URL
                        st.query_params.clear()
                        return True
                    except Exception as e:
                        st.error(f"Authentication failed: {str(e)}")
                        return False
                else:
                    # Show authorization link
                    st.markdown("### Google Drive Authentication Required")
                    st.markdown(f"[Authorize with Google Drive]({auth_url})")
                    st.info("Click the link above to authorize access to Google Drive, you'll be redirected back automatically")
                    st.stop()
            else:
                st.error("Google credentials missing in Streamlit secrets. Please add your Google OAuth2 credentials.")
                st.markdown("""
                **Setup Instructions:**
                1. Go to [Google Cloud Console](https://console.cloud.google.com)
                2. Create or select a project
                3. Enable Google Drive API
                4. Create OAuth2 credentials (Web application)
                5. Add your Streamlit app URL to authorized redirect URIs
                6. Add the credentials JSON to Streamlit secrets as `google.credentials_json`
                """)
                return False
                
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return False
    
    def list_drive_files(self, folder_id: str, days_back: int = 7) -> List[Dict]:
        """List PDF files in Drive folder"""
        try:
            if not folder_id:
                st.error("No folder ID provided")
                return []
            
            start_datetime = datetime.utcnow() - timedelta(days=days_back)
            start_str = start_datetime.strftime('%Y-%m-%dT00:00:00Z')
            
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false and createdTime > '{start_str}'"
            
            files = []
            page_token = None
            
            while True:
                results = self.drive_service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, createdTime, size)",
                    pageToken=page_token,
                    orderBy="createdTime desc"
                ).execute()
                
                files.extend(results.get('files', []))
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            st.info(f"Found {len(files)} PDF files in Drive folder")
            return files
            
        except Exception as e:
            st.error(f"Failed to list Drive files: {str(e)}")
            return []
    
    def download_from_drive(self, file_id: str) -> bytes:
        """Download file from Drive"""
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            file_data = request.execute()
            return file_data
        except Exception as e:
            st.error(f"Failed to download file {file_id}: {str(e)}")
            return b""
    
    def clean_text(self, text):
        """Clean extracted text"""
        return text.strip().replace('\n', ' ').replace('\r', ' ').replace('  ', ' ')

    def extract_text_from_pdf(self, pdf_bytes):
        """Extract text from PDF bytes"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            st.error(f"Failed to extract text from PDF: {str(e)}")
            return ""

    def extract_grn_data(self, text, source_filename=""):
        """Extract GRN data from text with enhanced patterns"""
        metadata = {
            "GRN No": None, "GRN Date": None, "Vendor Invoice No": None, "PO No": None,
            "PO Date": None, "Consignee Location": None, "Truck No": None, "Challan No": None,
            "Source File": source_filename
        }

        patterns = {
            "GRN No": r'GOODS RECEIPT NOTE No\.\s*:\s*(\S+)',
            "GRN Date": r'Date:\s*(\d{2}\.\d{2}\.\d{4})',
            "Vendor Invoice No": r'Vendor invoice no\s*:\s*(\S+)',
            "Consignee Location": r'Consignee\s*:\s*([^\n]+)\n',
            "PO No": r'PO Number\s*:\s*(\S+)',
            "PO Date": r'PO Number.*?Date\s*:\s*(\d{2}\.\d{2}\.\d{4})|(?<!\S)Date\s*:\s*(\d{2}\.\d{2}\.\d{4})',
            "Truck No": r'Truck/ Lorry/ Carrier No:\s*(\S+)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1) or match.group(2)

        if metadata["Vendor Invoice No"]:
            metadata["Challan No"] = metadata["Vendor Invoice No"]

        items = []
        table_start = re.search(r'S No\s+Article', text, re.IGNORECASE)
        if table_start:
            table_text = text[table_start.start():]
            item_pattern = re.compile(
                r'(\d+)\s+(\d+)\s+([\w\s\.\-%#]+?)\s+(\d{13})\s+(\w+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d\.]+)\b'
            )
            for match in item_pattern.finditer(table_text):
                description = re.sub(r'\s+', ' ', match.group(3).strip())
                items.append({
                    "S No": match.group(1), 
                    "Article": match.group(2), 
                    "Item Description": description,
                    "EAN Number": match.group(4), 
                    "UoM": match.group(5), 
                    "Challan Qty": match.group(6),
                    "Received Qty": match.group(7), 
                    "Accepted Qty": match.group(8), 
                    "MRP": match.group(9)
                })

        return metadata, items

# Session State Initialization
if 'df_result' not in st.session_state:
    st.session_state.df_result = None
if 'file_count' not in st.session_state:
    st.session_state.file_count = 0
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'workflow_mode' not in st.session_state:
    st.session_state.workflow_mode = None
if 'drive_config' not in st.session_state:
    st.session_state.drive_config = {
        'folder_id': '',
        'days_back': 30,
        'max_files': 100
    }

# Header Section
st.markdown("""
<div class="main-header animate-fade-in">
    <h1 class="main-title">📦 GRN Parser Pro+</h1>
    <p class="main-subtitle">Transform your Goods Receipt Note PDFs into organized Excel data with local upload or Google Drive integration</p>
</div>
""", unsafe_allow_html=True)

# Workflow Selection
st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
st.markdown("### 🚀 Choose Your Workflow")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📁 Local Upload Workflow", key="local_workflow", help="Upload PDF files directly from your computer"):
        st.session_state.workflow_mode = "local"

with col2:
    if st.button("☁️ Google Drive Workflow", key="drive_workflow", help="Process PDF files from Google Drive"):
        st.session_state.workflow_mode = "drive"

with col3:
    if st.button("🔄 Combined Workflow", key="combined_workflow", help="Upload locally AND process from Google Drive"):
        st.session_state.workflow_mode = "combined"

st.markdown('</div>', unsafe_allow_html=True)

# Workflow Configuration
if st.session_state.workflow_mode in ["drive", "combined"]:
    st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Google Drive Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        folder_id = st.text_input(
            "Google Drive Folder ID",
            value=st.session_state.drive_config['folder_id'],
            help="The ID of the Google Drive folder containing your PDF files",
            placeholder="1ABC123def456ghi789..."
        )
    
    with col2:
        days_back = st.number_input(
            "Days Back to Search",
            value=st.session_state.drive_config['days_back'],
            min_value=1,
            max_value=365,
            help="How many days back to search for files"
        )
    
    with col3:
        max_files = st.number_input(
            "Max Files to Process",
            value=st.session_state.drive_config['max_files'],
            min_value=1,
            max_value=500,
            help="Maximum number of files to process"
        )
    
    if st.button("Update Drive Settings"):
        st.session_state.drive_config = {
            'folder_id': folder_id,
            'days_back': days_back,
            'max_files': max_files
        }
        st.success("Drive settings updated!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Execute Workflows
if st.session_state.workflow_mode == "local":
    # Local Upload Workflow (Original functionality)
    st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="upload-zone">
            <h3 style="color: #667eea; margin-bottom: 1rem;">📁 Upload Your GRN PDFs</h3>
            <p style="color: #64748b; margin-bottom: 1.5rem;">Select multiple PDF files to process them all at once</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose PDF files", 
            type="pdf", 
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_files:
        # File Metrics
        st.session_state.file_count = len(uploaded_files)
        
        st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
        st.markdown("### 📊 Upload Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{len(uploaded_files)}</span>
                <div class="metric-label">Files Uploaded</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_size = sum(file.size for file in uploaded_files) / (1024 * 1024)
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{total_size:.2f}</span>
                <div class="metric-label">Total Size (MB)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_size = total_size / len(uploaded_files)
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{avg_size:.2f}</span>
                <div class="metric-label">Avg Size (MB)</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Processing Section
        st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Process All PDFs", key="process_local_btn"):
                processor = RelianceGRNProcessor()
                with st.spinner("📄 Processing your files..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    all_data = []
                    
                    for i, file in enumerate(uploaded_files):
                        status_text.text(f"Processing: {file.name}")
                        
                        text = processor.extract_text_from_pdf(file.read())
                        metadata, items = processor.extract_grn_data(text, file.name)
                        
                        if not items:
                            row = defaultdict(lambda: "")
                            row.update(metadata)
                            row["file_name"] = file.name
                            all_data.append(row)
                        else:
                            for item in items:
                                row = {**metadata, **item, "file_name": file.name}
                                all_data.append(row)
                        
                        progress_bar.progress((i + 1) / len(uploaded_files))
                        time.sleep(0.1)
                    
                    status_text.text("✅ Processing complete!")
                    
                    if all_data:
                        st.session_state.df_result = pd.DataFrame(all_data)
                        st.session_state.processing_complete = True
                        st.success("🎉 All files processed successfully!")
                    else:
                        st.session_state.df_result = pd.DataFrame()
                        st.warning("⚠️ No data could be extracted from the uploaded files.")
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.workflow_mode == "drive":
    # Google Drive Workflow
    processor = RelianceGRNProcessor()
    
    if not st.session_state.drive_config['folder_id']:
        st.warning("Please configure Google Drive folder ID above to proceed.")
    else:
        st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
        st.markdown("### ☁️ Google Drive Authentication")
        
        auth_progress = st.progress(0)
        auth_status = st.empty()
        
        if processor.authenticate_from_secrets(auth_progress, auth_status):
            st.success("🔑 Authentication successful!")
            
            # List files from Drive
            st.markdown("### 📂 Files from Google Drive")
            
            with st.spinner("📋 Loading files from Google Drive..."):
                drive_files = processor.list_drive_files(
                    st.session_state.drive_config['folder_id'],
                    st.session_state.drive_config['days_back']
                )
            
            if drive_files:
                # Limit files if specified
                if len(drive_files) > st.session_state.drive_config['max_files']:
                    drive_files = drive_files[:st.session_state.drive_config['max_files']]
                    st.info(f"Limited to {st.session_state.drive_config['max_files']} most recent files")
                
                # Drive Files Metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <span class="metric-value">{len(drive_files)}</span>
                        <div class="metric-label">Drive Files Found</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    total_size = sum(int(f.get('size', 0)) for f in drive_files) / (1024 * 1024)
                    st.markdown(f"""
                    <div class="metric-card">
                        <span class="metric-value">{total_size:.2f}</span>
                        <div class="metric-label">Total Size (MB)</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    oldest_file = min(drive_files, key=lambda x: x['createdTime'])['createdTime'][:10]
                    st.markdown(f"""
                    <div class="metric-card">
                        <span class="metric-value">{oldest_file}</span>
                        <div class="metric-label">Oldest File</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # File List Preview
                with st.expander("📋 Preview Drive Files", expanded=False):
                    file_df = pd.DataFrame([
                        {
                            'Name': f['name'], 
                            'Size (KB)': int(f.get('size', 0)) / 1024,
                            'Created': f['createdTime'][:19].replace('T', ' ')
                        } 
                        for f in drive_files[:10]  # Show first 10
                    ])
                    st.dataframe(file_df, use_container_width=True)
                    if len(drive_files) > 10:
                        st.info(f"... and {len(drive_files) - 10} more files")
                
                # Process Drive Files
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("☁️ Process Drive PDFs", key="process_drive_btn"):
                        with st.spinner("📄 Processing files from Google Drive..."):
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            all_data = []
                            
                            for i, file in enumerate(drive_files):
                                status_text.text(f"Processing: {file['name']}")
                                
                                # Download file from Drive
                                pdf_bytes = processor.download_from_drive(file['id'])
                                if pdf_bytes:
                                    text = processor.extract_text_from_pdf(pdf_bytes)
                                    metadata, items = processor.extract_grn_data(text, file['name'])
                                    
                                    if not items:
                                        row = defaultdict(lambda: "")
                                        row.update(metadata)
                                        row["file_name"] = file['name']
                                        row["drive_file_id"] = file['id']
                                        all_data.append(row)
                                    else:
                                        for item in items:
                                            row = {**metadata, **item, "file_name": file['name'], "drive_file_id": file['id']}
                                            all_data.append(row)
                                
                                progress_bar.progress((i + 1) / len(drive_files))
                                time.sleep(0.1)
                            
                            status_text.text("✅ Drive processing complete!")
                            
                            if all_data:
                                st.session_state.df_result = pd.DataFrame(all_data)
                                st.session_state.processing_complete = True
                                st.success("🎉 All Drive files processed successfully!")
                            else:
                                st.session_state.df_result = pd.DataFrame()
                                st.warning("⚠️ No data could be extracted from the Drive files.")
            else:
                st.warning("📂 No PDF files found in the specified Google Drive folder.")
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.workflow_mode == "combined":
    # Combined Workflow - Local Upload + Google Drive
    processor = RelianceGRNProcessor()
    
    st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown("### 🔄 Combined Processing Workflow")
    st.info("This workflow will process both locally uploaded files AND files from Google Drive")
    
    # Local Upload Section
    st.markdown("#### 📁 Step 1: Upload Local Files (Optional)")
    uploaded_files = st.file_uploader(
        "Choose PDF files from your computer", 
        type="pdf", 
        accept_multiple_files=True
    )
    
    # Google Drive Section
    st.markdown("#### ☁️ Step 2: Configure Google Drive")
    
    if not st.session_state.drive_config['folder_id']:
        st.warning("Please configure Google Drive folder ID in the configuration section above.")
        drive_files = []
        drive_authenticated = False
    else:
        # Authenticate with Google Drive
        auth_progress = st.progress(0)
        auth_status = st.empty()
        
        drive_authenticated = processor.authenticate_from_secrets(auth_progress, auth_status)
        
        if drive_authenticated:
            st.success("🔐 Google Drive authentication successful!")
            
            with st.spinner("📋 Loading files from Google Drive..."):
                drive_files = processor.list_drive_files(
                    st.session_state.drive_config['folder_id'],
                    st.session_state.drive_config['days_back']
                )
                
                if len(drive_files) > st.session_state.drive_config['max_files']:
                    drive_files = drive_files[:st.session_state.drive_config['max_files']]
        else:
            drive_files = []
    
    # Combined Metrics
    if uploaded_files or drive_files:
        st.markdown("#### 📊 Combined Processing Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            local_count = len(uploaded_files) if uploaded_files else 0
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{local_count}</span>
                <div class="metric-label">Local Files</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            drive_count = len(drive_files)
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{drive_count}</span>
                <div class="metric-label">Drive Files</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_count = local_count + drive_count
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{total_count}</span>
                <div class="metric-label">Total Files</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Calculate total size
            local_size = sum(file.size for file in uploaded_files) / (1024 * 1024) if uploaded_files else 0
            drive_size = sum(int(f.get('size', 0)) for f in drive_files) / (1024 * 1024)
            total_size = local_size + drive_size
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{total_size:.1f}</span>
                <div class="metric-label">Total Size (MB)</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Process Combined Files
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Process All Files (Local + Drive)", key="process_combined_btn"):
                with st.spinner("🔄 Processing combined files..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    all_data = []
                    
                    total_files = total_count
                    processed_count = 0
                    
                    # Process local files first
                    if uploaded_files:
                        status_text.text("📁 Processing local files...")
                        for file in uploaded_files:
                            status_text.text(f"Processing local: {file.name}")
                            
                            text = processor.extract_text_from_pdf(file.read())
                            metadata, items = processor.extract_grn_data(text, file.name)
                            
                            if not items:
                                row = defaultdict(lambda: "")
                                row.update(metadata)
                                row["file_name"] = file.name
                                row["source"] = "local"
                                all_data.append(row)
                            else:
                                for item in items:
                                    row = {**metadata, **item, "file_name": file.name, "source": "local"}
                                    all_data.append(row)
                            
                            processed_count += 1
                            progress_bar.progress(processed_count / total_files)
                            time.sleep(0.1)
                    
                    # Process Drive files
                    if drive_files and drive_authenticated:
                        status_text.text("☁️ Processing Google Drive files...")
                        for file in drive_files:
                            status_text.text(f"Processing Drive: {file['name']}")
                            
                            # Download file from Drive
                            pdf_bytes = processor.download_from_drive(file['id'])
                            if pdf_bytes:
                                text = processor.extract_text_from_pdf(pdf_bytes)
                                metadata, items = processor.extract_grn_data(text, file['name'])
                                
                                if not items:
                                    row = defaultdict(lambda: "")
                                    row.update(metadata)
                                    row["file_name"] = file['name']
                                    row["source"] = "drive"
                                    row["drive_file_id"] = file['id']
                                    all_data.append(row)
                                else:
                                    for item in items:
                                        row = {**metadata, **item, "file_name": file['name'], 
                                               "source": "drive", "drive_file_id": file['id']}
                                        all_data.append(row)
                            
                            processed_count += 1
                            progress_bar.progress(processed_count / total_files)
                            time.sleep(0.1)
                    
                    status_text.text("✅ Combined processing complete!")
                    
                    if all_data:
                        st.session_state.df_result = pd.DataFrame(all_data)
                        st.session_state.processing_complete = True
                        st.success("🎉 All files processed successfully!")
                    else:
                        st.session_state.df_result = pd.DataFrame()
                        st.warning("⚠️ No data could be extracted from any files.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Results Display Section
if st.session_state.processing_complete and st.session_state.df_result is not None:
    st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown("### 📊 Processing Results")
    
    if not st.session_state.df_result.empty:
        # Results metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_rows = len(st.session_state.df_result)
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{total_rows}</span>
                <div class="metric-label">Total Records</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            unique_grns = st.session_state.df_result['GRN No'].nunique() if 'GRN No' in st.session_state.df_result.columns else 0
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{unique_grns}</span>
                <div class="metric-label">Unique GRNs</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            unique_files = st.session_state.df_result['file_name'].nunique() if 'file_name' in st.session_state.df_result.columns else 0
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{unique_files}</span>
                <div class="metric-label">Files Processed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Check if source column exists (for combined workflow)
            if 'source' in st.session_state.df_result.columns:
                local_count = len(st.session_state.df_result[st.session_state.df_result['source'] == 'local'])
                drive_count = len(st.session_state.df_result[st.session_state.df_result['source'] == 'drive'])
                source_info = f"L:{local_count} D:{drive_count}"
            else:
                source_info = "Single"
            
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value" style="font-size: 1.8rem;">{source_info}</span>
                <div class="metric-label">Source Split</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Data Preview
        st.markdown("#### 👁️ Data Preview")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            if 'GRN No' in st.session_state.df_result.columns:
                grn_filter = st.selectbox(
                    "Filter by GRN No:",
                    ['All'] + list(st.session_state.df_result['GRN No'].dropna().unique())
                )
            else:
                grn_filter = 'All'
        
        with col2:
            if 'source' in st.session_state.df_result.columns:
                source_filter = st.selectbox(
                    "Filter by Source:",
                    ['All', 'local', 'drive']
                )
            else:
                source_filter = 'All'
        
        # Apply filters
        filtered_df = st.session_state.df_result.copy()
        
        if grn_filter != 'All':
            filtered_df = filtered_df[filtered_df['GRN No'] == grn_filter]
        
        if source_filter != 'All' and 'source' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['source'] == source_filter]
        
        # Display filtered data
        st.dataframe(filtered_df, use_container_width=True, height=400)
        
        # Download Section
        st.markdown("#### 📥 Download Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Excel download
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, sheet_name='GRN_Data', index=False)
                
                # Add summary sheet if we have multiple sources
                if 'source' in st.session_state.df_result.columns:
                    summary_data = {
                        'Metric': ['Total Records', 'Local Files', 'Drive Files', 'Unique GRNs'],
                        'Value': [
                            len(st.session_state.df_result),
                            len(st.session_state.df_result[st.session_state.df_result['source'] == 'local']),
                            len(st.session_state.df_result[st.session_state.df_result['source'] == 'drive']),
                            st.session_state.df_result['GRN No'].nunique()
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            processed_data = output.getvalue()
            
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"grn_data_{current_time}.xlsx"
            
            st.download_button(
                label="📊 Download Excel",
                data=processed_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download the processed data as Excel file"
            )
        
        with col2:
            # CSV download
            csv_data = filtered_df.to_csv(index=False)
            csv_filename = f"grn_data_{current_time}.csv"
            
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=csv_filename,
                mime="text/csv",
                help="Download the processed data as CSV file"
            )
        
        with col3:
            # JSON download
            json_data = filtered_df.to_json(orient='records', indent=2)
            json_filename = f"grn_data_{current_time}.json"
            
            st.download_button(
                label="🔗 Download JSON",
                data=json_data,
                file_name=json_filename,
                mime="application/json",
                help="Download the processed data as JSON file"
            )
        
        # Data Quality Report
        with st.expander("📈 Data Quality Report", expanded=False):
            st.markdown("#### Data Completeness Analysis")
            
            # Calculate completeness for key fields
            key_fields = ['GRN No', 'GRN Date', 'Vendor Invoice No', 'PO No', 'Consignee Location']
            completeness_data = []
            
            for field in key_fields:
                if field in st.session_state.df_result.columns:
                    total = len(st.session_state.df_result)
                    non_null = st.session_state.df_result[field].notna().sum()
                    non_empty = (st.session_state.df_result[field].astype(str).str.strip() != '').sum()
                    completeness = (non_empty / total) * 100 if total > 0 else 0
                    
                    completeness_data.append({
                        'Field': field,
                        'Total Records': total,
                        'Non-Empty': non_empty,
                        'Completeness %': f"{completeness:.1f}%"
                    })
            
            if completeness_data:
                completeness_df = pd.DataFrame(completeness_data)
                st.dataframe(completeness_df, use_container_width=True)
            
            # File processing summary
            if 'file_name' in st.session_state.df_result.columns:
                st.markdown("#### File Processing Summary")
                file_summary = st.session_state.df_result.groupby('file_name').size().reset_index(name='Records Extracted')
                file_summary = file_summary.sort_values('Records Extracted', ascending=False)
                st.dataframe(file_summary, use_container_width=True)
    
    else:
        st.warning("⚠️ No data was extracted from the processed files. Please check your PDF files and try again.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Reset/Clear Section
if st.session_state.processing_complete:
    st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Process New Files", key="reset_btn", help="Clear current results and process new files"):
            # Reset session state
            st.session_state.df_result = None
            st.session_state.file_count = 0
            st.session_state.processing_complete = False
            st.session_state.workflow_mode = None
            # Clear OAuth token if needed
            if 'oauth_token' in st.session_state:
                del st.session_state.oauth_token
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 2rem; color: #64748b;">
    <p>📦 <strong>GRN Parser Pro+</strong> - Streamline your goods receipt processing workflow</p>
    <p style="font-size: 0.9rem; opacity: 0.8;">
        Built with ❤️ using Streamlit • Enhanced PDF processing • Google Drive integration
    </p>
</div>
""", unsafe_allow_html=True)
