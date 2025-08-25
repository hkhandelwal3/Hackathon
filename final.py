# ndmo_streamlit_app.py
import streamlit as st
import pandas as pd
import json
import random
from io import BytesIO
from datetime import datetime
from google.cloud import storage, bigquery
import vertexai
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any
import re
from difflib import get_close_matches

# --- Constants ---
GCP_PROJECT_ID = "nse-gcp-ema-tt-beb55-sbx-1"
GCP_LOCATION = "us-central1"
GCP_BUCKET_NAME = "ndmo-data"
BQ_TABLE_ID = f"{GCP_PROJECT_ID}.falcons_dataset.data_requests"

# Fixed requester ID (replace with your own default as needed)
DEFAULT_REQUESTER_ID = 123456

# --- Initialize Clients ---
bq_client = bigquery.Client(project=GCP_PROJECT_ID)
storage_client = storage.Client(project=GCP_PROJECT_ID)
vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)

# --- Functions ---

def detect_category(user_input):
    categories = ["bank", "smart city", "hospital"]
    user_input_lower = user_input.lower()
    for category in categories:
        if category in user_input_lower:
            return category
    matches = get_close_matches(user_input_lower, categories, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    return None

class ClassificationOutput(BaseModel):
    classification: str
    impact_category: str
    impact_level: str
    excluded_columns: List[str]
    justification: str
    ndmo_reference: str
    safe_dataset: List[Dict[str, Any]]

def fetch_data_from_gcs(category):
    file_map = {
        "bank": "Bank",
        "smart city": "SmartCity",
        "hospital": "Hospital",
    }
    filename = file_map.get(category.lower())
    if not filename:
        return None, "Invalid category"
    try:
        bucket = storage_client.bucket(GCP_BUCKET_NAME)
        blob = bucket.blob(filename)
        data_bytes = blob.download_as_bytes()
        df = pd.read_csv(BytesIO(data_bytes))
        return df, "Success"
    except Exception as e:
        return None, f"Error fetching data: {e}"

def classify_ndmo_data(file_text: str):
    client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="global")
    model = "gemini-2.5-flash"
    tools = [
        types.Tool(
            retrieval=types.Retrieval(
                vertex_rag_store=types.VertexRagStore(
                    rag_resources=[
                        types.VertexRagStoreRagResource(
                            rag_corpus="projects/997601944772/locations/us-central1/ragCorpora/4611686018427387904"
                        )
                    ]
                )
            )
        )
    ]
    prompt = f"""
    Assume you are a data classifier. Classify the data based on NDMO policy.
    Return JSON with:
    {{
      "classification": "<Level>",
      "impact_category": "<Category>",
      "impact_level": "<High/Medium/Low/None>",
      "excluded_columns": ["<Column1>", ...],
      "justification": "<Why>",
      "ndmo_reference": "<Policy section>",
      "safe_dataset": [{{ "column1": "value", ... }}]
    }}
    entity data: {file_text}
    """
    config = types.GenerateContentConfig(
        system_instruction=[prompt],
        tools=tools,
        response_json_schema=ClassificationOutput.model_json_schema(),
        response_mime_type="application/json"
    )
    response = client.models.generate_content(
        model=model,
        config=config,
        contents=["Analyze the provided data and generate the classification report."]
    )
    try:
        return ClassificationOutput.model_validate_json(response.text)
    except ValidationError as e:
        st.error(f"Validation failed:\n{e}")
        st.json(response.text)
        return None

def log_request_to_bigquery(request_id, requester, classification, justification):
    MAX_LENGTH = 255
    now = datetime.utcnow()
    now_iso = now.isoformat()
    row = {
        "request_id": int(request_id),
        "requester": int(requester),
        "classification": str(classification)[:MAX_LENGTH],
        "request_time": now_iso,
        "decision_time": now_iso,
        "decision": str(justification)[:MAX_LENGTH],
        "requested_data": str(category)[:MAX_LENGTH]
    }
    errors = bq_client.insert_rows_json(BQ_TABLE_ID, [row])
    if errors == []:
        st.success("")
    else:
        st.error(f"❌ Error logging to BigQuery: {errors}")

