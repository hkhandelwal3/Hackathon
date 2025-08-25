import os
import streamlit as st
import random
import pandas as pd
import uuid
from google.cloud import storage, bigquery
from io import BytesIO
import vertexai
from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
from datetime import datetime
import json

# Service account paths
VERTEX_AI_CREDENTIALS = r"C:\\Users\\hkhandelwal3\\OneDrive - Deloitte (O365D)\\Desktop\\NDMO\\nse-gcp-ema-tt-beb55-sbx-1-b1166898ac8d.json"
GCS_CREDENTIALS = r"C:\\Users\\hkhandelwal3\\OneDrive - Deloitte (O365D)\\Desktop\\NDMO\\nse-gcp-ema-tt-beb55-sbx-1-6196b2b0dfed.json"
BIGQUERY_CREDENTIALS = r"C:\\Users\\hkhandelwal3\\OneDrive - Deloitte (O365D)\\Desktop\\NDMO\\nse-gcp-ema-tt-beb55-sbx-1-2e76e78d0648.json"

# GCP bucket and project info
GCP_BUCKET_NAME = "ndmo-data"
GCP_PROJECT_ID = "nse-gcp-ema-tt-beb55-sbx-1"
GCP_LOCATION = "us-central1"
BQ_TABLE_ID = "nse-gcp-ema-tt-beb55-sbx-1.falcons_dataset.data_requests"

# Set credentials for BigQuery
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = BIGQUERY_CREDENTIALS
bq_client = bigquery.Client()

@st.cache_resource
def get_storage_client():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCS_CREDENTIALS
    return storage.Client()

def fetch_data_from_gcs(category):
    client = get_storage_client()
    file_map = {
        "bank": "Bank",
        "smart city": "SmartCity",
        "hospital": "Hospital",
    }
    filename = file_map.get(category.lower())
    if not filename:
        return None, "Invalid category"
    try:
        bucket = client.bucket(GCP_BUCKET_NAME)
        blob = bucket.blob(filename)
        data_bytes = blob.download_as_bytes()
        df = pd.read_csv(BytesIO(data_bytes))
        return df, "Success"
    except Exception as e:
        return None, f"Error fetching data: {e}"

def parse_with_gemini(user_text):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = VERTEX_AI_CREDENTIALS
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
    model = GenerativeModel("gemini-2.5-pro")

    prompt = f"Extract the data category from this query: '{user_text}'"

    generation_config = GenerationConfig(
        response_mime_type="application/json",
        response_schema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["bank", "smart city", "hospital"]
                }
            },
            "required": ["category"]
        }
    )

    try:
        response = model.generate_content(prompt, generation_config=generation_config)
        json_response = response.candidates[0].content.parts[0].text
        parsed = json.loads(json_response)
        return parsed.get("category")
    except Exception:
        return None

# Page config and styling
st.set_page_config(page_title="NDMO Chatbot", layout="centered")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        background-color: #f5f5dc !important;
        font-family: 'Segoe UI', sans-serif;
        color: #333333;
    }
    .main-title {
        font-size: 36px;
        font-weight: 600;
        text-align: center;
        margin-top: 30px;
        margin-bottom: 10px;
    }
    .subtitle {
        font-size: 18px;
        text-align: center;
        color: #555555;
        margin-bottom: 40px;
    }
    .status-table table {
        width: 100%;
        border-collapse: collapse;
    }
    .status-table th, .status-table td {
        border: 1px solid #ccc;
        padding: 12px;
        text-align: left;
    }
    .status-table th {
        background-color: #eae6d5;
        font-weight: 600;
    }
    .status-table td {
        background-color: #ffffff;
    }

    /* Added CSS for history table */
    .history-table table {
        width: 100% !important;
        table-layout: fixed;
        border-collapse: collapse;
    }
    .history-table th, .history-table td {
        border: 1px solid #ccc;
        padding: 12px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        vertical-align: middle;
    }
    .history-table th {
        background-color: #eae6d5;
        font-weight: 600;
        text-align: left;
    }
    .history-table td {
        background-color: #ffffff;
    }
    .history-table th:nth-child(1), .history-table td:nth-child(1) {
        width: 15%;
    }
    .history-table th:nth-child(2), .history-table td:nth-child(2) {
        width: 30%;
    }
    .history-table th:nth-child(3), .history-table td:nth-child(3) {
        width: 20%;
    }
    .history-table th:nth-child(4), .history-table td:nth-child(4) {
        width: 35%;
    }
    </style>
""", unsafe_allow_html=True)

if "request_history" not in st.session_state:
    st.session_state.request_history = []

tab1, tab2 = st.tabs(["📊 Data Chatbot", "📄 My Request History"])

with tab1:
    st.markdown('<div class="main-title">NDMO Compliant Data Chatbot</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Ask for classified NDMO-compliant data from trusted domains.</div>', unsafe_allow_html=True)

    user_input = st.text_input("You:", placeholder="Ask for NDMO data like 'Get Smart City data'")

    if st.button("Send") and user_input.strip():
        category = parse_with_gemini(user_input)
        ticket_id = random.randint(10000000, 99999999)
        status_message = "⏳ In Progress"

        if category:
            df, fetch_status = fetch_data_from_gcs(category)
            if df is not None and not df.empty:
                status_message = "✅ Approved"
                st.success(f"✅ Data successfully fetched for {category}")
                st.dataframe(df)
            else:
                status_message = f"❌ Failed to fetch data: {fetch_status}"
                st.error(status_message)
        else:
            status_message = "❌ Could not identify category"
            st.warning("Could not identify a valid data category from your message.")

        # Save to session history
        st.session_state.request_history.append([
            ticket_id,
            category if category else "Unknown",
            "Not specified",
            status_message
        ])

        # Save to BigQuery with NULLs where needed
        row = {
            "request_id": ticket_id,
            "requester": None,  # NULL to avoid type mismatch
            "classification": "Confidential" if category else None,
            "request_time": datetime.now().isoformat(),
            "decision_time": datetime.now().isoformat(),
            "decision": status_message.replace("✅ ", "").replace("❌ ", "").replace("⏳ ", "")
        }

        try:
            errors = bq_client.insert_rows_json(BQ_TABLE_ID, [row])
            if errors == []:
                st.success("✅ Request logged in BigQuery.")
            else:
                st.error(f"❌ Error logging request: {errors}")
        except Exception as e:
            st.error(f"❌ BigQuery insertion failed: {e}")

        # Display status
        status_df = pd.DataFrame({
            "Process": ["Ticket ID", "Request Sent", "Data Retrieval"],
            "Status": [
                ticket_id,
                f"✅ Sent for {category}" if category else "Invalid request",
                status_message
            ]
        })

        st.markdown('<div class="status-table">', unsafe_allow_html=True)
        st.table(status_df)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="main-title">My Request History</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Previously made requests during this session.</div>', unsafe_allow_html=True)

    if st.session_state.request_history:
        history_df = pd.DataFrame(
            st.session_state.request_history,
            columns=["Ticket ID", "Data Requested", "Year Range", "Status"]
        )
        st.markdown('<div class="history-table">', unsafe_allow_html=True)
        st.table(history_df)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No requests made yet.")
