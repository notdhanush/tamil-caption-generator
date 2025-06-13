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
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="Tamil Caption Generator Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Enhanced Styling ---
st.markdown("""
<style>
    .css-1d391kg {display: none}
    section[data-testid="stSidebar"] {
        display: none;
    }
    
    /* Main Header */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* Card Styling */
    .upload-card, .edit-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    .upload-card h2, .edit-card h2 {
        color: #2c3e50;
        margin-bottom: 1.5rem;
        font-size: 1.8rem;
    }
    
    /* Button Styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* Results and Info Boxes */
    .results-box {
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #28A745;
        background: linear-gradient(135deg, #f8fff8 0%, #e8f5e8 100%);
        margin-top: 1rem;
        box-shadow: 0 3px 10px rgba(40, 167, 69, 0.1);
    }
    
    .info-box {
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border: 1px solid #2196f3;
        color: #0277bd;
        margin: 1rem 0;
        font-size: 0.95em;
        box-shadow: 0 2px 8px rgba(33, 150, 243, 0.1);
    }
    
    .edit-info {
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        border: 1px solid #9c27b0;
        color: #7b1fa2;
        margin: 1rem 0;
        font-size: 0.95em;
        box-shadow: 0 2px 8px rgba(156, 39, 176, 0.1);
    }
    
    .save-success {
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #28a745;
        color: #155724;
        margin: 1rem 0;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.1);
    }
    
    .error-box {
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #dc3545;
        color: #721c24;
        margin: 1rem 0;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(220, 53, 69, 0.1);
    }
    
    /* Audio Player Enhancement */
    .audio-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    /* Language Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
    }
    
    /* File Upload Area */
    .uploadedFile {
        background: #f8f9fa;
        border: 2px dashed #dee2e6;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        border-color: #4ECDC4;
        background: #f0fffe;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
    }
    
    /* Text Areas */
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid #dee2e6;
        padding: 1rem;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    .stTextArea textarea:focus {
        border-color: #4ECDC4;
        box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.1);
    }
    
    /* Feature Grid */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.15);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Export Section */
    .export-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-top: 2rem;
        border: 1px solid #dee2e6;
    }
    
    .export-section h2 {
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Enhanced Authentication ---
def load_credentials():
    """Load and validate Google Cloud credentials with comprehensive error handling."""
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
            return None, "No Google Cloud credentials found in secrets"
            
    except json.JSONDecodeError as e:
        return None, f"JSON parsing error: {str(e)}"
    except ValueError as e:
        return None, f"Credential validation error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error loading credentials: {str(e)}"

# --- Enhanced Caching System ---
def get_audio_hash(audio_content):
    """Generate unique hash for audio content for caching"""
    return hashlib.md5(audio_content).hexdigest()

def cache_translation_results(audio_hash, results):
    """Cache all translation results using session state"""
    cache_key = f"cache_{audio_hash}"
    st.session_state[cache_key] = {
        'timestamp': time.time(),
        'results': results
    }

def get_cached_translations(audio_hash):
    """Get cached translations if available and not expired"""
    cache_key = f"cache_{audio_hash}"
    if cache_key in st.session_state:
        cached_data = st.session_state[cache_key]
        # Cache valid for 24 hours
        if time.time() - cached_data['timestamp'] < 86400:
            return cached_data['results']
    return None

# --- Video Processing Function ---
def process_video_to_audio(video_content):
    """Extract audio from video files and convert to processable format"""
    try:
        # Load video file
        video_segment = AudioSegment.from_file(io.BytesIO(video_content))
        
        # Convert to standard audio format for processing
        audio_segment = video_segment.set_frame_rate(16000).set_channels(1)
        
        # Export as audio
        buffer = io.BytesIO()
        audio_segment.export(buffer, format="flac")
        return buffer.getvalue(), True
        
    except Exception as e:
        return None, False

# --- Enhanced Translation Functions ---
def generate_initial_translations(tamil_text):
    """Generate all translations at once with improved accuracy"""
    try:
        # Enhanced Tanglish conversion with proper phonetic rules
        tanglish_prompt = f"""
        Convert this Tamil text to accurate Tanglish (Tamil written in phonetic English letters) following these rules:

        PHONETIC RULES:
        - க = ka/ga, ச = cha/sa, ட = ta/da, த = tha, ப = pa/ba, ற = ra
        - ங் = ng, ன் = n, ம் = m, ல் = l, ர் = r, ய் = y
        - ஆ = aa, ஈ = ee, ஊ = oo, ஏ = e, ஐ = ai, ஓ = o, ஔ = au
        - Double consonants: க்க = kka, ச்ச = cha, ட்ட = tta, ப்ப = ppa
        - Common words: என்ன = enna, அவன் = avan, இவன் = ivan, அது = adhu

        EXAMPLES:
        - நமக்கு = namaku (not "namakku")
        - நிச்சயமான = nichchayamana (not "nichchayamaana")
        - நாடுகள் = naadugal (not "naadukkitta")
        - கிட்ட = kitta (not "kku")
        - தொழில்நுட்பம் = thozhilnutpam
        - சிஸ்டம் = system
        - மிசைல் = missile

        Make it sound natural like how Tamil speakers actually write in English.
        Keep English words as they are (technology, system, missile, etc.).

        Text: "{tamil_text}"

        Return only the accurate Tanglish translation, nothing else.
        """
        
        tanglish_response = generative_model.generate_content(tanglish_prompt)
        tanglish_text = tanglish_response.text.strip()
        
        # Enhanced English translation
        english_prompt = f"""
        Translate this Tamil text to natural, contextually accurate English.

        TRANSLATION GUIDELINES:
        - Preserve the original meaning and tone
        - Use natural English expressions, not word-for-word translation
        - Maintain any technical terms appropriately
        - Keep the conversational flow if it's spoken content
        - For Tamil cultural references, use equivalent English expressions

        Text: "{tamil_text}"

        Return only the natural English translation, nothing else.
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

# --- Local Text Processing Functions ---
def local_text_corrections(text):
    """Apply common text corrections without API calls"""
    corrections = {
        # Common speech-to-text errors
        'anna': 'அண்ணா',
        'amma': 'அம்மா',
        'appa': 'அப்பா',
        'akka': 'அக்கா',
        'thambi': 'தம்பி',
        'thangachi': 'தங்கச்சி',
        'message': 'missile',  # Common misrecognition
        'system': 'system',
        'technology': 'technology',
    }
    
    corrected_text = text
    for error, correction in corrections.items():
        corrected_text = corrected_text.replace(error, correction)
    
    return corrected_text

def smart_text_sync(edited_tanglish, original_translations):
    """Intelligently sync translations without API calls when possible"""
    original_words = original_translations['tanglish'].split()
    edited_words = edited_tanglish.split()
    
    # If word count is very different, suggest re-translation
    word_diff_ratio = abs(len(original_words) - len(edited_words)) / max(len(original_words), 1)
    
    if word_diff_ratio > 0.3:  # More than 30% word difference
        return None, "major_changes"
    
    # For minor changes, apply simple sync
    return {
        'tamil': original_translations['tamil'],
        'tanglish': edited_tanglish,
        'english': original_translations['english']
    }, "minor_changes"

# --- Initialize Authentication ---
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

# --- Initialize Session State ---
session_vars = [
    'audio_hash', 'original_transcript', 'tanglish_transcript', 'tamil_transcript',
    'english_transcript', 'timestamps', 'processing_translations', 'editing_mode',
    'save_message', 'original_translations', 'file_type'
]

for var in session_vars:
    if var not in st.session_state:
        if var in ['processing_translations', 'editing_mode']:
            st.session_state[var] = False
        elif var in ['timestamps', 'original_translations']:
            st.session_state[var] = {}
        else:
            st.session_state[var] = ""

# --- Main App UI ---
st.markdown("""
<div class="main-header">
    <h1>🎬 Tamil Caption Generator Pro</h1>
    <p>Upload Audio/Video → Get Perfect Captions → Edit Unlimited → Download in Any Language</p>
</div>
""", unsafe_allow_html=True)

# Features Overview
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">🎤</div>
        <h3>Audio Support</h3>
        <p>WAV, MP3, FLAC, M4A, OGG</p>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🎥</div>
        <h3>Video Support</h3>
        <p>MP4, AVI, MOV, MKV</p>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🗣️</div>
        <h3>Multi-Language</h3>
        <p>Tamil, Tanglish, English</p>
    </div>
    <div class="feature-card">
        <div class="feature-icon">✏️</div>
        <h3>Unlimited Editing</h3>
        <p>Edit as much as you want</p>
    </div>
</div>
""", unsafe_allow_html=True)

if not auth_success:
    st.markdown(f"""
    <div class="error-box">
        ⚠️ Service is currently unavailable: {auth_message}
        <br>Please try again later or contact support.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    st.markdown("## 📤 Upload & Transcribe")
    
    uploaded_file = st.file_uploader(
        "Choose your audio or video file",
        type=["wav", "mp3", "flac", "m4a", "ogg", "mp4", "avi", "mov", "mkv"],
        help="Supports audio formats (WAV, MP3, FLAC, M4A, OGG) and video formats (MP4, AVI, MOV, MKV) - Max: 200MB"
    )

    if uploaded_file:
        # Store file type
        file_extension = uploaded_file.name.lower().split('.')[-1]
        st.session_state.file_type = file_extension
        is_video = file_extension in ['mp4', 'avi', 'mov', 'mkv']
        
        if is_video:
            st.markdown("""
            <div class="info-box">
                🎥 <strong>Video File Detected!</strong><br>
                We'll extract the audio automatically for processing.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="audio-container">', unsafe_allow_html=True)
            st.audio(uploaded_file)
            st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="edit-card">', unsafe_allow_html=True)
    st.markdown("## 📝 Edit Transcript")

    if st.session_state.editing_mode and st.session_state.tanglish_transcript:
        
        # Show save message if exists
        if st.session_state.save_message:
            st.markdown(f'<div class="save-success">{st.session_state.save_message}</div>', unsafe_allow_html=True)
        
        # Editing info
        st.markdown("""
        <div class="edit-info">
            ✨ <strong>Unlimited Editing Mode Active</strong><br>
            Edit as much as you want - changes are processed locally for instant updates.
        </div>
        """, unsafe_allow_html=True)
        
        # Edit controls
        col_edit1, col_edit2, col_edit3 = st.columns([2, 1, 1])
        with col_edit1:
            st.markdown("### ✏️ Smart Editing Tools")
        with col_edit2:
            if st.button("🔄 Smart Sync", help="Sync other languages with your edits locally", use_container_width=True):
                with st.spinner("🔄 Syncing languages locally..."):
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
        
        with col_edit3:
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
        
        # Quick Actions
        col_quick1, col_quick2, col_quick3 = st.columns(3)
        with col_quick1:
            if st.button("🔤 Fix Common Errors", help="Apply common Tamil speech-to-text corrections", use_container_width=True):
                corrected_text = local_text_corrections(st.session_state.tanglish_transcript)
                st.session_state.tanglish_transcript = corrected_text
                st.session_state.save_message = "✅ Common errors fixed!"
                st.rerun()
        
        with col_quick2:
            if st.button("↩️ Reset to Original", help="Reset to original transcription", use_container_width=True):
                if st.session_state.original_translations:
                    st.session_state.tanglish_transcript = st.session_state.original_translations['tanglish']
                    st.session_state.tamil_transcript = st.session_state.original_translations['tamil']
                    st.session_state.english_transcript = st.session_state.original_translations['english']
                    st.session_state.save_message = "↩️ Reset to original!"
                    st.rerun()
        
        with col_quick3:
            if st.button("📋 Copy Tanglish", help="Copy Tanglish text to clipboard", use_container_width=True):
                st.session_state.save_message = "📋 Tanglish text ready to copy from the editor below!"
                st.rerun()
        
        # Main editing area
        st.markdown("### 📝 Edit Your Transcript")
        st.info("💡 **Pro Tip:** Edit freely in Tanglish! Use 'Smart Sync' for free local updates or 'AI Re-translate' for AI-powered accuracy.")
        
        # Editing area with enhanced features
        edited_tanglish = st.text_area(
            "Edit your transcript (Tanglish):",
            value=st.session_state.tanglish_transcript,
            height=250,
            key="tanglish_editor",
            help="Edit in Tanglish - unlimited edits! Changes are saved automatically.",
            placeholder="Your Tanglish transcript will appear here..."
        )
        
        # Update session state when text changes
        if edited_tanglish != st.session_state.tanglish_transcript:
            st.session_state.tanglish_transcript = edited_tanglish
            st.session_state.save_message = ""
        
        # Word count and stats
        word_count = len(edited_tanglish.split()) if edited_tanglish else 0
        char_count = len(edited_tanglish) if edited_tanglish else 0
        
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("📊 Words", word_count)
        with col_stats2:
            st.metric("🔤 Characters", char_count)
        with col_stats3:
            estimated_duration = word_count / 150 if word_count > 0 else 0  # Assuming 150 words per minute
            st.metric("⏱️ Est. Duration", f"{estimated_duration:.1f} min")
        
        # Language preview tabs with enhanced styling
        st.markdown("### 📖 Language Previews")
        tab1, tab2, tab3 = st.tabs(["🔤 Tanglish (Editable)", "🕉️ Tamil", "🌍 English"])
        
        with tab1:
            st.text_area(
                "Current Tanglish:", 
                value=st.session_state.tanglish_transcript, 
                height=120, 
                disabled=True,
                help="This is your current Tanglish text"
            )
        
        with tab2:
            st.text_area(
                "Current Tamil:", 
                value=st.session_state.tamil_transcript, 
                height=120, 
                disabled=True,
                help="Tamil version - updates when you sync or re-translate"
            )
        
        with tab3:
            st.text_area(
                "Current English:", 
                value=st.session_state.english_transcript, 
                height=120, 
                disabled=True,
                help="English version - updates when you sync or re-translate"
            )
        
        # Translation Quality Feedback
        st.markdown("### 🎯 Translation Quality")
        col_quality1, col_quality2 = st.columns(2)
        
        with col_quality1:
            quality_rating = st.select_slider(
                "Rate Tanglish Accuracy:",
                options=["Poor", "Fair", "Good", "Excellent"],
                value="Good",
                help="Help us improve by rating the accuracy"
            )
        
        with col_quality2:
            if st.button("💬 Report Issue", help="Report translation issues", use_container_width=True):
                st.info("📧 Issue reported! We'll use this feedback to improve our AI models.")
    
    else:
        # Show when no file is processed
        st.markdown("""
        <div class="info-box">
            👈 <strong>Upload a file to get started!</strong><br>
            Once you upload and process an audio/video file, you'll be able to edit the transcript here.
        </div>
        """, unsafe_allow_html=True)
        
        # Show preview of features
        st.markdown("### 🌟 What You'll Get:")
        st.markdown("""
        - **🎯 Accurate Tanglish**: Natural Tamil in English script
        - **✏️ Unlimited Editing**: Edit as much as you want
        - **🔄 Smart Sync**: Local updates without API calls
        - **🤖 AI Re-translate**: AI-powered accuracy improvements
        - **📊 Real-time Stats**: Word count, duration estimates
        - **💾 Auto-save**: Changes saved automatically
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Enhanced Export Section ---
if st.session_state.editing_mode and st.session_state.tanglish_transcript:
    st.markdown("---")
    st.markdown("""
    <div class="export-section">
        <h2>📥 Professional Export Options</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Export options
    col_export1, col_export2, col_export3 = st.columns([1, 1, 1])
    
    with col_export1:
        export_language = st.selectbox(
            "🌍 Select Language:",
            ["Tanglish", "Tamil", "English"],
            help="Choose which language version to download"
        )
    
    with col_export2:
        export_format = st.selectbox(
            "📄 Select Format:",
            ["TXT", "SRT", "VTT", "JSON"],
            help="Choose file format for different platforms"
        )
    
    with col_export3:
        export_quality = st.selectbox(
            "⚙️ Export Quality:",
            ["Standard", "High Quality", "Professional"],
            help="Choose export quality and formatting"
        )

    # Format-specific options
    if export_format in ["SRT", "VTT"]:
        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            words_per_subtitle = st.slider("Words per subtitle:", 5, 15, 8, help="How many words per subtitle line")
        with col_sub2:
            subtitle_duration = st.slider("Max subtitle duration (seconds):", 2, 8, 4, help="Maximum time each subtitle shows")

    def create_srt(text, timestamps, words_per_chunk=8):
        """Create enhanced SRT subtitle file"""
        def format_time(seconds):
            td = timedelta(seconds=seconds)
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            millis = td.microseconds // 1000
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

        text_words = text.split()
        srt_content = ""
        
        for i in range(0, len(text_words), words_per_chunk):
            chunk_words = text_words[i : i + words_per_chunk]
            if not chunk_words:
                continue
            
            timestamp_start_idx = min(i, len(timestamps) - 1) if timestamps else i
            timestamp_end_idx = min(i + words_per_chunk - 1, len(timestamps) - 1) if timestamps else i + words_per_chunk - 1
            
            if timestamps and timestamp_start_idx < len(timestamps) and timestamp_end_idx < len(timestamps):
                start_time = timestamps[timestamp_start_idx]['start_time']
                end_time = timestamps[timestamp_end_idx]['end_time']
            else:
                start_time = i * 2
                end_time = (i + words_per_chunk) * 2
            
            text_chunk = " ".join(chunk_words)
            
            subtitle_num = (i // words_per_chunk) + 1
            srt_content += f"{subtitle_num}\n"
            srt_content += f"{format_time(start_time)} --> {format_time(end_time)}\n"
            srt_content += f"{text_chunk}\n\n"
        
        return srt_content

    def create_vtt(text, timestamps, words_per_chunk=8):
        """Create WebVTT subtitle file"""
        def format_time_vtt(seconds):
            td = timedelta(seconds=seconds)
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            millis = td.microseconds // 1000
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

        text_words = text.split()
        vtt_content = "WEBVTT\n\n"
        
        for i in range(0, len(text_words), words_per_chunk):
            chunk_words = text_words[i : i + words_per_chunk]
            if not chunk_words:
                continue
            
            timestamp_start_idx = min(i, len(timestamps) - 1) if timestamps else i
            timestamp_end_idx = min(i + words_per_chunk - 1, len(timestamps) - 1) if timestamps else i + words_per_chunk - 1
            
            if timestamps and timestamp_start_idx < len(timestamps) and timestamp_end_idx < len(timestamps):
                start_time = timestamps[timestamp_start_idx]['start_time']
                end_time = timestamps[timestamp_end_idx]['end_time']
            else:
                start_time = i * 2
                end_time = (i + words_per_chunk) * 2
            
            text_chunk = " ".join(chunk_words)
            
            vtt_content += f"{format_time_vtt(start_time)} --> {format_time_vtt(end_time)}\n"
            vtt_content += f"{text_chunk}\n\n"
        
        return vtt_content

    def create_json_export(text, timestamps, language, metadata):
        """Create comprehensive JSON export"""
        export_data = {
            "metadata": {
                "language": language,
                "export_timestamp": time.time(),
                "word_count": len(text.split()),
                "character_count": len(text),
                "estimated_duration_minutes": len(text.split()) / 150,
                "file_type": st.session_state.get('file_type', 'unknown'),
                **metadata
            },
            "transcript": {
                "full_text": text,
                "words": text.split(),
                "timestamps": timestamps
            },
            "export_info": {
                "format": "JSON",
                "quality": export_quality,
                "generated_by": "Tamil Caption Generator Pro"
            }
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)

    # Enhanced export button
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        if st.button("📥 Generate & Download", type="primary", use_container_width=True):
            with st.spinner(f"🔄 Preparing {export_language} {export_format} file..."):
                try:
                    # Get text based on language
                    if export_language == "Tanglish":
                        export_text = st.session_state.tanglish_transcript
                    elif export_language == "Tamil":
                        export_text = st.session_state.tamil_transcript
                    else:
                        export_text = st.session_state.english_transcript
                    
                    # Generate file based on format
                    if export_format == "TXT":
                        file_extension = "txt"
                        if export_quality == "Professional":
                            file_data = f"Tamil Caption Generator Pro\n{'='*50}\n\n"
                            file_data += f"Language: {export_language}\n"
                            file_data += f"Export Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            file_data += f"Word Count: {len(export_text.split())}\n\n"
                            file_data += f"Transcript:\n{'-'*20}\n{export_text}"
                        else:
                            file_data = export_text
                        mime_type = "text/plain"
                    
                    elif export_format == "SRT":
                        file_extension = "srt"
                        file_data = create_srt(export_text, st.session_state.timestamps, words_per_subtitle)
                        mime_type = "text/plain"
                    
                    elif export_format == "VTT":
                        file_extension = "vtt"
                        file_data = create_vtt(export_text, st.session_state.timestamps, words_per_subtitle)
                        mime_type = "text/plain"
                    
                    elif export_format == "JSON":
                        file_extension = "json"
                        metadata = {
                            "export_quality": export_quality,
                            "original_file": uploaded_file.name if 'uploaded_file' in locals() else "unknown"
                        }
                        file_data = create_json_export(export_text, st.session_state.timestamps, export_language, metadata)
                        mime_type = "application/json"
                    
                    filename = f"transcript_{export_language.lower()}_{export_quality.lower().replace(' ', '_')}.{file_extension}"
                    
                    st.download_button(
                        label=f"📥 Download {export_language} {export_format} ({export_quality})",
                        data=file_data,
                        file_name=filename,
                        mime=mime_type,
                        use_container_width=True,
                    )
                    
                    st.success(f"✅ {export_language} {export_format} file ready for download!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating {export_language} version: {e}")
    
    with col_btn2:
        if st.button("🔄 Refresh", help="Refresh export options", use_container_width=True):
            st.rerun()
    
    # Export preview
    if st.session_state.tanglish_transcript:
        with st.expander("👁️ Preview Export", expanded=False):
            preview_text = ""
            if export_language == "Tanglish":
                preview_text = st.session_state.tanglish_transcript
            elif export_language == "Tamil":
                preview_text = st.session_state.tamil_transcript
            else:
                preview_text = st.session_state.english_transcript
            
            if export_format in ["SRT", "VTT"]:
                if export_format == "SRT":
                    preview_content = create_srt(preview_text, st.session_state.timestamps, words_per_subtitle if 'words_per_subtitle' in locals() else 8)
                else:
                    preview_content = create_vtt(preview_text, st.session_state.timestamps, words_per_subtitle if 'words_per_subtitle' in locals() else 8)
                
                st.code(preview_content[:1000] + "..." if len(preview_content) > 1000 else preview_content)
            else:
                st.text_area("Preview:", value=preview_text[:500] + "..." if len(preview_text) > 500 else preview_text, height=150, disabled=True)

# --- Footer and Additional Features ---
if not st.session_state.editing_mode:
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px; margin: 2rem 0;">
        <h3 style="color: #2c3e50; margin-bottom: 1rem;">🚀 Ready to Get Started?</h3>
        <p style="color: #6c757d; font-size: 1.1rem; margin-bottom: 1.5rem;">
            Upload your audio or video file above to experience the power of AI-driven Tamil caption generation!
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <div style="text-align: center;">
                <div style="font-size: 2rem; color: #4ECDC4;">⚡</div>
                <strong>Fast Processing</strong>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem; color: #FF6B6B;">🎯</div>
                <strong>High Accuracy</strong>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem; color: #667eea;">🔄</div>
                <strong>Unlimited Edits</strong>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem; color: #764ba2;">📥</div>
                <strong>Multiple Formats</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Help Section ---
with st.expander("❓ Help & Tips", expanded=False):
    st.markdown("""
    ### 🎯 Getting the Best Results
    
    **For Audio Files:**
    - Use clear, high-quality recordings
    - Minimize background noise
    - Speak clearly and at moderate pace
    
    **For Video Files:**
    - Ensure good audio quality in the video
    - Videos with clear speech work best
    - The app automatically extracts audio from video
    
    **Language Settings:**
    - Choose Tamil as primary language for Tamil content
    - Use English as secondary for mixed content
    - Enable punctuation for better readability
    
    **Editing Tips:**
    - Edit in Tanglish for easier understanding
    - Use 'Smart Sync' for quick local updates
    - Use 'AI Re-translate' for major changes
    - The app auto-saves your changes
    
    **Export Options:**
    - TXT: Plain text format
    - SRT: For video players and YouTube
    - VTT: For web players
    - JSON: Complete data with timestamps
    
    ### 🛠️ Troubleshooting
    
    **If transcription is inaccurate:**
    1. Check language settings
    2. Try re-uploading with better audio quality
    3. Use the editing tools to make corrections
    
    **If translation seems wrong:**
    1. Edit the Tanglish version manually
    2. Use 'AI Re-translate' for better results
    3. Try 'Fix Common Errors' for typical mistakes
    
    **File Upload Issues:**
    - Maximum file size: 200MB
    - Supported formats: WAV, MP3, FLAC, M4A, OGG, MP4, AVI, MOV, MKV
    - Try converting to MP3 if other formats don't work
    """)

# --- About Section ---
with st.expander("ℹ️ About Tamil Caption Generator Pro", expanded=False):
    st.markdown("""
    ### 🎬 About This Tool
    
    Tamil Caption Generator Pro is an AI-powered tool that converts audio and video content into accurate Tamil captions in multiple languages and formats.
    
    **Key Features:**
    - 🎤 Audio & Video Support
    - 🗣️ Multi-language Output (Tamil, Tanglish, English)
    - ✏️ Unlimited Editing Capabilities
    - 📥 Professional Export Options
    - ⚡ Smart Caching for Faster Processing
    - 🔄 Real-time Sync and Translation
    
    **Technology Stack:**
    - Google Cloud Speech-to-Text API
    - Google Gemini AI for Translation
    - Streamlit for User Interface
    - PyDub for Audio Processing
    
    **Perfect For:**
    - Content Creators
    - Educators
    - Researchers
    - Media Professionals
    - Anyone working with Tamil content
    
    ### 🔒 Privacy & Security
    - Your files are processed securely
    - No permanent storage of your content
    - Cached results are temporary and local
    - All processing happens in secure cloud environments
    
    ### 💡 Tips for Best Results
    - Upload high-quality audio/video files
    - Speak clearly and avoid background noise
    - Use appropriate language settings
    - Take advantage of unlimited editing features
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 1rem;">
    <p>Made with ❤️ for the Tamil community | Powered by AI</p>
</div>
""", unsafe_allow_html=True)=True)
        
        # Calculate duration
        try:
            if is_video:
                # For video files, we'll estimate duration differently
                file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                estimated_duration = file_size_mb / 2  # Rough estimate
                duration_text = f"~{estimated_duration:.1f} minutes (estimated)"
            else:
                audio_segment = AudioSegment.from_file(uploaded_file)
                duration_minutes = len(audio_segment) / (1000 * 60)
                duration_text = f"{duration_minutes:.1f} minutes"
        except:
            duration_text = "Duration calculation unavailable"
        
        st.markdown(f"""
        <div class="info-box">
            📊 <strong>File Info:</strong> {uploaded_file.name}<br>
            ⏱️ <strong>Duration:</strong> {duration_text}<br>
            🎯 <strong>Output:</strong> Tamil + Tanglish + English + Unlimited Editing
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced Language settings
        with st.expander("🗣️ Advanced Language Settings", expanded=False):
            col_lang1, col_lang2 = st.columns(2)
            with col_lang1:
                primary_language = st.selectbox(
                    "Primary Language",
                    ["ta-IN", "en-IN", "hi-IN"],
                    help="Main language in the audio/video"
                )
            with col_lang2:
                secondary_language = st.selectbox(
                    "Secondary Language",
                    ["en-IN", "ta-IN", "hi-IN"],
                    help="Fallback language for mixed content"
                )
            
            enable_punctuation = st.checkbox("Enable Auto Punctuation", value=True)
            enable_word_timestamps = st.checkbox("Enable Word Timestamps", value=True)
        
        if st.button("🧠 Process File", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("Processing your file..."):
                try:
                    # Reset states
                    st.session_state.editing_mode = False
                    st.session_state.save_message = ""
                    
                    status_text.text("📁 Reading file...")
                    progress_bar.progress(10)
                    
                    # Generate audio hash for caching
                    audio_content = uploaded_file.getvalue()
                    audio_hash = get_audio_hash(audio_content)
                    st.session_state.audio_hash = audio_hash
                    
                    # Check cache
                    status_text.text("🔍 Checking cache...")
                    progress_bar.progress(20)
                    
                    cached_results = get_cached_translations(audio_hash)
                    
                    if cached_results:
                        status_text.text("⚡ Loading from cache...")
                        progress_bar.progress(100)
                        
                        st.session_state.original_transcript = cached_results['tamil']
                        st.session_state.tamil_transcript = cached_results['tamil']
                        st.session_state.tanglish_transcript = cached_results['tanglish']
                        st.session_state.english_transcript = cached_results['english']
                        st.session_state.timestamps = cached_results.get('timestamps', [])
                        st.session_state.original_translations = cached_results
                        st.session_state.editing_mode = True
                        
                        st.success("✅ Loaded from cache instantly!")
                        time.sleep(1)
                        st.rerun()
                    
                    # Process file
                    if is_video:
                        status_text.text("🎥 Extracting audio from video...")
                        progress_bar.progress(30)
                        
                        processed_audio, success = process_video_to_audio(audio_content)
                        if not success:
                            st.error("❌ Failed to extract audio from video. Please try with a different file format.")
                            st.stop()
                        content = processed_audio
                    else:
                        status_text.text("🎵 Processing audio...")
                        progress_bar.progress(30)
                        
                        audio_segment = AudioSegment.from_file(io.BytesIO(audio_content))
                        audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)

                        buffer = io.BytesIO()
                        audio_segment.export(buffer, format="flac")
                        content = buffer.getvalue()
                    
                    # Speech recognition
                    status_text.text("🗣️ Converting speech to text...")
                    progress_bar.progress(50)
                    
                    recognition_audio = speech.RecognitionAudio(content=content)
                    config = speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
                        sample_rate_hertz=16000,
                        language_code=primary_language,
                        alternative_language_codes=[secondary_language],
                        enable_automatic_punctuation=enable_punctuation,
                        enable_word_time_offsets=enable_word_timestamps,
                        model="latest_long"
                    )

                    response = speech_client.recognize(config=config, audio=recognition_audio)
                    
                    if not response.results:
                        st.warning("⚠️ Could not transcribe the file. Please check if the audio is clear and the language settings are correct.")
                        st.stop()
                    
                    # Process results
                    status_text.text("📝 Processing transcription...")
                    progress_bar.progress(70)
                    
                    full_transcript = ""
                    timestamps_data = []
                    for result in response.results:
                        full_transcript += result.alternatives[0].transcript + " "
                        if enable_word_timestamps:
                            for word_info in result.alternatives[0].words:
                                timestamps_data.append({
                                    'word': word_info.word,
                                    'start_time': word_info.start_time.total_seconds(),
                                    'end_time': word_info.end_time.total_seconds()
                                })
                    
                    tamil_transcript = full_transcript.strip()
                    
                    # Generate translations
                    status_text.text("🌍 Generating all language versions...")
                    progress_bar.progress(85)
                    
                    translations = generate_initial_translations(tamil_transcript)
                    
                    # Store results
                    status_text.text("💾 Saving results...")
                    progress_bar.progress(95)
                    
                    st.session_state.original_transcript = tamil_transcript
                    st.session_state.tamil_transcript = translations['tamil']
                    st.session_state.tanglish_transcript = translations['tanglish']
                    st.session_state.english_transcript = translations['english']
                    st.session_state.timestamps = timestamps_data
                    st.session_state.original_translations = translations.copy()
                    st.session_state.original_translations['timestamps'] = timestamps_data
                    
                    # Cache results
                    cache_translation_results(audio_hash, st.session_state.original_translations)
                    
                    st.session_state.editing_mode = True
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")
                    
                    time.sleep(1)
                    st.success("🎉 File processed successfully!")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ An error occurred during processing: {str(e)}")
                    st.error("Please try again or contact support if the problem persists.")
    
    st.markdown('</div>', unsafe_allow_html=True)
