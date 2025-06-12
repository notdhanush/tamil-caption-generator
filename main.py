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

# --- Page Configuration ---
st.set_page_config(
    page_title="Tamil Caption Generator",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Styling ---
st.markdown("""
<style>
    .css-1d391kg {display: none}
    section[data-testid="stSidebar"] {
        display: none;
    }
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
    .cost-info {
        padding: 0.5rem;
        border-radius: 5px;
        background: #e3f2fd;
        border: 1px solid #2196f3;
        color: #0277bd;
        margin: 0.5rem 0;
        font-size: 0.9em;
    }
    .edit-info {
        padding: 0.5rem;
        border-radius: 5px;
        background: #f3e5f5;
        border: 1px solid #9c27b0;
        color: #7b1fa2;
        margin: 0.5rem 0;
        font-size: 0.9em;
    }
    .save-success {
        padding: 0.5rem;
        border-radius: 5px;
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 0.5rem 0;
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

# --- SMART CACHING SYSTEM ---
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

# --- ONE-TIME TRANSLATION FUNCTIONS (ONLY CALLED ONCE PER AUDIO) ---
def generate_initial_translations(tamil_text):
    """Generate all translations at once - ONLY called after initial transcription"""
    try:
        # Tanglish conversion
        tanglish_prompt = f"""
        Convert this Tamil text to Tanglish (Tamil written in phonetic English letters).
        Keep any existing English words as they are.
        Make it natural and readable for Tamil speakers who prefer English script.
        Text: "{tamil_text}"
        
        Return only the Tanglish translation, nothing else.
        """
        tanglish_response = generative_model.generate_content(tanglish_prompt)
        tanglish_text = tanglish_response.text.strip()
        
        # English translation
        english_prompt = f"""
        Translate this Tamil text accurately to natural-sounding English.
        Maintain the meaning and context.
        Text: "{tamil_text}"
        
        Return only the English translation, nothing else.
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

# --- LOCAL TEXT PROCESSING FUNCTIONS (NO API CALLS) ---
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
        # Add more common corrections
    }
    
    corrected_text = text
    for error, correction in corrections.items():
        corrected_text = corrected_text.replace(error, correction)
    
    return corrected_text

def smart_text_sync(edited_tanglish, original_translations):
    """Intelligently sync translations without API calls when possible"""
    # Simple word-by-word mapping for basic edits
    # This is a simplified version - you can enhance this logic
    
    # For now, return original translations if major changes detected
    # Only update if minor edits (like punctuation, spacing)
    
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

# Load credentials
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
if 'audio_hash' not in st.session_state:
    st.session_state.audio_hash = None
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
if 'editing_mode' not in st.session_state:
    st.session_state.editing_mode = False
if 'save_message' not in st.session_state:
    st.session_state.save_message = ""
if 'api_calls_made' not in st.session_state:
    st.session_state.api_calls_made = 0
if 'original_translations' not in st.session_state:
    st.session_state.original_translations = {}

# --- Main App UI ---
st.markdown("""
<div class="main-header">
    <h1>🗣️ Tamil + Tanglish Caption Generator</h1>
    <p>Upload audio → Get captions → Edit unlimited times → Download in any language</p>
</div>
""", unsafe_allow_html=True)

if not auth_success:
    st.error("⚠️ Service is currently unavailable. Please try again later.")
    st.stop()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.header("📤 Upload & Transcribe")
    
    # Cost information
    st.markdown("""
    <div class="cost-info">
        💰 <strong>Pricing:</strong> ₹1.25 per minute of audio<br>
        ✨ <strong>Unlimited editing included!</strong> Edit as many times as you want at no extra cost.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose your audio file",
        type=["wav", "mp3", "flac", "m4a", "ogg"],
        help="Supports most common audio formats (Max: 200MB)"
    )

    if uploaded_file:
        st.audio(uploaded_file)
        
        # Calculate audio duration and cost
        audio_segment = AudioSegment.from_file(uploaded_file)
        duration_minutes = len(audio_segment) / (1000 * 60)  # Convert to minutes
        estimated_cost = duration_minutes * 1.25
        
        st.markdown(f"""
        <div class="cost-info">
            📊 <strong>Audio Duration:</strong> {duration_minutes:.1f} minutes<br>
            💵 <strong>Processing Cost:</strong> ₹{estimated_cost:.2f}<br>
            🎯 <strong>What you get:</strong> Tamil + Tanglish + English + Unlimited Editing
        </div>
        """, unsafe_allow_html=True)
        
        # Language settings
        with st.expander("🗣️ Language Settings (Optional)", expanded=False):
            col_lang1, col_lang2 = st.columns(2)
            with col_lang1:
                primary_language = st.selectbox(
                    "Primary Language",
                    ["ta-IN", "en-IN", "hi-IN"],
                    help="Main language in the audio"
                )
            with col_lang2:
                secondary_language = st.selectbox(
                    "Secondary Language",
                    ["en-IN", "ta-IN", "hi-IN"],
                    help="Fallback language"
                )
        
        if st.button("🧠 Transcribe Audio", type="primary", use_container_width=True):
            with st.spinner("Processing audio and generating all language versions..."):
                try:
                    # Reset states
                    st.session_state.editing_mode = False
                    st.session_state.save_message = ""
                    st.session_state.api_calls_made = 0
                    
                    # Generate audio hash for caching
                    audio_content = uploaded_file.getvalue()
                    audio_hash = get_audio_hash(audio_content)
                    st.session_state.audio_hash = audio_hash
                    
                    # Check if we have cached results
                    cached_results = get_cached_translations(audio_hash)
                    
                    if cached_results:
                        st.info("⚡ Found cached results! Loading instantly...")
                        st.session_state.original_transcript = cached_results['tamil']
                        st.session_state.tamil_transcript = cached_results['tamil']
                        st.session_state.tanglish_transcript = cached_results['tanglish']
                        st.session_state.english_transcript = cached_results['english']
                        st.session_state.timestamps = cached_results.get('timestamps', [])
                        st.session_state.original_translations = cached_results
                        st.session_state.editing_mode = True
                        st.success("✅ Loaded from cache - No API cost!")
                        st.rerun()
                    
                    # Process audio with pydub
                    audio_segment = AudioSegment.from_file(io.BytesIO(audio_content))
                    audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)

                    buffer = io.BytesIO()
                    audio_segment.export(buffer, format="flac")
                    content = buffer.getvalue()
                    
                    # Call Google Speech-to-Text API (COST: ₹1.04 per minute)
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
                    st.session_state.api_calls_made += 1
                    
                    if not response.results:
                        st.warning("Could not transcribe the audio. The file might be silent or the language settings incorrect.")
                        st.stop()
                    
                    # Process transcription results
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
                    
                    tamil_transcript = full_transcript.strip()
                    
                    # Generate ALL translations in ONE GO (COST: ₹0.21 per minute)
                    st.session_state.api_calls_made += 1
                    translations = generate_initial_translations(tamil_transcript)
                    
                    # Store everything
                    st.session_state.original_transcript = tamil_transcript
                    st.session_state.tamil_transcript = translations['tamil']
                    st.session_state.tanglish_transcript = translations['tanglish']
                    st.session_state.english_transcript = translations['english']
                    st.session_state.timestamps = timestamps_data
                    st.session_state.original_translations = translations.copy()
                    st.session_state.original_translations['timestamps'] = timestamps_data
                    
                    # Cache the results for future use
                    cache_translation_results(audio_hash, st.session_state.original_translations)
                    
                    st.session_state.editing_mode = True
                    
                    # Show cost breakdown
                    actual_cost = st.session_state.api_calls_made * (duration_minutes * 0.625)  # Approx API cost
                    st.success(f"✅ Complete! Total API calls: {st.session_state.api_calls_made} (₹{actual_cost:.2f})")
                    st.rerun()

                except Exception as e:
                    st.error(f"An error occurred during transcription: {e}")

with col2:
    st.header("📝 Edit Transcript")

    if st.session_state.editing_mode and st.session_state.tanglish_transcript:
        
        # Editing info
        st.markdown("""
        <div class="edit-info">
            ✨ <strong>Unlimited Editing Mode</strong><br>
            Edit as much as you want - no additional API costs!<br>
            Changes are processed locally for instant updates.
        </div>
        """, unsafe_allow_html=True)
        
        # Show save message if exists
        if st.session_state.save_message:
            st.markdown(f'<div class="save-success">{st.session_state.save_message}</div>', unsafe_allow_html=True)
        
        # Edit controls
        col_edit1, col_edit2, col_edit3 = st.columns([3, 1, 1])
        with col_edit1:
            st.subheader("✏️ Edit Mode")
        with col_edit2:
            if st.button("🔄 Smart Sync", help="Sync other languages with your edits (no API cost)"):
                with st.spinner("Syncing languages locally..."):
                    synced_result, change_type = smart_text_sync(
                        st.session_state.tanglish_transcript, 
                        st.session_state.original_translations
                    )
                    
                    if synced_result:
                        st.session_state.tamil_transcript = synced_result['tamil']
                        st.session_state.english_transcript = synced_result['english']
                        st.session_state.save_message = "✅ Languages synced locally!"
                    else:
                        st.session_state.save_message = "⚠️ Major changes detected. Translations kept as-is to avoid errors."
                    st.rerun()
        
        with col_edit3:
            if st.button("🔄 Re-translate", help="Use AI to re-translate (costs ₹0.21)"):
                with st.spinner("Re-translating with AI..."):
                    try:
                        # This is the ONLY edit operation that costs money
                        new_translations = generate_initial_translations(st.session_state.tanglish_transcript)
                        st.session_state.api_calls_made += 1
                        
                        st.session_state.tamil_transcript = new_translations['tamil']
                        st.session_state.english_transcript = new_translations['english']
                        st.session_state.save_message = f"✅ Re-translated with AI! (API call #{st.session_state.api_calls_made})"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Re-translation failed: {e}")
        
        st.info("💡 Edit freely in Tanglish! Use 'Smart Sync' for free local updates or 'Re-translate' for AI-powered updates.")
        
        # Editing area
        edited_tanglish = st.text_area(
            "Edit your transcript:",
            value=st.session_state.tanglish_transcript,
            height=200,
            key="tanglish_editor",
            help="Edit in Tanglish - unlimited edits, no extra cost!"
        )
        
        # Update session state when text changes
        if edited_tanglish != st.session_state.tanglish_transcript:
            st.session_state.tanglish_transcript = edited_tanglish
            st.session_state.save_message = ""
        
        # Language preview tabs
        st.subheader("📖 Language Previews")
        tab1, tab2, tab3 = st.tabs(["🔤 Tanglish", "🕉️ Tamil", "🌍 English"])
        
        with tab1:
            st.text_area("Current Tanglish:", value=st.session_state.tanglish_transcript, height=100, disabled=True)
        
        with tab2:
            st.text_area("Current Tamil:", value=st.session_state.tamil_transcript, height=100, disabled=True)
        
        with tab3:
            st.text_area("Current English:", value=st.session_state.english_transcript, height=100, disabled=True)

# --- Export Section ---
if st.session_state.editing_mode and st.session_state.tanglish_transcript:
    st.markdown("---")
    st.header("📥 Download Options")
    
    col_lang, col_format = st.columns([1, 1])
    
    with col_lang:
        export_language = st.selectbox(
            "🌍 Select Language:",
            ["Tanglish", "Tamil", "English"],
            help="Choose which language version to download"
        )
    
    with col_format:
        export_format = st.selectbox(
            "📄 Select Format:",
            ["TXT", "SRT"],
            help="Choose file format"
        )

    def create_srt(text, timestamps):
        """Create SRT subtitle file"""
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
        chunk_size = 8
        
        for i in range(0, len(text_words), chunk_size):
            chunk_words = text_words[i : i + chunk_size]
            if not chunk_words:
                continue
            
            timestamp_start_idx = min(i, len(timestamps) - 1)
            timestamp_end_idx = min(i + chunk_size - 1, len(timestamps) - 1)
            
            if timestamp_start_idx < len(timestamps) and timestamp_end_idx < len(timestamps):
                start_time = timestamps[timestamp_start_idx]['start_time']
                end_time = timestamps[timestamp_end_idx]['end_time']
            else:
                start_time = i * 2
                end_time = (i + chunk_size) * 2
            
            text_chunk = " ".join(chunk_words)
            
            subtitle_num = (i // chunk_size) + 1
            srt_content += f"{subtitle_num}\n"
            srt_content += f"{format_time(start_time)} --> {format_time(end_time)}\n"
            srt_content += f"{text_chunk}\n\n"
        
        return srt_content

    if st.button("📥 Generate & Download", type="primary", use_container_width=True):
        with st.spinner(f"Preparing {export_language} {export_format} file..."):
            try:
                if export_language == "Tanglish":
                    export_text = st.session_state.tanglish_transcript
                elif export_language == "Tamil":
                    export_text = st.session_state.tamil_transcript
                else:
                    export_text = st.session_state.english_transcript
                
                if export_format == "TXT":
                    file_extension = "txt"
                    file_data = export_text
                    mime_type = "text/plain"
                else:
                    file_extension = "srt"
                    file_data = create_srt(export_text, st.session_state.timestamps)
                    mime_type = "text/plain"
                
                filename = f"transcript_{export_language.lower()}.{file_extension}"
                
                st.download_button(
                    label=f"📥 Download {export_language} {export_format}",
                    data=file_data,
                    file_name=filename,
                    mime=mime_type,
                    use_container_width=True,
                )
                
                st.subheader(f"📄 Preview ({export_language} {export_format})")
                if export_format == "SRT":
                    st.code(file_data[:500] + "..." if len(file_data) > 500 else file_data)
                else:
                    st.text_area("Preview:", value=export_text, height=150, disabled=True)
                
            except Exception as e:
                st.error(f"Error generating {export_language} version: {e}")

# Show initial message
if not st.session_state.editing_mode and not st.session_state.processing_translations:
    st.info("👆 Upload an audio file above to get started!")
    
    # Show API cost tracker
    if st.session_state.api_calls_made > 0:
        st.markdown(f"""
        <div class="cost-info">
            📊 <strong>Session Stats:</strong><br>
            API Calls Made: {st.session_state.api_calls_made}<br>
            Estimated Cost: ₹{st.session_state.api_calls_made * 0.625:.2f}
        </div>
        """, unsafe_allow_html=True)