# Optional: Test insert function to verify schema and permissions
def test_bigquery_insert():
    now_iso = datetime.utcnow().isoformat()
    test_row = {
        "request_id": 99999999,
        "requester": DEFAULT_REQUESTER_ID,
        "classification": "Test",
        "request_time": now_iso,
        "decision_time": now_iso,
        "decision": "Test decision"
    }
    st.write("Running test insert row:", test_row)
    errors = bq_client.insert_rows_json(BQ_TABLE_ID, [test_row])
    if errors:
        st.error(f"Error inserting test row: {errors}")
    else:
        st.success("Test row inserted successfully!")

# --- Streamlit App ---

st.set_page_config(
    page_title="NDMO Smart Data Request & Classification Portal",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main > div .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "request_history" not in st.session_state:
    st.session_state.request_history = []

st.markdown(
    """
    <h1 style="text-align:center; color:#003366; font-weight:bold;">NDMO Smart Data Request & Classification Portal</h1>
    <p style="text-align:center; color:#555; font-size:18px;">
    Easily query NDMO datasets, classify data access requests with AI-powered compliance checks, and view your request history.
    </p>
    <hr>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "🔍 Navigate",
    options=["Query NDMO Data", "Request History"],
    index=0,
)

if page == "Query NDMO Data":
    st.subheader("🗂️ Query NDMO Data")

    user_input = st.text_input(
        "Enter your query below:",
        placeholder='e.g. "Get Smart City data"',
        max_chars=100,
    )
    send_query = st.button("🚀 Send Query")

    if send_query:
        if not user_input.strip():
            st.warning("⚠️ Please enter a valid query.")
        else:
            st.write(f"**User Query:** {user_input}")
            category = detect_category(user_input)
            if not category:
                st.error("❌ Could not determine the data category from your query. Try mentioning 'bank', 'smart city', or 'hospital'.")
            else:
                request_id = random.randint(10000000, 99999999)
                df, status = fetch_data_from_gcs(category)

                if df is not None and not df.empty:
                    with st.spinner("📦 Fetching and classifying data..."):
                        file_text = df.to_json(orient="records")
                        result = classify_ndmo_data(file_text)

                    if result:
                        st.success("✅ Classification Complete!")

                        metadata = result.model_dump(exclude={'safe_dataset'})
                        st.markdown("### 📊 Classification Metadata")
                        st.json(metadata)

                        safe_df = pd.DataFrame(result.safe_dataset)
                        st.markdown("### 🔐 Safe Dataset Preview")
                        st.dataframe(safe_df.head(), height=300)

                        # ✅ New: Download full safe dataset
                        csv = safe_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Full Safe Dataset",
                            data=csv,
                            file_name=f"safe_dataset_{request_id}.csv",
                            mime="text/csv"
                        )

                        log_request_to_bigquery(
                            request_id=request_id,
                            requester=DEFAULT_REQUESTER_ID,
                            classification=result.classification,
                            justification=result.justification
                        )

                        st.markdown("---")
                        st.markdown("### 📋 Request Summary")
                        st.write(f"**Request ID:** `{request_id}`")
                        st.write(f"**Requester ID:** {DEFAULT_REQUESTER_ID}")
                        st.write(f"**Category:** {category.title()}")
                        st.write(f"**Classification:** {result.classification}")
                        st.write(f"**Justification:** {result.justification}")

                        st.session_state.request_history.append(
                            {
                                "request_id": request_id,
                                "requester": DEFAULT_REQUESTER_ID,
                                "category": category,
                                "classification": result.classification,
                                "justification": result.justification,
                                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                            }
                        )
                    else:
                        st.error("❌ Classification failed. Please try again.")
                else:
                    st.error(f"❌ Failed to fetch data: {status}")

elif page == "Request History":
    st.subheader("📜 Request History")

    if st.session_state.request_history:
        df_history = pd.DataFrame(st.session_state.request_history)
        df_history["timestamp"] = pd.to_datetime(df_history["timestamp"])
        df_history = df_history.sort_values(by="timestamp", ascending=False)

        st.dataframe(
            df_history[["request_id", "requester", "category", "classification", "justification", "timestamp"]],
            use_container_width=True,
            height=400,
        )
    else:
        st.info("No requests made yet. Your query history will appear here.")