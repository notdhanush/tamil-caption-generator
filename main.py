import streamlit as st
from google.cloud import speech
from google.oauth2 import service_account
import google.generativeai as genai
import json
from pydub import AudioSegment
import io
from datetime import timedelta

# --- Page Configuration ---
# Must be the first Streamlit command in your script
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
</style>
""", unsafe_allow_html=True)

# --- Secure Authentication ---
# This block handles loading credentials safely from Streamlit's Secrets.
try:
    # Load Google Cloud credentials from Streamlit's secrets
    google_creds_json = st.secrets["google_credentials_json"]
    creds_dict = json.loads(google_creds_json)
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    speech_client = speech.SpeechClient(credentials=credentials)

    # Configure Gemini API Key
    genai.configure(api_key=st.secrets["gemini_api_key"])
    generative_model = genai.GenerativeModel("gemini-pro")
    
    auth_success = True
except (KeyError, json.JSONDecodeError):
    auth_success = False


# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.info("This app uses Google Cloud and Gemini AI. Ensure your API keys are set in Streamlit's Secrets Manager.")

    if not auth_success:
        st.error("🚨 API Keys Not Found!\n\nPlease add your Google Cloud JSON and Gemini API Key to your Streamlit Secrets.")
        st.code("""
# secrets.toml

google_credentials_json = \"\"\"
{
  "type": "service_account",
  "project_id": "your-project-id",
  ...
}
\"\"\"

gemini_api_key = "your-gemini-api-key"
        """)
    else:
        st.success("✅ API Keys Loaded Successfully!")

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
# This ensures variables persist across reruns
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'edited_transcript' not in st.session_state:
    st.session_state.edited_transcript = ""
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = []
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""

# --- Main App UI ---
st.markdown("""
<div class="main-header">
    <h1>🗣️ Tamil + Tanglish Caption Generator</h1>
    <p>Upload audio → Get captions → Edit → Translate → Export SRT</p>
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
                    
                    st.session_state.transcript = full_transcript.strip()
                    st.session_state.edited_transcript = full_transcript.strip()
                    st.session_state.timestamps = timestamps_data
                    st.session_state.translated_text = "" # Reset translation
                    
                    st.success("✅ Transcription complete!")

                except Exception as e:
                    st.error(f"An error occurred during transcription: {e}")
    elif not auth_success:
        st.warning("Please configure your API keys in the sidebar to begin.")


with col2:
    st.header("📝 Results & Editing")

    if st.session_state.transcript:
        st.subheader("✏️ Edit Transcript")
        st.session_state.edited_transcript = st.text_area(
            "Make corrections before translating:",
            value=st.session_state.edited_transcript,
            height=200
        )

        st.subheader("🌍 Translate with Gemini")
        trans_col1, trans_col2 = st.columns(2)

        with trans_col1:
            if st.button("Tamil → Tanglish", use_container_width=True):
                with st.spinner("Translating to Tanglish..."):
                    prompt = f"""
                    Convert this Tamil text to Tanglish (Tamil written in phonetic English letters).
                    Keep any existing English words as they are.
                    Text: "{st.session_state.edited_transcript}"
                    """
                    try:
                        response = generative_model.generate_content(prompt)
                        st.session_state.translated_text = response.text
                    except Exception as e:
                        st.error(f"Translation Error: {e}")

        with trans_col2:
            if st.button("Tamil → English", use_container_width=True):
                 with st.spinner("Translating to English..."):
                    prompt = f"""
                    Translate this Tamil text accurately to natural-sounding English.
                    Text: "{st.session_state.edited_transcript}"
                    """
                    try:
                        response = generative_model.generate_content(prompt)
                        st.session_state.translated_text = response.text
                    except Exception as e:
                        st.error(f"Translation Error: {e}")

        if st.session_state.translated_text:
            st.markdown('<div class="results-box">', unsafe_allow_html=True)
            st.subheader("🔄 Translation Result")
            st.write(st.session_state.translated_text)
            st.markdown('</div>', unsafe_allow_html=True)
            

# --- Export Section ---
if st.session_state.transcript:
    st.markdown("---")
    st.header("📥 Export Options")

    # Helper function to create SRT content
    def create_srt(timestamps):
        def format_time(seconds):
            td = timedelta(seconds=seconds)
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            millis = td.microseconds // 1000
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

        srt_content = ""
        chunk_size = 8  # Words per subtitle line
        for i in range(0, len(timestamps), chunk_size):
            chunk = timestamps[i : i + chunk_size]
            if not chunk:
                continue
            
            start_time = chunk[0]['start_time']
            end_time = chunk[-1]['end_time']
            text = " ".join(c['word'] for c in chunk)
            
            subtitle_num = (i // chunk_size) + 1
            srt_content += f"{subtitle_num}\n"
            srt_content += f"{format_time(start_time)} --> {format_time(end_time)}\n"
            srt_content += f"{text}\n\n"
        return srt_content

    exp_col1, exp_col2, exp_col3 = st.columns(3)

    with exp_col1:
        st.download_button(
            label="📄 Download TXT",
            data=st.session_state.edited_transcript,
            file_name="transcript.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with exp_col2:
        # Note: SRT uses the *original* transcript for timing accuracy.
        srt_data = create_srt(st.session_state.timestamps)
        st.download_button(
            label="🎬 Download SRT",
            data=srt_data,
            file_name="subtitles.srt",
            mime="text/plain",
            use_container_width=True,
            help="SRT timing is based on the original, unedited transcript."
        )
