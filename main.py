import sys
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop
sys.modules['pyaudioop'] = audioop

import streamlit as st
from google.cloud import speech
import google.generativeai as genai
import os
import io
import json
import re
from datetime import timedelta
from pydub import AudioSegment

# Page config
st.set_page_config(
    page_title="Tamil Caption Generator",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .feature-box {
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #E1E5E9;
        margin: 1rem 0;
        background: #F8F9FA;
    }
    .transcript-box {
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #28A745;
        background: #F8FFF8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🗣️ Tamil + Tanglish Caption Generator</h1>
    <p>Upload audio → Get captions → Edit → Translate → Export SRT</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Keys (using secrets)
    st.subheader("🔑 API Configuration")
    google_creds = st.text_area(
        "Google Cloud Credentials (JSON)", 
        help="Paste your Google Cloud service account JSON here",
        type="password"
    )
    
    gemini_api_key = st.text_input(
        "Gemini API Key", 
        type="password",
        help="Get from Google AI Studio"
    )
    
    # Language settings
    st.subheader("🗣️ Language Settings")
    primary_language = st.selectbox(
        "Primary Language",
        ["ta-IN", "en-IN", "hi-IN"],
        help="Main language for transcription"
    )
    
    secondary_language = st.selectbox(
        "Secondary Language", 
        ["en-IN", "ta-IN", "hi-IN"],
        help="Fallback language"
    )

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'edited_transcript' not in st.session_state:
    st.session_state.edited_transcript = ""
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = []
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📤 Upload Audio")
    uploaded_file = st.file_uploader(
        "Choose your audio file", 
        type=["wav", "mp3", "flac", "m4a", "ogg"],
        help="Supports most audio formats"
    )
    
    if uploaded_file:
        st.audio(uploaded_file)
        
        # Audio processing options
        st.subheader("🎛️ Audio Settings")
        audio_duration = st.slider("Max Duration (seconds)", 10, 300, 60)
        
        if st.button("🧠 Transcribe Audio", type="primary"):
            if not google_creds:
                st.error("Please add Google Cloud credentials in the sidebar!")
            else:
                try:
                    # Setup Google credentials
                    credentials_dict = json.loads(google_creds)
                    with open('temp_creds.json', 'w') as f:
                        json.dump(credentials_dict, f)
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "temp_creds.json"
                    
                    # Process audio
                    with st.spinner("Processing audio..."):
                        audio_bytes = uploaded_file.read()
                        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
                        
                        # Trim if too long
                        if len(audio) > audio_duration * 1000:
                            audio = audio[:audio_duration * 1000]
                        
                        # Optimize for Google API
                        audio = audio.set_frame_rate(16000).set_channels(1)
                        flac_audio = io.BytesIO()
                        audio.export(flac_audio, format="flac")
                    
                    # Google Speech-to-Text
                    with st.spinner("Transcribing with Google AI..."):
                        client = speech.SpeechClient()
                        
                        # Enhanced config for better accuracy
                        config = speech.RecognitionConfig(
                            encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
                            sample_rate_hertz=16000,
                            language_code=primary_language,
                            alternative_language_codes=[secondary_language],
                            enable_automatic_punctuation=True,
                            enable_word_time_offsets=True,  # For SRT timing
                            model="latest_long"
                        )
                        
                        response = client.recognize(
                            config=config,
                            audio=speech.RecognitionAudio(content=flac_audio.getvalue())
                        )
                        
                        if response.results:
                            # Extract transcript and timestamps
                            full_transcript = ""
                            timestamps = []
                            
                            for result in response.results:
                                full_transcript += result.alternatives[0].transcript + " "
                                
                                # Extract word-level timestamps
                                for word_info in result.alternatives[0].words:
                                    timestamps.append({
                                        'word': word_info.word,
                                        'start_time': word_info.start_time.total_seconds(),
                                        'end_time': word_info.end_time.total_seconds()
                                    })
                            
                            st.session_state.transcript = full_transcript.strip()
                            st.session_state.edited_transcript = full_transcript.strip()
                            st.session_state.timestamps = timestamps
                            
                            st.success("✅ Transcription completed!")
                            
                            # Clean up temp file
                            if os.path.exists('temp_creds.json'):
                                os.remove('temp_creds.json')
                        else:
                            st.error("No transcription returned. Try with clearer audio.")
                            
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    if os.path.exists('temp_creds.json'):
                        os.remove('temp_creds.json')

with col2:
    st.header("📝 Results & Editing")
    
    if st.session_state.transcript:
        # Original transcript
        st.subheader("🎯 Original Transcript")
        st.markdown(f'<div class="transcript-box">{st.session_state.transcript}</div>', 
                   unsafe_allow_html=True)
        
        # Editable transcript
        st.subheader("✏️ Edit Transcript")
        st.session_state.edited_transcript = st.text_area(
            "Edit your transcript:",
            value=st.session_state.edited_transcript,
            height=150,
            help="Make corrections to improve accuracy"
        )
        
        # Translation section
        st.subheader("🌍 Translation")
        col_trans1, col_trans2 = st.columns(2)
        
        with col_trans1:
            if st.button("Tamil → Tanglish"):
                if gemini_api_key:
                    try:
                        genai.configure(api_key=gemini_api_key)
                        model = genai.GenerativeModel('gemini-pro')
                        
                        prompt = f"""
                        Convert this Tamil text to Tanglish (Tamil written in English letters):
                        
                        Text: {st.session_state.edited_transcript}
                        
                        Rules:
                        1. Keep English words as English
                        2. Convert Tamil words to English phonetic spelling
                        3. Make it readable for English speakers
                        4. Keep the same meaning
                        """
                        
                        response = model.generate_content(prompt)
                        st.session_state.translated_text = response.text
                        
                    except Exception as e:
                        st.error(f"Translation error: {str(e)}")
                else:
                    st.error("Please add Gemini API key in sidebar!")
        
        with col_trans2:
            if st.button("Tamil → English"):
                if gemini_api_key:
                    try:
                        genai.configure(api_key=gemini_api_key)
                        model = genai.GenerativeModel('gemini-pro')
                        
                        prompt = f"""
                        Translate this Tamil/Tanglish text to clear English:
                        
                        Text: {st.session_state.edited_transcript}
                        
                        Provide a natural English translation that preserves the original meaning.
                        """
                        
                        response = model.generate_content(prompt)
                        st.session_state.translated_text = response.text
                        
                    except Exception as e:
                        st.error(f"Translation error: {str(e)}")
                else:
                    st.error("Please add Gemini API key in sidebar!")
        
        # Show translation result
        if st.session_state.translated_text:
            st.subheader("🔄 Translation Result")
            st.markdown(f'<div class="transcript-box">{st.session_state.translated_text}</div>', 
                       unsafe_allow_html=True)

# Export section
if st.session_state.edited_transcript:
    st.header("📥 Export Options")
    
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        # Plain text export
        st.download_button(
            label="📄 Download TXT",
            data=st.session_state.edited_transcript,
            file_name="transcript.txt",
            mime="text/plain"
        )
    
    with col_exp2:
        # JSON export with timestamps
        if st.session_state.timestamps:
            json_data = {
                "transcript": st.session_state.edited_transcript,
                "timestamps": st.session_state.timestamps,
                "translation": st.session_state.translated_text
            }
            
            st.download_button(
                label="📊 Download JSON",
                data=json.dumps(json_data, indent=2),
                file_name="transcript_data.json",
                mime="application/json"
            )
    
    with col_exp3:
        # SRT export
        if st.session_state.timestamps:
            def create_srt():
                srt_content = ""
                words = st.session_state.edited_transcript.split()
                timestamps = st.session_state.timestamps
                
                # Group words into subtitle chunks (8-10 words per subtitle)
                chunk_size = 8
                for i in range(0, len(words), chunk_size):
                    chunk_words = words[i:i+chunk_size]
                    
                    if i < len(timestamps):
                        start_time = timestamps[i]['start_time']
                        end_idx = min(i + chunk_size - 1, len(timestamps) - 1)
                        end_time = timestamps[end_idx]['end_time']
                        
                        # Format time for SRT
                        def format_time(seconds):
                            td = timedelta(seconds=seconds)
                            hours = int(td.total_seconds() // 3600)
                            minutes = int((td.total_seconds() % 3600) // 60)
                            seconds = td.total_seconds() % 60
                            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')
                        
                        subtitle_num = (i // chunk_size) + 1
                        srt_content += f"{subtitle_num}\n"
                        srt_content += f"{format_time(start_time)} --> {format_time(end_time)}\n"
                        srt_content += f"{' '.join(chunk_words)}\n\n"
                
                return srt_content
            
            srt_data = create_srt()
            st.download_button(
                label="🎬 Download SRT",
                data=srt_data,
                file_name="subtitles.srt",
                mime="text/plain"
            )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>Built with ❤️ using Streamlit, Google Cloud Speech-to-Text & Gemini AI</p>
    <p>🚀 <strong>Next steps:</strong> Add more languages, batch processing, and video support!</p>
</div>
""", unsafe_allow_html=True)
