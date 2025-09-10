#!/usr/bin/env python3
"""
Enhanced Reliance GRN Parser with Google Drive Integration and Google Sheets Output
Separate workflows for Manual Upload and Google Drive processing with hardcoded config
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

.workflow-section {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 2.5rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    border: 2px solid rgba(102, 126, 234, 0.2);
    margin-bottom: 2rem;
    border-left: 6px solid #667eea;
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

/* Section Headers */
.section-header {
    font-size: 2rem;
    font-weight: 600;
    color: #667eea;
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #667eea;
    display: flex;
    align-items: center;
    gap: 1rem;
}

.section-icon {
    font-size: 2.5rem;
}

/* Buttons */
.primary-btn {
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

.primary-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    background: linear-gradient(135deg, #5a67d8 0%, #6b5b95 100%);
}

.drive-btn {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
}

.drive-btn:hover {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4) !important;
}

/* Status indicators */
.status-success {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-weight: 500;
    display: inline-block;
    margin: 0.5rem 0;
}

.status-warning {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-weight: 500;
    display: inline-block;
    margin: 0.5rem 0;
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

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# Hardcoded Configuration based on the image
HARDCODED_CONFIG = {
    'mail_to_drive': {
        'folder_id': '1h1yU576532RpLNeVo_gIHEeu92gI0-K3',
        'sender': 'DONOTREPLY@ril.com',
        'search_term': 'GRN',
        'days_back': 7,
        'max_result': 1000
    },
    'drive_to_sheet': {
        'folder_id': '1oJsbr8Uq8BahFDUSUM98KMMu8pXRc5I5',
        'sheet_id': '1AD2yYIzeHID0ND3mRTsFZ1LmSjgEX_Prt2uO69biLg0',
        'days_back': 7,
        'max_result': 1000
    }
}

class RelianceGRNProcessor:
    def __init__(self):
        self.drive_service = None
        self.sheets_service = None
        self.scopes = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
    
    def authenticate_from_secrets(self, progress_bar, status_text):
        """Authenticate using Streamlit secrets with web-based OAuth flow"""
        try:
            status_text.text("Authenticating with Google Services...")
            progress_bar.progress(10)
            
            # Check for existing token in session state
            if 'oauth_token' in st.session_state:
                try:
                    creds = Credentials.from_authorized_user_info(st.session_state.oauth_token, self.scopes)
                    if creds and creds.valid:
                        progress_bar.progress(50)
                        self.drive_service = build('drive', 'v3', credentials=creds)
                        self.sheets_service = build('sheets', 'v4', credentials=creds)
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
                    scopes=self.scopes,
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
                        self.sheets_service = build('sheets', 'v4', credentials=creds)
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
                    st.markdown("### Google Services Authentication Required")
                    st.markdown(f"[Authorize with Google Services]({auth_url})")
                    st.info("Click the link above to authorize access to Google Drive and Sheets")
                    st.stop()
            else:
                st.error("Google credentials missing in Streamlit secrets.")
                return False
                
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return False
    
    def list_drive_files(self, folder_id: str, days_back: int = 7, max_files: int = 1000) -> List[Dict]:
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
            
            while len(files) < max_files:
                results = self.drive_service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, createdTime, size)",
                    pageToken=page_token,
                    orderBy="createdTime desc",
                    pageSize=min(100, max_files - len(files))
                ).execute()
                
                batch_files = results.get('files', [])
                files.extend(batch_files)
                
                page_token = results.get('nextPageToken')
                if not page_token or len(batch_files) == 0:
                    break
            
            st.info(f"Found {len(files)} PDF files in Drive folder")
            return files[:max_files]
            
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
    
    def append_to_sheet(self, sheet_id: str, data: List[Dict], progress_bar=None, status_text=None):
        """Append data to Google Sheet"""
        try:
            if not data:
                st.warning("No data to append to sheet")
                return False
            
            if status_text:
                status_text.text("Preparing data for Google Sheets...")
            if progress_bar:
                progress_bar.progress(10)
            
            # Convert data to DataFrame for easier manipulation
            df = pd.DataFrame(data)
            
            # Get existing sheet headers to match column order
            try:
                sheet_metadata = self.sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
                sheet_name = sheet_metadata['sheets'][0]['properties']['title']  # Use first sheet
                
                # Get existing headers
                header_range = f"{sheet_name}!1:1"
                header_result = self.sheets_service.spreadsheets().values().get(
                    spreadsheetId=sheet_id, range=header_range
                ).execute()
                
                existing_headers = header_result.get('values', [[]])[0] if header_result.get('values') else []
                
                if progress_bar:
                    progress_bar.progress(30)
                
            except Exception as e:
                st.warning(f"Could not read existing headers: {e}")
                existing_headers = []
                sheet_name = 'Sheet1'  # Default sheet name
            
            # Prepare data rows
            if existing_headers:
                # Reorder columns to match existing sheet
                df_ordered = pd.DataFrame()
                for header in existing_headers:
                    if header in df.columns:
                        df_ordered[header] = df[header]
                    else:
                        df_ordered[header] = ''  # Empty column for missing data
                
                # Add any new columns not in existing headers
                for col in df.columns:
                    if col not in existing_headers:
                        df_ordered[col] = df[col]
                
                df = df_ordered
            
            if status_text:
                status_text.text("Converting data to sheet format...")
            if progress_bar:
                progress_bar.progress(50)
            
            # Convert DataFrame to list of lists for Google Sheets API
            values = df.fillna('').astype(str).values.tolist()
            
            # If no existing headers, add headers as first row
            if not existing_headers:
                headers = list(df.columns)
                values.insert(0, headers)
            
            if status_text:
                status_text.text("Uploading to Google Sheets...")
            if progress_bar:
                progress_bar.progress(70)
            
            # Append data to sheet
            body = {
                'values': values
            }
            
            range_name = f"{sheet_name}!A:Z"  # Append to end of sheet
            
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            if progress_bar:
                progress_bar.progress(100)
            
            if status_text:
                status_text.text("✅ Data successfully uploaded to Google Sheets!")
            
            rows_added = result.get('updates', {}).get('updatedRows', 0)
            st.success(f"Successfully added {rows_added} rows to Google Sheets!")
            
            return True
            
        except Exception as e:
            st.error(f"Failed to append data to Google Sheets: {str(e)}")
            return False
    
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
            "Source File": source_filename, "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'sheets_uploaded' not in st.session_state:
    st.session_state.sheets_uploaded = False

# Header Section
st.markdown("""
<div class="main-header animate-fade-in">
    <h1 class="main-title">📦 GRN Parser Pro+</h1>
    <p class="main-subtitle">Transform your Goods Receipt Note PDFs into organized data with automated Google Sheets integration</p>
