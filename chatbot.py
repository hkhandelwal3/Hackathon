import os
import streamlit as st
from google import genai
from google.genai.types import HttpOptions, Content, Part

# Set your service account key JSON path here:
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\hkhandelwal3\OneDrive - Deloitte (O365D)\Desktop\NDMO\nse-gcp-ema-tt-beb55-sbx-1-b1166898ac8d.json"

# Initialize GenAI client with Vertex AI config
@st.cache_resource
def load_client():
    return genai.Client(
        vertexai=True,
        project="nse-gcp-ema-tt-beb55-sbx-1",
        location="us-central1",
        http_options=HttpOptions(api_version="v1")
    )

def main():
    st.title("Gemini 2.5 Pro Chatbot")

    client = load_client()
    model_name = "gemini-2.5-pro"

    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    user_input = st.text_input("You:", placeholder="Ask me anything!")

    if st.button("Send") and user_input.strip():
        st.session_state.conversation.append(
            Content(role="user", parts=[Part(text=user_input)])
        )

        with st.spinner("Thinking..."):
            response = client.models.generate_content(
                model=model_name,
                contents=st.session_state.conversation
            )
            ai_text = response.text
            st.session_state.conversation.append(
                Content(role="model", parts=[Part(text=ai_text)])
            )

        st.rerun()  # Updated from experimental_rerun

    if st.session_state.conversation:
        for turn in st.session_state.conversation:
            if turn.role == "user":
                st.markdown(f"**You:** {turn.parts[0].text}")
            elif turn.role == "model":
                st.markdown(f"**AI:** {turn.parts[0].text}")
            st.markdown("---")

if __name__ == "__main__":
    main()
