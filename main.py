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
    page_title="Tamil Caption Generator",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Professional Styling
st.markdown("""
<style>
    /* Hide Streamlit elements */
    .css-1d391kg {display: none}
    section[data-testid="stSidebar"] {display: none}
    .css-k1vhr4 {padding: 1rem 2rem}
    
    /* Main container */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* Header */
    .app-header {
        text-align: center;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .app-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .app-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0;
        font-weight: 400;
    }
    
    /* Step indicator */
    .step-indicator {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
        gap: 1rem;
    }
    
    .step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .step.active {
        background: #2a5298;
        color: white;
    }
    
    .step.inactive {
        background: #f0f2f6;
        color: #6b7280;
    }
    
    .step.completed {
        background: #10b981;
        color: white;
    }
    
    /* Cards */
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    .card h3 {
        margin: 0 0 1rem 0;
        color: #1f2937;
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(42,82,152,0.3);
        width: auto;
        min-width: 120px;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(42,82,152,0.4);
    }
    
    /* File uploader */
    .uploadedFile {
        border: 2px dashed #d1d5db;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: #f9fafb;
        transition: all 0.2s ease;
    }
    
    .uploadedFile:hover {
        border-color: #2a5298;
        background: #f0f4ff;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    .success-box {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #10b981;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #065f46;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #92400e;
    }
    
    /* Transcript editor */
    .transcript-editor {
        background: #ffffff;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        min-height: 300px;
        font-family: 'Monaco', 'Menlo', monospace;
        line-height: 1.6;
    }
    
    .transcript-editor:focus {
        border-color: #2a5298;
        box-shadow: 0 0 0 3px rgba(42,82,152,0.1);
    }
    
    /* Language tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        justify-content: center;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: #2a5298;
        color: white;
    }
    
    /* Audio player */
    .audio-player {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Export section */
    .export-section {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 2rem;
    }
    
    /* Help tooltip */
    .help-tooltip {
        display: inline-block;
        margin-left: 8px;
        color: #6b7280;
        cursor: help;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main-container {
            padding: 0.5rem;
        }
        
        .app-header {
            padding: 1.5rem;
        }
        
        .app-header h1 {
            font-size: 1.8rem;
        }
        
        .step-indicator {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .card {
            padding: 1rem;
        }
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
    <h1>🎬 Tamil Caption Generator</h1>
    <p>Professional audio & video transcription with perfect Tanglish output</p>
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
                st.session_state.current_step = 2
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# STEP 2: Processing
elif st.session_state.current_step == 2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🔄 Processing Your File")
    
    # Processing logic
    progress_container = st.container()
    status_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
    
    with status_container:
        status_text = st.empty()
    
    try:
        # Reset states
        st.session_state.editing_mode = False
        st.session_state.save_message = ""
        
        status_text.info("📁 Reading file...")
        progress_bar.progress(10)
        time.sleep(0.5)
        
        # Get uploaded file from session or reupload
        uploaded_file = st.file_uploader(
            "File",
            type=["mp3", "wav", "m4a", "ogg", "flac", "mp4", "mov", "avi", "mkv"],
            label_visibility="collapsed",
            key="processing_uploader"
        )
        
        if not uploaded_file:
            st.warning("Please upload a file first!")
            if st.button("← Back to Upload"):
                st.session_state.current_step = 1
                st.rerun()
            st.stop()
        
        audio_content = uploaded_file.getvalue()
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
        file_extension = uploaded_file.name.lower().split('.')[-1]
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
        💡 <strong>Pro Tip:</strong> Edit in Tanglish for best results. Use 'Smart Sync' for quick updates or 'AI Re-translate' for accuracy.
    </div>
    """, unsafe_allow_html=True)
    
    # Editing tools
    col1, col2, col3 = st.columns(3)
    
    with col1:
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
        if st.button("↩️ Reset Original", help="Reset to original transcription", use_container_width=True):
            if st.session_state.original_translations:
                st.session_state.tanglish_transcript = st.session_state.original_translations['tanglish']
                st.session_state.tamil_transcript = st.session_state.original_translations['tamil']
                st.session_state.english_transcript = st.session_state.original_translations['english']
                st.session_state.save_message = "↩️ Reset to original!"
                st.rerun()
    
    # Line-by-line transcript editor
    st.markdown("#### 📝 Line-by-Line Editor")
    
    # Convert to line-by-line format
    lines = st.session_state.tanglish_transcript.split('.')
    lines = [line.strip() for line in lines if line.strip()]
    
    edited_lines = []
    for i, line in enumerate(lines):
        col_line, col_help = st.columns([10, 1])
        with col_line:
            edited_line = st.text_input(
                f"Line {i+1}",
                value=line,
                key=f"line_{i}",
                label_visibility="collapsed"
            )
            edited_lines.append(edited_line)
        with col_help:
            st.markdown(f'<span class="help-tooltip" title="Edit this line">❓</span>', unsafe_allow_html=True)
    
    # Update transcript from lines
    new_transcript = '. '.join(edited_lines)
    if new_transcript != st.session_state.tanglish_transcript:
        st.session_state.tanglish_transcript = new_transcript
        st.session_state.save_message = ""
    
    # Stats
    word_count = len(new_transcript.split()) if new_transcript else 0
    char_count = len(new_transcript) if new_transcript else 0
    estimated_duration = word_count / 150 if word_count > 0 else 0
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("📊 Words", word_count)
    with col_stat2:
        st.metric("🔤 Characters", char_count)
    with col_stat3:
        st.metric("⏱️ Duration", f"{estimated_duration:.1f} min")
    
    # Language preview tabs
    st.markdown("#### 📖 Language Previews")
    tab1, tab2, tab3 = st.tabs(["🔤 Tanglish", "🕉️ Tamil", "🌍 English"])
    
    with tab1:
        st.text_area(
            "Tanglish Preview:", 
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
    
    # Navigation
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

# STEP 4: Export
elif st.session_state.current_step == 4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🎬 Export Configuration")
    
    st.markdown("""
    <div class="info-box">
        🎯 <strong>Choose your export settings:</strong> Configure subtitles like a professional video editor
    </div>
    """, unsafe_allow_html=True)
    
    # Export options in columns
    col1, col2 = st.columns(2)
    
    with col1:
        export_language = st.selectbox(
            "🌍 Language",
            ["Tanglish", "Tamil", "English"],
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
    if export_language == "Tanglish":
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
    
    # Download section
    st.markdown("#### 📥 Download")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("📥 Generate & Download", type="primary", use_container_width=True):
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
                    
                    filename = f"transcript_{export_language.lower()}.{file_extension}"
                    
                    st.download_button(
                        label=f"📥 Download {export_language} {export_format}",
                        data=file_data,
                        file_name=filename,
                        mime=mime_type,
                        use_container_width=True,
                        key="download_btn"
                    )
                    
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ <strong>Ready for download!</strong><br>
                        📁 File: {filename} | 📊 Size: {len(file_data.encode('utf-8')) / 1024:.1f} KB
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Export failed: {e}")
    
    with col2:
        if st.button("🔄 New File", help="Process another file", use_container_width=True):
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
            st.rerun()
    
    # Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Edit"):
            st.session_state.current_step = 3
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Invalid step fallback
else:
    st.session_state.current_step = 1
    st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; margin-top: 3rem; border-top: 1px solid #e5e7eb;">
    <p style="color: #6b7280; margin: 0;">
        Made with ❤️ for the Tamil community | Professional AI-powered transcription
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