</div>
""", unsafe_allow_html=True)

# Configuration Display
st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
st.markdown("### ⚙️ Current Configuration")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🔧 Mail to Drive Workflow:**")
    st.code(f"""
Folder ID: {HARDCODED_CONFIG['mail_to_drive']['folder_id']}
Sender: {HARDCODED_CONFIG['mail_to_drive']['sender']}
Search Term: {HARDCODED_CONFIG['mail_to_drive']['search_term']}
Days Back: {HARDCODED_CONFIG['mail_to_drive']['days_back']}
Max Results: {HARDCODED_CONFIG['mail_to_drive']['max_result']}
    """)

with col2:
    st.markdown("**📊 Drive to Sheet Workflow:**")
    st.code(f"""
Folder ID: {HARDCODED_CONFIG['drive_to_sheet']['folder_id']}
Sheet ID: {HARDCODED_CONFIG['drive_to_sheet']['sheet_id']}
Days Back: {HARDCODED_CONFIG['drive_to_sheet']['days_back']}
Max Results: {HARDCODED_CONFIG['drive_to_sheet']['max_result']}
    """)

st.markdown('</div>', unsafe_allow_html=True)

# Create tabs for different workflows
tab1, tab2 = st.tabs(["📁 Manual Upload", "☁️ Google Drive Processing"])

# Tab 1: Manual Upload Workflow
with tab1:
    st.markdown('<div class="workflow-section animate-fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><span class="section-icon">📁</span>Manual Upload Workflow</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-zone">
        <h3 style="color: #667eea; margin-bottom: 1rem;">📄 Upload Your GRN PDFs</h3>
        <p style="color: #64748b; margin-bottom: 1.5rem;">Select multiple PDF files to process them all at once</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Choose PDF files", 
        type="pdf", 
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="manual_upload"
    )
    
    if uploaded_files:
        # File Metrics
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
        
        # Processing Section
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Process Manual PDFs", key="process_manual_btn", help="Process uploaded PDF files"):
                processor = RelianceGRNProcessor()
                with st.spinner("🔄 Processing your files..."):
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
                            row["source"] = "manual"
                            all_data.append(row)
                        else:
                            for item in items:
                                row = {**metadata, **item, "file_name": file.name, "source": "manual"}
                                all_data.append(row)
                        
                        progress_bar.progress((i + 1) / len(uploaded_files))
                        time.sleep(0.1)
                    
                    status_text.text("✅ Processing complete!")
                    
                    if all_data:
                        st.session_state.df_result = pd.DataFrame(all_data)
                        st.session_state.processing_complete = True
                        st.session_state.sheets_uploaded = False
                        st.success("🎉 All manual files processed successfully!")
                    else:
                        st.session_state.df_result = pd.DataFrame()
                        st.warning("⚠️ No data could be extracted from the uploaded files.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Tab 2: Google Drive Workflow
with tab2:
    st.markdown('<div class="workflow-section animate-fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><span class="section-icon">☁️</span>Google Drive Processing Workflow</div>', unsafe_allow_html=True)
    
    processor = RelianceGRNProcessor()
    
    # Authentication Section
    st.markdown("#### 🔐 Google Services Authentication")
    auth_progress = st.progress(0)
    auth_status = st.empty()
    
    if processor.authenticate_from_secrets(auth_progress, auth_status):
        st.markdown('<div class="status-success">🔓 Authentication successful!</div>', unsafe_allow_html=True)
        
        # List files from Drive using hardcoded config
        st.markdown("#### 📂 Files from Google Drive")
        
        config = HARDCODED_CONFIG['drive_to_sheet']
        
        with st.spinner("📋 Loading files from Google Drive..."):
            drive_files = processor.list_drive_files(
                config['folder_id'],
                config['days_back'],
                config['max_result']
            )
        
        if drive_files:
            # Drive Files Metrics
            col1, col2, col3, col4 = st.columns(4)
            
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
                oldest_file = min(drive_files, key=lambda x: x['createdTime'])['createdTime']
                oldest_date = datetime.fromisoformat(oldest_file.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                st.markdown(f"""
                <div class="metric-card">
                    <span class="metric-value" style="font-size: 1.5rem;">{oldest_date}</span>
                    <div class="metric-label">Oldest File Date</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                newest_file = max(drive_files, key=lambda x: x['createdTime'])['createdTime']
                newest_date = datetime.fromisoformat(newest_file.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                st.markdown(f"""
                <div class="metric-card">
                    <span class="metric-value" style="font-size: 1.5rem;">{newest_date}</span>
                    <div class="metric-label">Newest File Date</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display files table
            files_df = pd.DataFrame(drive_files)
            files_df['created_date'] = pd.to_datetime(files_df['createdTime']).dt.strftime('%Y-%m-%d %H:%M')
            files_df['size_mb'] = (files_df['size'].astype(int) / (1024 * 1024)).round(2)
            
            display_df = files_df[['name', 'created_date', 'size_mb']].rename(columns={
                'name': 'File Name',
                'created_date': 'Created Date',
                'size_mb': 'Size (MB)'
            })
            
            st.dataframe(display_df, use_container_width=True, height=300)
            
            # Process Drive Files
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Process Drive PDFs", key="process_drive_btn", help="Process files from Google Drive"):
                    with st.spinner("📄 Processing Drive files..."):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        all_data = []
                        
                        for i, file in enumerate(drive_files):
                            status_text.text(f"Processing: {file['name']}")
                            
                            # Download file
                            file_data = processor.download_from_drive(file['id'])
                            if file_data:
                                text = processor.extract_text_from_pdf(file_data)
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
                                        row = {**metadata, **item, 
                                               "file_name": file['name'], 
                                               "source": "drive",
                                               "drive_file_id": file['id']}
                                        all_data.append(row)
                            
                            progress_bar.progress((i + 1) / len(drive_files))
                            time.sleep(0.1)
                        
                        status_text.text("✅ Processing complete!")
                        
                        if all_data:
                            st.session_state.df_result = pd.DataFrame(all_data)
                            st.session_state.processing_complete = True
                            st.session_state.sheets_uploaded = False
                            st.success("🎉 All Drive files processed successfully!")
                        else:
                            st.session_state.df_result = pd.DataFrame()
                            st.warning("⚠️ No data could be extracted from the Drive files.")
        else:
            st.warning("📂 No PDF files found in the specified Google Drive folder.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Results Section (shown for both workflows)
if st.session_state.processing_complete and st.session_state.df_result is not None:
    st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><span class="section-icon">📊</span>Processing Results</div>', unsafe_allow_html=True)
    
    df = st.session_state.df_result
    
    if not df.empty:
        # Results Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{len(df)}</span>
                <div class="metric-label">Total Records</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            unique_grns = df['GRN No'].nunique() if 'GRN No' in df.columns else 0
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{unique_grns}</span>
                <div class="metric-label">Unique GRNs</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            unique_files = df['file_name'].nunique() if 'file_name' in df.columns else 0
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{unique_files}</span>
                <div class="metric-label">Files Processed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            success_rate = (df['GRN No'].notna().sum() / len(df) * 100) if 'GRN No' in df.columns else 0
            st.markdown(f"""
            <div class="metric-card">
                <span class="metric-value">{success_rate:.1f}%</span>
                <div class="metric-label">Success Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Data Preview
        st.markdown("#### 🔍 Data Preview")
        st.dataframe(df.head(20), use_container_width=True, height=400)
        
        # Download and Upload Options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download as CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"grn_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_csv"
            )
        
        with col2:
            # Download as Excel
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='GRN_Data', index=False)
            
            st.download_button(
                label="📊 Download Excel",
                data=buffer.getvalue(),
                file_name=f"grn_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )
        
        with col3:
            # Upload to Google Sheets
            if not st.session_state.sheets_uploaded:
                if st.button("📋 Upload to Google Sheets", key="upload_sheets_btn"):
                    processor = RelianceGRNProcessor()
                    
                    # Re-authenticate if needed
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    if processor.authenticate_from_secrets(progress_bar, status_text):
                        # Convert DataFrame to list of dictionaries
                        data_list = df.to_dict('records')
                        
                        # Upload to the hardcoded sheet
                        sheet_id = HARDCODED_CONFIG['drive_to_sheet']['sheet_id']
                        
                        if processor.append_to_sheet(sheet_id, data_list, progress_bar, status_text):
                            st.session_state.sheets_uploaded = True
                            st.rerun()
                    else:
                        st.error("❌ Authentication failed. Cannot upload to Google Sheets.")
            else:
                st.markdown('<div class="status-success">✅ Data uploaded to Google Sheets!</div>', unsafe_allow_html=True)
    
    else:
        st.warning("⚠️ No data was extracted from the processed files.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer Information
st.markdown("""
<div class="glass-card animate-fade-in">
    <div style="text-align: center; padding: 1rem;">
        <h4 style="color: #667eea; margin-bottom: 1rem;">📋 Processing Summary</h4>
        <p style="color: #64748b; margin-bottom: 0.5rem;">
            This application processes Reliance GRN (Goods Receipt Note) PDFs and extracts structured data including:
        </p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
            <div style="background: rgba(102, 126, 234, 0.1); padding: 0.5rem; border-radius: 8px;">
                <strong>📄 Document Info:</strong><br>GRN Number, Date, PO Details
            </div>
            <div style="background: rgba(102, 126, 234, 0.1); padding: 0.5rem; border-radius: 8px;">
                <strong>🚚 Logistics:</strong><br>Truck Number, Challan Details
            </div>
            <div style="background: rgba(102, 126, 234, 0.1); padding: 0.5rem; border-radius: 8px;">
                <strong>📦 Items:</strong><br>Article Details, Quantities, MRP
            </div>
            <div style="background: rgba(102, 126, 234, 0.1); padding: 0.5rem; border-radius: 8px;">
                <strong>🏢 Location:</strong><br>Consignee Information
            </div>
        </div>
        <p style="color: #64748b; font-size: 0.9rem; margin-top: 1rem;">
            <strong>Supported Formats:</strong> PDF files with structured GRN layouts<br>
            <strong>Output Options:</strong> CSV, Excel, Google Sheets integration
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Clear data button
if st.session_state.processing_complete:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🗑️ Clear All Data", key="clear_data_btn", help="Clear all processed data and start fresh"):
            st.session_state.df_result = None
            st.session_state.processing_complete = False
            st.session_state.sheets_uploaded = False
            st.success("✅ All data cleared successfully!")
            st.rerun()

# Debug information (only shown in development)
if st.query_params.get("debug") == "true":
    st.markdown("---")
    st.markdown("### 🔧 Debug Information")
    st.write("Session State:", st.session_state)
    st.write("Query Params:", dict(st.query_params))
