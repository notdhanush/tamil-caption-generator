import streamlit as st
import json
import tempfile
import os
from google.cloud import speech
import google.generativeai as genai

# Set page config
st.set_page_config(
    page_title="Tamil Caption Generator",
    page_icon="🎯",
    layout="wide"
)

# Setup Google Cloud credentials from Streamlit secrets
def setup_google_credentials():
    try:
        # Get credentials from Streamlit secrets
        credentials_info = st.secrets["google_credentials_json"]
        credentials_dict = json.loads(credentials_info)
        
        # Create temporary file for credentials
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(credentials_dict, f)
            credentials_path = f.name
        
        # Set environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        return True
    except Exception as e:
        st.error(f"Error setting up Google credentials: {str(e)}")
        return False

# Setup Gemini API
def setup_gemini():
    try:
        genai.configure(api_key=st.secrets["gemini_api_key"])
        return True
    except Exception as e:
        st.error(f"Error setting up Gemini API: {str(e)}")
        return False

# Main app
def main():
    st.title("🎯 Tamil Caption Generator")
    
    # Check if credentials are properly set
    if "google_credentials_json" not in st.secrets or "gemini_api_key" not in st.secrets:
        st.error("⚠️ API credentials not found in Streamlit secrets. Please add them in the Manage App settings.")
        st.info("Go to Manage App → Secrets to add your Google Cloud and Gemini API keys.")
        return
    
    # Setup APIs
    google_setup = setup_google_credentials()
    gemini_setup = setup_gemini()
    
    if not google_setup or not gemini_setup:
        st.error("Failed to setup API credentials. Check your secrets configuration.")
        return
    
    st.success("✅ APIs configured successfully!")
    st.info("Upload an audio file to generate Tamil captions.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an audio file", 
        type=['wav', 'mp3', 'm4a', 'ogg']
    )
    
    if uploaded_file is not None:
        st.audio(uploaded_file)
        
        if st.button("Generate Captions"):
            with st.spinner("Processing audio..."):
                st.info("Audio processing feature will be implemented here!")
                # Add your audio processing logic here

if __name__ == "__main__":
    main()
