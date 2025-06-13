import streamlit as st
from google.cloud import speech
from google.oauth2 import service_account
import google.generativeai as genai
import json
from pydub import AudioSegment
import io
from datetime import timedelta
import hashlib
import time

# Page Configuration
st.set_page_config(
    page_title="Thanglish - Tamil Caption Generator",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Enhanced Professional Styling with Playful Colors
st.markdown("""
<style>
    /* Hide Streamlit elements */
    .css-1d391kg {display: none}
    section[data-testid="stSidebar"] {display: none}
    .css-k1vhr4 {padding: 1rem 2rem}
    
    /* Main container */
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* Header with playful gradient */
    .app-header {
        text-align: center;
        background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 50%, #45B7D1 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
    }
    
    .app-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 10px,
            rgba(255,255,255,0.05) 10px,
            rgba(255,255,255,0.05) 20px
        );
        animation: shine 3s linear infinite;
    }
    
    @keyframes shine {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .app-header h1 {
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .app-header p {
        font-size: 1.2rem;
        opacity: 0.95;
        margin: 0;
        font-weight: 500;
        position: relative;
        z-index: 1;
    }
    
    /* Step indicator with playful colors */
    .step-indicator {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
        gap: 1rem;
        flex-wrap: wrap;
    }
    
    .step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.7rem 1.2rem;
        border-radius: 25px;
        font-size: 0.95rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .step.active {
        background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
        color: white;
        transform: scale(1.05);
    }
    
    .step.inactive {
        background: #f8f9fa;
        color: #6c757d;
    }
    
    .step.completed {
        background: linear-gradient(135deg, #4ECDC4, #6ED3D0);
        color: white;
    }
    
    /* Cards with better spacing */
    .card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        transition: transform 0.2s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .card h3 {
        margin: 0 0 1.5rem 0;
        color: #2d3748;
        font-size: 1.4rem;
        font-weight: 700;
    }
    
    /* Enhanced buttons */
    .stButton>button {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 1.8rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255,107,107,0.4);
        width: auto;
        min-width: 140px;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(255,107,107,0.5);
        background: linear-gradient(135deg, #FF5252 0%, #FF7979 100%);
    }
    
    /* Secondary buttons */
    .secondary-button button {
        background: linear-gradient(135deg, #4ECDC4 0%, #6ED3D0 100%) !important;
        box-shadow: 0 4px 15px rgba(78,205,196,0.4) !important;
    }
    
    .secondary-button button:hover {
        background: linear-gradient(135deg, #45B7D1 0%, #5DADE2 100%) !important;
        box-shadow: 0 6px 25px rgba(69,183,209,0.5) !important;
    }
    
    /* Tertiary buttons */
    .tertiary-button button {
        background: linear-gradient(135deg, #FFA726 0%, #FFB74D 100%) !important;
        box-shadow: 0 4px 15px rgba(255,167,38,0.4) !important;
    }
    
    /* Download button special styling */
    .download-button button {
        background: linear-gradient(135deg, #4ECDC4 0%, #45B7D1 100%) !important;
        color: white !important;
        box-shadow: 0 4px 20px rgba(78,205,196,0.4) !important;
        font-size: 1.1rem !important;
        padding: 1rem 2rem !important;
        border-radius: 15px !important;
    }
    
    .download-button button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 35px rgba(78,205,196,0.6) !important;
    }
    
    /* Enhanced file uploader */
    .uploadedFile {
        border: 3px dashed #4ECDC4;
        border-radius: 16px;
        padding: 2.5rem;
        text-align: center;
        background: linear-gradient(135deg, #f8fdff 0%, #e8f8f5 100%);
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        border-color: #FF6B6B;
        background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
        transform: scale(1.02);
    }
    
    /* Info boxes with playful colors */
    .info-box {
        background: linear-gradient(135deg, #e8f4fd 0%, #d6eaf8 100%);
        border: 2px solid #45B7D1;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        font-size: 0.95rem;
        box-shadow: 0 4px 15px rgba(69,183,209,0.2);
    }
    
    .success-box {
        background: linear-gradient(135deg, #e8f8f5 0%, #d5f4e6 100%);
        border: 2px solid #4ECDC4;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        font-size: 0.95rem;
        color: #2d5a4a;
        box-shadow: 0 4px 15px rgba(78,205,196,0.2);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff8e1 0%, #fff3c4 100%);
        border: 2px solid #FFA726;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        font-size: 0.95rem;
        color: #e65100;
        box-shadow: 0 4px 15px rgba(255,167,38,0.2);
    }
    
    /* Line editor with better spacing */
    .line-editor {
        margin: 1rem 0;
        padding: 1rem;
        background: #fafbfc;
        border-radius: 12px;
        border: 1px solid #e9ecef;
    }
    
    .line-divider {
        height: 1px;
        background: linear-gradient(to right, transparent, #dee2e6, transparent);
        margin: 0.5rem 0;
    }
    
    /* Audio player styling */
    .audio-player {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #dee2e6;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    /* Language tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        justify-content: center;
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 20px;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
        color: white;
        box-shadow: 0 4px 15px rgba(255,107,107,0.3);
    }
    
    /* Export section */
    .export-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 16px;
        padding: 2rem;
        margin-top: 2rem;
        border: 2px solid #dee2e6;
    }
    
    /* Stats cards */
    .stats-container {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
        flex-wrap: wrap;
    }
    
    .stat-card {
        flex: 1;
        background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #e9ecef;
        min-width: 120px;
    }
    
    /* Expandable sections */
    .expandable-section {
        margin: 1.5rem 0;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main-container {
            padding: 0.5rem;
        }
        
        .app-header {
            padding: 2rem 1rem;
        }
        
        .app-header h1 {
            font-size: 2.2rem;
        }
        
        .step-indicator {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .card {
            padding: 1.5rem;
        }
        
        .stats-container {
            flex-direction: column;
        }
    }
    
    /* Navigation spacing */
    .navigation-section {
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 2px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Authentication and helper functions
def load_credentials():
    try:
        if "google_credentials_json" in st.secrets:
            creds_json = st.secrets["google_credentials_json"]
            
            if isinstance(creds_json, str):
                creds_dict = json.loads(creds_json)
            else:
                creds_dict = dict(creds_json)
            
            required_fields = ["type", "project_id", "private_key_id", "private_key", 
                             "client_email", "client_id", "auth_uri", "token_uri"]
            missing_fields = [field for field in required_fields if field not in creds_dict]
            
            if missing_fields:
                return None, f"Missing required fields in credentials: {missing_fields}"
            
            private_key = creds_dict.get("private_key", "")
            if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
                return None, "Private key format is invalid"
            
            if not private_key.endswith("-----END PRIVATE KEY-----\n"):
                if not private_key.endswith("-----END PRIVATE KEY-----"):
                    creds_dict["private_key"] = private_key + "\n-----END PRIVATE KEY-----\n"
                elif not private_key.endswith("\n"):
                    creds_dict["private_key"] = private_key + "\n"
            
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            return credentials, "Success"
            
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
            return None, "No credentials found in secrets"
            
    except json.JSONDecodeError as e:
        return None, f"JSON parsing error: {str(e)}"
    except ValueError as e:
        return None, f"Credential validation error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error loading credentials: {str(e)}"

def get_audio_hash(audio_content):
    return hashlib.md5(audio_content).hexdigest()

def cache_translation_results(audio_hash, results):
    cache_key = f"cache_{audio_hash}"
    st.session_state[cache_key] = {
        'timestamp': time.time(),
        'results': results
    }

def get_cached_translations(audio_hash):
    cache_key = f"cache_{audio_hash}"
    if cache_key in st.session_state:
        cached_data = st.session_state[cache_key]
        if time.time() - cached_data['timestamp'] < 86400:
            return cached_data['results']
    return None

def process_video_to_audio(video_content):
    try:
        video_segment = AudioSegment.from_file(io.BytesIO(video_content))
        audio_segment = video_segment.set_frame_rate(16000).set_channels(1)
        buffer = io.BytesIO()
        audio_segment.export(buffer, format="flac")
        return buffer.getvalue(), True
    except Exception as e:
        return None, False

def generate_initial_translations(tamil_text):
    try:
        # Enhanced prompt for better Tanglish accuracy
        tanglish_prompt = f"""
        Convert this Tamil text to highly accurate Thanglish (Tamil written in phonetic English letters) following these strict rules:

        CRITICAL PHONETIC RULES:
        - க = ka/ga, ச = cha/sa, ட = ta/da, த = tha, ப = pa/ba, ற = ra/rra
        - ங் = ng, ன் = n, ம் = m, ல் = l, ர் = r, ய் = y, ழ் = zh
        - ஆ = aa, ஈ = ee, ஊ = oo, ஏ = e, ஐ = ai, ஓ = o, ஔ = au
        - Double consonants: க்க = kka, ச்ச = chcha, ட்ட = tta, ப்ப = ppa
        
        WORD ACCURACY FIXES:
        - மிசைல் = missile (keep English technical terms)
        - சிஸ்டம் = system 
        - மெசேஜ் = message
        - டெக்னாலஜி = technology
        - இன்ஜினியர் = engineer
        - கம்ப்யூட்டர் = computer
        
        COMMON WORDS - USE THESE EXACT SPELLINGS:
        - என்ன = enna, அவன் = avan, இவன் = ivan, அது = adhu, இது = idhu
        - நமக்கு = namaku, எங்களுக்கு = engaluku, உங்களுக்கு = ungaluku
        - பண்ணலாம் = pannalam, செய்யலாம் = seiyalam
        - இருக்கு = iruku, வருகிறேன் = varukiren
        - கிட்ட = kitta, கூட = kooda, மட்டும் = mattum
        
        EXAMPLES OF CORRECT CONVERSION:
        - நிச்சயமான = nichchayamana 
        - நாடுகள் = naadugal
        - தொழில்நுட்பம் = thozhilnutpam
        - பொறுப்பு = poruppu
        - நிறுவனம் = niruvanam
        
        Text: "{tamil_text}"

        Return ONLY the accurate Thanglish translation with proper phonetic spelling.
        """
        
        tanglish_response = generative_model.generate_content(tanglish_prompt)
        tanglish_text = tanglish_response.text.strip()
        
        english_prompt = f"""
        Translate this Tamil text to natural, contextually accurate English with perfect grammar.

        TRANSLATION GUIDELINES:
        - Preserve the original meaning and conversational tone
        - Use natural English expressions, not literal translations
        - Maintain technical terms appropriately 
        - Keep the conversational flow for spoken content
        - For Tamil cultural references, use equivalent English expressions
        - Ensure grammatical correctness and natural sentence structure

        Text: "{tamil_text}"

        Return ONLY the natural English translation with proper grammar.
        """
        
        english_response = generative_model.generate_content(english_prompt)
        english_text = english_response.text.strip()
        
        return {
            'tamil': tamil_text,
            'tanglish': tanglish_text,
            'english': english_text
        }
    except Exception as e:
        return {
            'tamil': tamil_text,
            'tanglish': f"Translation Error: {e}",
            'english': f"Translation Error: {e}"
        }

def smart_text_sync(edited_tanglish, original_translations):
    if not original_translations:
        return None, "no_original"
    
    original_words = original_translations['tanglish'].split()
    edited_words = edited_tanglish.split()
    
    word_diff_ratio = abs(len(original_words) - len(edited_words)) / max(len(original_words), 1)
    
    if word_diff_ratio > 0.3:
        return None, "major_changes"
    
    return {
        'tamil': original_translations['tamil'],
        'tanglish': edited_tanglish,
        'english': original_translations['english']
    }, "minor_changes"

# Initialize Authentication
credentials, auth_message = load_credentials()
auth_success = credentials is not None

if auth_success:
    try:
        speech_client = speech.SpeechClient(credentials=credentials)
        if "gemini_api_key" in st.secrets:
            genai.configure(api_key=st.secrets["gemini_api_key"])
            generative_model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            auth_success = False
            auth_message = "Gemini API key not found in secrets"
    except Exception as e:
        auth_success = False
        auth_message = f"Error initializing clients: {str(e)}"

# Initialize Session State
session_vars = [
    'current_step', 'audio_hash', 'original_transcript', 'tanglish_transcript', 
    'tamil_transcript', 'english_transcript', 'timestamps', 'editing_mode',
    'save_message', 'original_translations', 'file_type', 'audio_content'
]

for var in session_vars:
    if var not in st.session_state:
        if var == 'current_step':
            st.session_state[var] = 1
        elif var == 'editing_mode':
            st.session_state[var] = False
        elif var in ['timestamps', 'original_translations']:
            st.session_state[var] = {}
        else:
            st.session_state[var] = ""

# Main App
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="app-header">
    <h1>🎬 Thanglish</h1>
    <p>Professional Tamil Caption Generator - Audio & Video to Perfect Thanglish/Tamil/English</p>
</div>
""", unsafe_allow_html=True)

# Step Indicator
def get_step_class(step_num):
    current = st.session_state.current_step
    if step_num < current:
        return "completed"
    elif step_num == current:
        return "active"
    else:
        return "inactive"

st.markdown(f"""
<div class="step-indicator">
    <div class="step {get_step_class(1)}">
        <span>1</span> Upload
    </div>
    <div class="step {get_step_class(2)}">
        <span>2</span> Process
    </div>
    <div class="step {get_step_class(3)}">
        <span>3</span> Edit
    </div>
    <div class="step {get_step_class(4)}">
        <span>4</span> Export
    </div>
</div>
""", unsafe_allow_html=True)

if not auth_success:
    st.markdown(f"""
    <div class="warning-box">
        ⚠️ Service temporarily unavailable: {auth_message}<br>
        Please try again later or contact support.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# STEP 1: Upload
if st.session_state.current_step == 1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📁 Upload Your File")
    
    st.markdown("""
    <div class="info-box">
        💡 <strong>Supported formats:</strong> Audio (MP3, WAV, M4A) and Video (MP4, MOV, AVI)<br>
        📊 <strong>File limit:</strong> 200MB | ⏱️ <strong>Duration:</strong> Up to 60 minutes
    </div>
    """, unsafe_allow_html=True)
    
    # Pro Tips Dropdown
    with st.expander("🎯 Pro Tips for Better Accuracy", expanded=False):
        st.markdown("""
        **🔊 Audio Quality Tips:**
        - Use clear, high-quality audio (avoid background noise)
        - Speak clearly and at normal pace (not too fast)
        - Use a good microphone if possible
        - Avoid echo or reverb
        
        **🎤 Recording Best Practices:**
        - Record in a quiet environment
        - Keep consistent volume levels
        - Pause between sentences for better processing
        - Tamil + English mixed content works great!
        
        **📹 Video Tips:**
        - Good audio quality matters more than video quality
        - Built-in phone mics work fine for clear speech
        - Avoid windy outdoor recordings
        - Indoor recordings usually work better
        """)
    
    uploaded_file = st.file_uploader(
        "Drop your file here or click to browse",
        type=["mp3", "wav", "m4a", "ogg", "flac", "mp4", "mov", "avi", "mkv"],
        help="Upload audio or video files for transcription",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        st.session_state.file_type = file_extension
        is_video = file_extension in ['mp4', 'mov', 'avi', 'mkv']
        
        # File info
        file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        try:
            if is_video:
                duration_text = f"~{file_size / 2:.1f} minutes (estimated)"
            else:
                audio_segment = AudioSegment.from_file(uploaded_file)
                duration_minutes = len(audio_segment) / (1000 * 60)
                duration_text = f"{duration_minutes:.1f} minutes"
        except:
            duration_text = "Duration calculation unavailable"
        
        st.markdown(f"""
        <div class="success-box">
            ✅ <strong>File uploaded:</strong> {uploaded_file.name}<br>
            📁 <strong>Size:</strong> {file_size:.1f} MB | ⏱️ <strong>Duration:</strong> {duration_text}<br>
            🎯 <strong>Type:</strong> {'Video' if is_video else 'Audio'} file
        </div>
        """, unsafe_allow_html=True)
        
        # Audio/Video preview
        if is_video:
            st.markdown("""
            <div class="info-box">
                🎥 Video detected! We'll extract high-quality audio for processing.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="audio-player">', unsafe_allow_html=True)
            st.audio(uploaded_file)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Language settings
        with st.expander("⚙️ Advanced Settings (Optional)", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                primary_language = st.selectbox(
                    "Primary Language",
                    ["ta-IN", "en-IN", "hi-IN"],
                    help="Main language in your audio/video"
                )
            with col2:
                secondary_language = st.selectbox(
                    "Secondary Language", 
                    ["en-IN", "ta-IN", "hi-IN"],
                    help="Fallback for mixed content"
                )
            
            enable_punctuation = st.checkbox("Auto Punctuation", value=True)
            enable_word_timestamps = st.checkbox("Word Timestamps", value=True)
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                # Store file content in session state
                st.session_state.uploaded_file_content = uploaded_file.getvalue()
                st.session_state.current_step = 2
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# STEP 2: Processing
elif st.session_state.current_step == 2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🔄 Processing Your File")
    
    # Auto-start processing
    progress_container = st.container()
    status_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
    
    with status_container:
        status_text = st.empty()
    
    # Auto-process without asking for file upload again
    if not hasattr(st.session_state, 'uploaded_file_content'):
        st.error("❌ No file found. Please go back and upload a file.")
        if st.button("← Back to Upload"):
            st.session_state.current_step = 1
            st.rerun()
        st.stop()
    
    try:
        # Reset states
        st.session_state.editing_mode = False
        st.session_state.save_message = ""
        
        status_text.info("📁 Reading file...")
        progress_bar.progress(10)
        time.sleep(0.5)
        
        audio_content = st.session_state.uploaded_file_content
        audio_hash = get_audio_hash(audio_content)
        st.session_state.audio_hash = audio_hash
        
        status_text.info("🔍 Checking cache...")
        progress_bar.progress(20)
        time.sleep(0.5)
        
        cached_results = get_cached_translations(audio_hash)
        
        if cached_results:
            status_text.success("⚡ Loading from cache...")
            progress_bar.progress(100)
            
            st.session_state.original_transcript = cached_results['tamil']
            st.session_state.tamil_transcript = cached_results['tamil']
            st.session_state.tanglish_transcript = cached_results['tanglish']
            st.session_state.english_transcript = cached_results['english']
            st.session_state.timestamps = cached_results.get('timestamps', [])
            st.session_state.original_translations = cached_results
            st.session_state.editing_mode = True
            st.session_state.current_step = 3
            st.session_state.audio_content = audio_content
            
            time.sleep(1)
            st.rerun()
        
        # Process file
        file_extension = st.session_state.file_type
        is_video = file_extension in ['mp4', 'mov', 'avi', 'mkv']
        
        if is_video:
            status_text.info("🎥 Extracting audio from video...")
            progress_bar.progress(30)
            time.sleep(1)
            
            processed_audio, success = process_video_to_audio(audio_content)
            if not success:
                st.error("❌ Failed to extract audio from video. Please try a different file.")
                st.stop()
            content = processed_audio
        else:
            status_text.info("🎵 Processing audio...")
            progress_bar.progress(30)
            time.sleep(1)
            
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_content))
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
            buffer = io.BytesIO()
            audio_segment.export(buffer, format="flac")
            content = buffer.getvalue()
        
        # Store processed audio for playback
        st.session_state.audio_content = content
        
        status_text.info("🗣️ Converting speech to text...")
        progress_bar.progress(50)
        time.sleep(1)
        
        recognition_audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
            sample_rate_hertz=16000,
            language_code=st.session_state.get('primary_language', 'ta-IN'),
            alternative_language_codes=[st.session_state.get('secondary_language', 'en-IN')],
            enable_automatic_punctuation=st.session_state.get('enable_punctuation', True),
            enable_word_time_offsets=st.session_state.get('enable_word_timestamps', True),
            model="latest_long"
        )

        response = speech_client.recognize(config=config, audio=recognition_audio)
        
        if not response.results:
            st.warning("⚠️ Could not transcribe the file. Please check audio quality and language settings.")
            st.stop()
        
        status_text.info("📝 Processing transcription...")
        progress_bar.progress(70)
        time.sleep(1)
        
        full_transcript = ""
        timestamps_data = []
        for result in response.results:
            full_transcript += result.alternatives[0].transcript + " "
            if st.session_state.get('enable_word_timestamps', True):
                for word_info in result.alternatives[0].words:
                    timestamps_data.append({
                        'word': word_info.word,
                        'start_time': word_info.start_time.total_seconds(),
                        'end_time': word_info.end_time.total_seconds()
                    })
        
        tamil_transcript = full_transcript.strip()
        
        status_text.info("🌍 Generating translations...")
        progress_bar.progress(85)
        time.sleep(1)
        
        translations = generate_initial_translations(tamil_transcript)
        
        status_text.info("💾 Saving results...")
        progress_bar.progress(95)
        time.sleep(0.5)
        
        st.session_state.original_transcript = tamil_transcript
        st.session_state.tamil_transcript = translations['tamil']
        st.session_state.tanglish_transcript = translations['tanglish']
        st.session_state.english_transcript = translations['english']
        st.session_state.timestamps = timestamps_data
        st.session_state.original_translations = translations.copy()
        st.session_state.original_translations['timestamps'] = timestamps_data
        
        cache_translation_results(audio_hash, st.session_state.original_translations)
        
        st.session_state.editing_mode = True
        st.session_state.current_step = 3
        
        progress_bar.progress(100)
        status_text.success("✅ Processing complete!")
        time.sleep(1)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        if st.button("← Back to Upload"):
            st.session_state.current_step = 1
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# STEP 3: Edit
elif st.session_state.current_step == 3 and st.session_state.editing_mode:
    # Audio player if available
    if st.session_state.audio_content:
        st.markdown('<div class="audio-player">', unsafe_allow_html=True)
        st.markdown("#### 🎵 Audio Playback")
        st.audio(st.session_state.audio_content)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ✏️ Edit Your Transcript")
    
    if st.session_state.save_message:
        st.markdown(f'<div class="success-box">{st.session_state.save_message}</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        💡 <strong>Pro Tip:</strong> Edit in Thanglish for best results. Use 'Smart Sync' for quick updates or 'AI Re-translate' for accuracy.
    </div>
    """, unsafe_allow_html=True)
    
    # Editing guide dropdown
    with st.expander("📚 Editing Guide & Tips", expanded=False):
        st.markdown("""
        **🎯 Editing Best Practices:**
        
        **For Thanglish Accuracy:**
        - Use phonetic English spelling for Tamil words
        - Keep technical terms in English (system, technology, etc.)
        - Example: "நமக்கு" → "namaku" (not "namakku")
        - Example: "மிசைல்" → "missile" (keep as English)
        
        **Common Thanglish Patterns:**
        - "என்ன" → "enna", "எப்படி" → "eppadi"
        - "பண்ணலாம்" → "pannalam", "செய்யலாம்" → "seiyalam"
        - "இருக்கு" → "iruku", "வருகிறேன்" → "varukiren"
        
        **Editing Tools Explained:**
        - **Smart Sync**: Quick local sync between languages
        - **AI Re-translate**: Full AI-powered translation for major edits
        - **Reset Original**: Restore to initial transcription
        
        **Pro Tips:**
        - Edit line by line for better control
        - Use proper punctuation for SRT exports
        - Check the preview tabs to see all language versions
        """)
    
    # Editing tools with better spacing
    st.markdown("#### 🛠️ Editing Tools")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
        if st.button("🔄 Smart Sync", help="Sync other languages with your edits locally", use_container_width=True):
            with st.spinner("🔄 Syncing languages..."):
                synced_result, change_type = smart_text_sync(
                    st.session_state.tanglish_transcript, 
                    st.session_state.original_translations
                )
                
                if synced_result:
                    st.session_state.tamil_transcript = synced_result['tamil']
                    st.session_state.english_transcript = synced_result['english']
                    st.session_state.save_message = "✅ Languages synced locally!"
                else:
                    st.session_state.save_message = "⚠️ Major changes detected. Use 'AI Re-translate' for better accuracy."
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if st.button("🤖 AI Re-translate", help="Use AI to re-translate all languages", use_container_width=True):
            with st.spinner("🤖 Re-translating with AI..."):
                try:
                    new_translations = generate_initial_translations(st.session_state.tanglish_transcript)
                    
                    st.session_state.tamil_transcript = new_translations['tamil']
                    st.session_state.english_transcript = new_translations['english']
                    st.session_state.save_message = "✅ Re-translated with AI!"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Re-translation failed: {e}")
    
    with col3:
        st.markdown('<div class="tertiary-button">', unsafe_allow_html=True)
        if st.button("↩️ Reset Original", help="Reset to original transcription", use_container_width=True):
            if st.session_state.original_translations:
                st.session_state.tanglish_transcript = st.session_state.original_translations['tanglish']
                st.session_state.tamil_transcript = st.session_state.original_translations['tamil']
                st.session_state.english_transcript = st.session_state.original_translations['english']
                st.session_state.save_message = "↩️ Reset to original!"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Line-by-line transcript editor with better spacing
    st.markdown("#### 📝 Line-by-Line Editor")
    st.markdown('<div class="line-editor">', unsafe_allow_html=True)
    
    # Convert to line-by-line format
    lines = st.session_state.tanglish_transcript.split('.')
    lines = [line.strip() for line in lines if line.strip()]
    
    edited_lines = []
    for i, line in enumerate(lines):
        edited_line = st.text_input(
            f"Line {i+1}",
            value=line,
            key=f"line_{i}",
            label_visibility="collapsed"
        )
        edited_lines.append(edited_line)
        
        # Improved line divider
        if i < len(lines) - 1:
            st.markdown('<div class="line-divider"></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Update transcript from lines
    new_transcript = '. '.join(edited_lines)
    if new_transcript != st.session_state.tanglish_transcript:
        st.session_state.tanglish_transcript = new_transcript
        st.session_state.save_message = ""
    
    # Stats with better styling
    word_count = len(new_transcript.split()) if new_transcript else 0
    char_count = len(new_transcript) if new_transcript else 0
    estimated_duration = word_count / 150 if word_count > 0 else 0
    
    st.markdown("#### 📊 Statistics")
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("📊 Words", word_count)
    with col_stat2:
        st.metric("🔤 Characters", char_count)
    with col_stat3:
        st.metric("⏱️ Duration", f"{estimated_duration:.1f} min")
    
    # Language preview tabs with better spacing
    st.markdown("#### 📖 Language Previews")
    tab1, tab2, tab3 = st.tabs(["🔤 Thanglish", "🕉️ Tamil", "🌍 English"])
    
    with tab1:
        st.text_area(
            "Thanglish Preview:", 
            value=st.session_state.tanglish_transcript, 
            height=150, 
            disabled=True,
            key="tanglish_preview"
        )
    
    with tab2:
        st.text_area(
            "Tamil Preview:", 
            value=st.session_state.tamil_transcript, 
            height=150, 
            disabled=True,
            key="tamil_preview"
        )
    
    with tab3:
        st.text_area(
            "English Preview:", 
            value=st.session_state.english_transcript, 
            height=150, 
            disabled=True,
            key="english_preview"
        )
    
    # Navigation with better spacing
    st.markdown('<div class="navigation-section">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Back to Process"):
            st.session_state.current_step = 2
            st.rerun()
    with col3:
        if st.button("Continue to Export →"):
            st.session_state.current_step = 4
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# STEP 4: Export
elif st.session_state.current_step == 4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🎬 Export Configuration")
    
    st.markdown("""
    <div class="info-box">
        🎯 <strong>Choose your export settings:</strong> Configure subtitles like a professional video editor
    </div>
    """, unsafe_allow_html=True)
    
    # Export guide dropdown
    with st.expander("📖 Export Format Guide", expanded=False):
        st.markdown("""
        **📄 Text Format (TXT):**
        - Clean text for documents and scripts
        - Perfect for sharing transcripts
        - Easy to copy-paste into other applications
        
        **🎬 Subtitle Format (SRT):**
        - Professional video subtitles
        - Works with Premiere Pro, Final Cut, DaVinci Resolve
        - Compatible with YouTube, Vimeo, and other platforms
        - Includes timing information for video sync
        
        **💡 Pro Tips:**
        - Use 42 characters max for readable subtitles
        - Single line works best for mobile viewing
        - Double line for desktop/TV viewing
        - Minimum 3 seconds ensures readability
        """)
    
    # Export options in columns
    col1, col2 = st.columns(2)
    
    with col1:
        export_language = st.selectbox(
            "🌍 Language",
            ["Thanglish", "Tamil", "English"],
            help="Choose which language version to download"
        )
        
        export_format = st.selectbox(
            "📄 Format",
            ["TXT", "SRT"],
            help="TXT for text, SRT for video subtitles"
        )
    
    with col2:
        if export_format == "SRT":
            max_chars = st.slider(
                "🔤 Max characters per subtitle",
                min_value=20, max_value=80, value=42,
                help="Premiere Pro style character limit"
            )
            
            min_duration = st.slider(
                "⏱️ Min duration (seconds)",
                min_value=1, max_value=10, value=3,
                help="Minimum time each subtitle shows"
            )
            
            lines_per_subtitle = st.radio(
                "📝 Lines per subtitle",
                ["Single", "Double"],
                help="Single or double line subtitles"
            )
        else:
            st.markdown("#### 📄 Text Export")
            st.markdown("Clean text format for documents and scripts")

    # Preview section
    st.markdown("#### 👁️ Export Preview")
    
    # Get export text
    if export_language == "Thanglish":
        export_text = st.session_state.tanglish_transcript
    elif export_language == "Tamil":
        export_text = st.session_state.tamil_transcript
    else:
        export_text = st.session_state.english_transcript
    
    if export_format == "SRT":
        # Create SRT preview
        def create_srt_preview(text, timestamps, max_chars=42):
            def format_time(seconds):
                td = timedelta(seconds=seconds)
                total_seconds = int(td.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                secs = total_seconds % 60
                millis = td.microseconds // 1000
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

            words = text.split()
            srt_content = ""
            chunk_size = 8
            
            for i in range(0, min(len(words), 24), chunk_size):  # Preview first 3 subtitles
                chunk_words = words[i : i + chunk_size]
                if not chunk_words:
                    continue
                
                # Use timestamps if available
                if timestamps and i < len(timestamps):
                    start_time = timestamps[min(i, len(timestamps) - 1)].get('start_time', i * 2)
                    end_time = timestamps[min(i + chunk_size - 1, len(timestamps) - 1)].get('end_time', (i + chunk_size) * 2)
                else:
                    start_time = i * 2
                    end_time = (i + chunk_size) * 2
                
                text_chunk = " ".join(chunk_words)
                
                # Respect character limit
                if len(text_chunk) > max_chars:
                    text_chunk = text_chunk[:max_chars-3] + "..."
                
                subtitle_num = (i // chunk_size) + 1
                srt_content += f"{subtitle_num}\n"
                srt_content += f"{format_time(start_time)} --> {format_time(end_time)}\n"
                srt_content += f"{text_chunk}\n\n"
            
            srt_content += "... (preview of first 3 subtitles)"
            return srt_content
        
        preview_content = create_srt_preview(
            export_text, 
            st.session_state.timestamps,
            max_chars if 'max_chars' in locals() else 42
        )
        st.code(preview_content, language="srt")
        
    else:
        # Text preview
        preview_text = export_text[:300] + "..." if len(export_text) > 300 else export_text
        st.text_area("Preview:", value=preview_text, height=150, disabled=True)
    
    # Enhanced download section
    st.markdown("#### 📥 Download Your Captions")
    
    # Initialize download state
    if 'download_ready' not in st.session_state:
        st.session_state.download_ready = False
        st.session_state.download_data = ""
        st.session_state.download_filename = ""
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Generate button
        st.markdown('<div class="download-button">', unsafe_allow_html=True)
        if st.button("🔄 Generate File", type="primary", use_container_width=True):
            with st.spinner(f"🔄 Preparing {export_language} {export_format} file..."):
                try:
                    if export_format == "TXT":
                        file_data = export_text
                        mime_type = "text/plain"
                        file_extension = "txt"
                    else:
                        # Create full SRT
                        def create_full_srt(text, timestamps, max_chars=42):
                            def format_time(seconds):
                                td = timedelta(seconds=seconds)
                                total_seconds = int(td.total_seconds())
                                hours = total_seconds // 3600
                                minutes = (total_seconds % 3600) // 60
                                secs = total_seconds % 60
                                millis = td.microseconds // 1000
                                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

                            words = text.split()
                            srt_content = ""
                            chunk_size = 8
                            
                            for i in range(0, len(words), chunk_size):
                                chunk_words = words[i : i + chunk_size]
                                if not chunk_words:
                                    continue
                                
                                if timestamps and i < len(timestamps):
                                    start_time = timestamps[min(i, len(timestamps) - 1)].get('start_time', i * 2)
                                    end_time = timestamps[min(i + chunk_size - 1, len(timestamps) - 1)].get('end_time', (i + chunk_size) * 2)
                                else:
                                    start_time = i * 2
                                    end_time = (i + chunk_size) * 2
                                
                                text_chunk = " ".join(chunk_words)
                                
                                if len(text_chunk) > max_chars:
                                    text_chunk = text_chunk[:max_chars-3] + "..."
                                
                                subtitle_num = (i // chunk_size) + 1
                                srt_content += f"{subtitle_num}\n"
                                srt_content += f"{format_time(start_time)} --> {format_time(end_time)}\n"
                                srt_content += f"{text_chunk}\n\n"
                            
                            return srt_content
                        
                        file_data = create_full_srt(
                            export_text, 
                            st.session_state.timestamps,
                            max_chars if 'max_chars' in locals() else 42
                        )
                        mime_type = "text/plain"
                        file_extension = "srt"
                    
                    filename = f"thanglish_captions_{export_language.lower()}.{file_extension}"
                    
                    # Store in session state
                    st.session_state.download_ready = True
                    st.session_state.download_data = file_data
                    st.session_state.download_filename = filename
                    st.session_state.download_mime = mime_type
                    
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ <strong>File generated successfully!</strong><br>
                        📁 File: {filename} | 📊 Size: {len(file_data.encode('utf-8')) / 1024:.1f} KB<br>
                        💡 Click "Download" to save your captions!
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Generation failed: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Download button (only appears after generation)
        if st.session_state.download_ready:
            st.download_button(
                label=f"📥 Download {export_language} {export_format}",
                data=st.session_state.download_data,
                file_name=st.session_state.download_filename,
                mime=st.session_state.download_mime,
                use_container_width=True,
                type="primary"
            )
        else:
            st.markdown("""
            <div style="padding: 0.8rem; text-align: center; color: #6c757d; 
                        border: 2px dashed #dee2e6; border-radius: 12px;">
                📝 Generate file first to download
            </div>
            """, unsafe_allow_html=True)
    
    # Additional actions
    st.markdown("#### 🔄 Next Steps")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
        if st.button("🔄 Process New File", help="Upload and process another file", use_container_width=True):
            # Reset all session state
            for var in session_vars:
                if var == 'current_step':
                    st.session_state[var] = 1
                elif var == 'editing_mode':
                    st.session_state[var] = False
                elif var in ['timestamps', 'original_translations']:
                    st.session_state[var] = {}
                else:
                    st.session_state[var] = ""
            # Reset download state
            st.session_state.download_ready = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="tertiary-button">', unsafe_allow_html=True)
        if st.button("📝 Try Different Format", help="Export in different format/language", use_container_width=True):
            st.session_state.download_ready = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation
    st.markdown('<div class="navigation-section">', unsafe_allow_html=True)
    if st.button("← Back to Edit"):
        st.session_state.current_step = 3
        st.session_state.download_ready = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Invalid step fallback
else:
    st.session_state.current_step = 1
    st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; margin-top: 3rem; border-top: 2px solid #e9ecef; 
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);">
    <p style="color: #6c757d; margin: 0; font-size: 1rem; font-weight: 500;">
        Made with ❤️ for Tamil creators | Thanglish - Professional AI-powered transcription
    </p>
    <p style="color: #adb5bd; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
        Tamil + English = Thanglish மேட்டர் 🚀
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
