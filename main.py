import streamlit as st
from google.cloud import speech
from google.oauth2 import service_account
import google.generativeai as genai
import json
from pydub import AudioSegment
import io
from datetime import timedelta
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="Tamil Caption Generator",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .results-box {
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #28A745;
        background: #F8FFF8;
        margin-top: 1rem;
    }
    .error-box {
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #DC3545;
        background: #FFF8F8;
        margin-top: 1rem;
    }
    .translation-box {
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #007BFF;
        background: #F8F9FF;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Enhanced Authentication with Better Error Handling ---
def load_credentials():
    """Load and validate Google Cloud credentials with comprehensive error handling."""
    try:
        # Method 1: Try loading from secrets as JSON string
        if "google_credentials_json" in st.secrets:
            creds_json = st.secrets["google_credentials_json"]
            
            # Handle if it's already a string or needs conversion
            if isinstance(creds_json, str):
                creds_dict = json.loads(creds_json)
            else:
                creds_dict = dict(creds_json)
            
            # Validate required fields
            required_fields = ["type", "project_id", "private_key_id", "private_key", 
                             "client_email", "client_id", "auth_uri", "token_uri"]
            missing_fields = [field for field in required_fields if field not in creds_dict]
            
            if missing_fields:
                return None, f"Missing required fields in credentials: {missing_fields}"
            
            # Validate private key format
            private_key = creds_dict.get("private_key", "")
            if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
                return None, "Private key format is invalid. It should start with '-----BEGIN PRIVATE KEY-----'"
            
            if not private_key.endswith("-----END PRIVATE KEY-----\n"):
                # Try to fix common formatting issues
                if not private_key.endswith("-----END PRIVATE KEY-----"):
                    creds_dict["private_key"] = private_key + "\n-----END PRIVATE KEY-----\n"
                elif not private_key.endswith("\n"):
                    creds_dict["private_key"] = private_key + "\n"
            
            # Create credentials
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            return credentials, "Success"
            
        # Method 2: Try loading individual components
        elif all(key in st.secrets for key in ["project_id", "private_key", "client_email"]):
            creds_dict = {
                "type": "service_account",
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets.get("private_key_id", ""),
                "private_key": st.secrets["private_key"],
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets.get("client_id", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
            
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            return credentials, "Success"
            
        else:
            return None, "No Google Cloud credentials found in secrets"
            
    except json.JSONDecodeError as e:
        return None, f"JSON parsing error: {str(e)}. Check if your credentials JSON is properly formatted."
    except ValueError as e:
        return None, f"Credential validation error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error loading credentials: {str(e)}"

# Load credentials with enhanced error handling
credentials, auth_message = load_credentials()
auth_success = credentials is not None

# Initialize clients only if authentication succeeds
if auth_success:
    try:
        speech_client = speech.SpeechClient(credentials=credentials)
        # Configure Gemini API Key
        if "gemini_api_key" in st.secrets:
            genai.configure(api_key=st.secrets["gemini_api_key"])
            # Use the updated model name
            generative_model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            auth_success = False
            auth_message = "Gemini API key not found in secrets"
    except Exception as e:
        auth_success = False
        auth_message = f"Error initializing clients: {str(e)}"

# --- Translation Functions ---
def translate_to_tanglish(text):
    """Convert Tamil text to Tanglish"""
    prompt = f"""
    Convert this Tamil text to Tanglish (Tamil written in phonetic English letters).
    Keep any existing English words as they are.
    Make it natural and readable for Tamil speakers who prefer English script.
    Text: "{text}"
    
    Return only the Tanglish translation, nothing else.
    """
    try:
        response = generative_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Translation Error: {e}"

def translate_to_english(text):
    """Translate Tamil text to English"""
    prompt = f"""
    Translate this Tamil text accurately to natural-sounding English.
    Maintain the meaning and context.
    Text: "{text}"
    
    Return only the English translation, nothing else.
    """
    try:
        response = generative_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Translation Error: {e}"

def translate_tanglish_to_tamil(tanglish_text):
    """Convert Tanglish back to Tamil"""
    prompt = f"""
    Convert this Tanglish (Tamil written in English letters) back to proper Tamil script.
    Text: "{tanglish_text}"
    
    Return only the Tamil text, nothing else.
    """
    try:
        response = generative_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Translation Error: {e}"

def translate_tanglish_to_english(tanglish_text):
    """Translate Tanglish to English"""
    prompt = f"""
    Translate this Tanglish (Tamil written in English letters) to natural English.
    Text: "{tanglish_text}"
    
    Return only the English translation, nothing else.
    """
    try:
        response = generative_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Translation Error: {e}"

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.info("This app uses Google Cloud and Gemini AI. Ensure your API keys are set in Streamlit's Secrets Manager.")

    if not auth_success:
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.error("🚨 Authentication Failed!")
        st.write(f"**Error:** {auth_message}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.subheader("📋 Setup Instructions")
        st.write("Add your credentials to Streamlit Secrets. You have two options:")
        
        st.write("**Option 1: Complete JSON (Recommended)**")
        st.code('''
# secrets.toml
google_credentials_json = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nYour-Private-Key-Here\\n-----END PRIVATE KEY-----\\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
"""

gemini_api_key = "your-gemini-api-key"
        ''')
        
        st.write("**Option 2: Individual Fields**")
        st.code('''
# secrets.toml
project_id = "your-project-id"
private_key = "-----BEGIN PRIVATE KEY-----\\nYour-Private-Key-Here\\n-----END PRIVATE KEY-----\\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
gemini_api_key = "your-gemini-api-key"
        ''')
        
        st.warning("⚠️ **Common Issues:**")
        st.write("• Ensure private key includes newlines (\\n)")
        st.write("• Private key must start with `-----BEGIN PRIVATE KEY-----`")
        st.write("• Private key must end with `-----END PRIVATE KEY-----`")
        st.write("• Check for any missing commas or quotes in JSON")
        st.write("• Verify all required fields are present")
        
    else:
        st.success("✅ Authentication Successful!")

    st.subheader("🗣️ Language Settings")
    primary_language = st.selectbox(
        "Primary Transcription Language",
        ["ta-IN", "en-IN", "hi-IN"],
        help="The main language spoken in the audio."
    )
    secondary_language = st.selectbox(
        "Secondary Language",
        ["en-IN", "ta-IN", "hi-IN"],
        help="A fallback language if needed."
    )

# --- Initialize Session State ---
if 'original_transcript' not in st.session_state:
    st.session_state.original_transcript = ""
if 'tanglish_transcript' not in st.session_state:
    st.session_state.tanglish_transcript = ""
if 'tamil_transcript' not in st.session_state:
    st.session_state.tamil_transcript = ""
if 'english_transcript' not in st.session_state:
    st.session_state.english_transcript = ""
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = []
if 'processing_translations' not in st.session_state:
    st.session_state.processing_translations = False

# --- Main App UI ---
st.markdown("""
<div class="main-header">
    <h1>🗣️ Tamil + Tanglish Caption Generator</h1>
    <p>Upload audio → Get captions → Edit in Tanglish → Download in any language</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.header("📤 Upload & Transcribe")
    uploaded_file = st.file_uploader(
        "Choose your audio file",
        type=["wav", "mp3", "flac", "m4a", "ogg"],
        help="Supports most common audio formats"
    )

    if uploaded_file and auth_success:
        st.audio(uploaded_file)
        
        if st.button("🧠 Transcribe Audio", type="primary", use_container_width=True):
            with st.spinner("Processing audio and transcribing..."):
                try:
                    # 1. Process Audio with pydub
                    audio_segment = AudioSegment.from_file(uploaded_file)
                    # Standardize for Google API: 16kHz, mono
                    audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)

                    # Export to a format Google likes (FLAC) in memory
                    buffer = io.BytesIO()
                    audio_segment.export(buffer, format="flac")
                    content = buffer.getvalue()
                    
                    # 2. Configure & Call Google Speech-to-Text API
                    recognition_audio = speech.RecognitionAudio(content=content)
                    config = speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
                        sample_rate_hertz=16000,
                        language_code=primary_language,
                        alternative_language_codes=[secondary_language],
                        enable_automatic_punctuation=True,
                        enable_word_time_offsets=True,
                        model="latest_long"
                    )

                    response = speech_client.recognize(config=config, audio=recognition_audio)
                    
                    if not response.results:
                        st.warning("Could not transcribe the audio. The file might be silent or the language settings incorrect.")
                        st.stop()
                    
                    # 3. Process and store results
                    full_transcript = ""
                    timestamps_data = []
                    for result in response.results:
                        full_transcript += result.alternatives[0].transcript + " "
                        for word_info in result.alternatives[0].words:
                            timestamps_data.append({
                                'word': word_info.word,
                                'start_time': word_info.start_time.total_seconds(),
                                'end_time': word_info.end_time.total_seconds()
                            })
                    
                    st.session_state.original_transcript = full_transcript.strip()
                    st.session_state.timestamps = timestamps_data
                    st.session_state.processing_translations = True
                    
                    st.success("✅ Transcription complete! Generating translations...")
                    st.rerun()

                except Exception as e:
                    st.error(f"An error occurred during transcription: {e}")
    elif not auth_success:
        st.warning("Please configure your API keys in the sidebar to begin.")

with col2:
    st.header("📝 Edit in Tanglish")

    # Auto-generate translations after transcription
    if st.session_state.processing_translations and st.session_state.original_transcript:
        with st.spinner("Generating translations..."):
            # Generate Tanglish version for editing
            st.session_state.tanglish_transcript = translate_to_tanglish(st.session_state.original_transcript)
            st.session_state.processing_translations = False
            st.rerun()

    if st.session_state.tanglish_transcript:
        st.subheader("✏️ Edit Transcript (Tanglish)")
        st.info("💡 Edit in Tanglish for easier understanding. Tamil and English versions will be updated automatically when you download.")
        
        edited_tanglish = st.text_area(
            "Make corrections in Tanglish:",
            value=st.session_state.tanglish_transcript,
            height=200,
            help="Edit in Tanglish (Tamil written in English letters) for easier editing"
        )
        
        # Update session state when text is changed
        if edited_tanglish != st.session_state.tanglish_transcript:
            st.session_state.tanglish_transcript = edited_tanglish
        
        # Show preview of original Tamil
        if st.session_state.original_transcript:
            with st.expander("📖 View Original Tamil Transcript"):
                st.write(st.session_state.original_transcript)

# --- Export Section ---
if st.session_state.tanglish_transcript:
    st.markdown("---")
    st.header("📥 Export Options")
    
    # Language selection for export
    col_lang, col_format = st.columns([1, 1])
    
    with col_lang:
        export_language = st.selectbox(
            "🌍 Select Language for Download:",
            ["Tanglish", "Tamil", "English"],
            help="Choose which language version to download"
        )
    
    with col_format:
        export_format = st.selectbox(
            "📄 Select Format:",
            ["TXT", "SRT"],
            help="Choose file format"
        )

    # Helper function to create SRT content
    def create_srt(text, timestamps):
        def format_time(seconds):
            td = timedelta(seconds=seconds)
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            millis = td.microseconds // 1000
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

        # Split text into words for timing
        text_words = text.split()
        srt_content = ""
        chunk_size = 8  # Words per subtitle line
        
        # Map text words to timestamps (approximate)
        for i in range(0, len(text_words), chunk_size):
            chunk_words = text_words[i : i + chunk_size]
            if not chunk_words:
                continue
            
            # Use timestamp mapping (approximate)
            timestamp_start_idx = min(i, len(timestamps) - 1)
            timestamp_end_idx = min(i + chunk_size - 1, len(timestamps) - 1)
            
            if timestamp_start_idx < len(timestamps) and timestamp_end_idx < len(timestamps):
                start_time = timestamps[timestamp_start_idx]['start_time']
                end_time = timestamps[timestamp_end_idx]['end_time']
            else:
                # Fallback timing
                start_time = i * 2  # 2 seconds per chunk
                end_time = (i + chunk_size) * 2
            
            text_chunk = " ".join(chunk_words)
            
            subtitle_num = (i // chunk_size) + 1
            srt_content += f"{subtitle_num}\n"
            srt_content += f"{format_time(start_time)} --> {format_time(end_time)}\n"
            srt_content += f"{text_chunk}\n\n"
        
        return srt_content

    # Export buttons
    if st.button("📥 Generate & Download", type="primary", use_container_width=True):
        with st.spinner(f"Generating {export_language} version..."):
            try:
                # Get the text in selected language
                if export_language == "Tanglish":
                    export_text = st.session_state.tanglish_transcript
                elif export_language == "Tamil":
                    # Generate Tamil from current Tanglish
                    export_text = translate_tanglish_to_tamil(st.session_state.tanglish_transcript)
                else:  # English
                    # Generate English from current Tanglish
                    export_text = translate_tanglish_to_english(st.session_state.tanglish_transcript)
                
                # Generate download based on format
                if export_format == "TXT":
                    file_extension = "txt"
                    file_data = export_text
                    mime_type = "text/plain"
                else:  # SRT
                    file_extension = "srt"
                    file_data = create_srt(export_text, st.session_state.timestamps)
                    mime_type = "text/plain"
                
                # Create filename
                filename = f"transcript_{export_language.lower()}.{file_extension}"
                
                # Show download button
                st.download_button(
                    label=f"📥 Download {export_language} {export_format}",
                    data=file_data,
                    file_name=filename,
                    mime=mime_type,
                    use_container_width=True,
                )
                
                # Show preview
                st.subheader(f"📄 Preview ({export_language} {export_format})")
                if export_format == "SRT":
                    st.code(file_data[:500] + "..." if len(file_data) > 500 else file_data)
                else:
                    st.write(export_text[:300] + "..." if len(export_text) > 300 else export_text)
                
            except Exception as e:
                st.error(f"Error generating {export_language} version: {e}")

    # Quick download buttons for all formats
    st.subheader("🚀 Quick Downloads")
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        if st.button("📄 Tanglish TXT", use_container_width=True):
            st.download_button(
                label="Download Tanglish TXT",
                data=st.session_state.tanglish_transcript,
                file_name="transcript_tanglish.txt",
                mime="text/plain",
            )
    
    with quick_col2:
        if st.button("🎬 Tanglish SRT", use_container_width=True):
            srt_data = create_srt(st.session_state.tanglish_transcript, st.session_state.timestamps)
            st.download_button(
                label="Download Tanglish SRT",
                data=srt_data,
                file_name="subtitles_tanglish.srt",
                mime="text/plain",
            )
    
    with quick_col3:
        st.info("Use 'Generate & Download' above for Tamil and English versions")

    # Show all versions preview
    if st.checkbox("🔍 Show All Language Previews"):
        st.subheader("📖 Language Previews")
        
        tab1, tab2, tab3 = st.tabs(["🔤 Tanglish", "🕉️ Tamil", "🌍 English"])
        
        with tab1:
            st.write("**Current Tanglish Version:**")
            st.write(st.session_state.tanglish_transcript)
        
        with tab2:
            if st.button("Generate Tamil Preview"):
                with st.spinner("Translating to Tamil..."):
                    tamil_preview = translate_tanglish_to_tamil(st.session_state.tanglish_transcript)
                    st.write("**Tamil Version:**")
                    st.write(tamil_preview)
        
        with tab3:
            if st.button("Generate English Preview"):
                with st.spinner("Translating to English..."):
                    english_preview = translate_tanglish_to_english(st.session_state.tanglish_transcript)
                    st.write("**English Version:**")
                    st.write(english_preview)
