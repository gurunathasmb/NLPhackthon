import streamlit as st
import whisper
import torch
from pyttsx3 import init as tts_init
import sounddevice as sd
import soundfile as sf
import numpy as np
import datetime
import json
import os
from pathlib import Path
import tempfile

# Set page configuration
st.set_page_config(
    page_title="NeuroPulse Speech Processor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for cyberpunk theme
def inject_custom_css():
    st.markdown("""
        <style>
        /* Main background and text colors */
        .stApp {
            background: linear-gradient(45deg, #000428, #004e92);
            color: #00ff9d;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #00ff9d !important;
            text-shadow: 0 0 10px #00ff9d80;
            font-family: 'Orbitron', sans-serif;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(45deg, #00ff9d, #00b8ff);
            color: black;
            border: none;
            border-radius: 5px;
            box-shadow: 0 0 15px #00ff9d40;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 25px #00ff9d60;
        }
        
        /* Text areas and input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: #001428;
            color: #00ff9d;
            border: 1px solid #00ff9d40;
            border-radius: 5px;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #000428;
        }
        
        /* Cards for history */
        .history-card {
            background: rgba(0, 20, 40, 0.7);
            border: 1px solid #00ff9d40;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 0 15px #00ff9d20;
        }

        /* Progress bar */
        .stProgress > div > div > div > div {
            background-color: #00ff9d;
        }
        </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_whisper_model():
    """Load Whisper model with caching"""
    model = whisper.load_model("base")
    return model

# Initialize text-to-speech engine
def init_tts():
    engine = tts_init()
    return engine

# Speech to text conversion using Whisper
def speech_to_text(audio_path, model):
    try:
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        return f"Error in transcription: {str(e)}"

# Text to speech conversion
def text_to_speech(text, engine):
    temp_file = "temp_speech.wav"
    engine.save_to_file(text, temp_file)
    engine.runAndWait()
    return temp_file

# Save to history
def save_to_history(text, conversion_type):
    history_file = "conversion_history.json"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {
        "timestamp": timestamp,
        "text": text,
        "type": conversion_type
    }
    
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            history = json.load(f)
    else:
        history = []
    
    history.append(new_entry)
    with open(history_file, 'w') as f:
        json.dump(history, f)

def main():
    inject_custom_css()
    
    st.title("💫 NeuroPulse Speech Processor")
    st.markdown("---")

    # Load Whisper model
    with st.spinner("Loading Whisper model..."):
        model = load_whisper_model()
    
    # Initialize TTS engine
    engine = init_tts()
    
    # Sidebar for history and model settings
    st.sidebar.title("🕒 Conversion History")
    
    # Model settings
    st.sidebar.title("⚙️ Settings")
    language = st.sidebar.selectbox(
        "Select Language",
        ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Chinese", "Japanese"],
        index=0
    )
    
    # History display
    if os.path.exists("conversion_history.json"):
        with open("conversion_history.json", 'r') as f:
            history = json.load(f)
        for entry in reversed(history[-5:]):
            with st.sidebar.container():
                st.markdown(f"""
                <div class="history-card">
                    <p><strong>Time:</strong> {entry['timestamp']}</p>
                    <p><strong>Type:</strong> {entry['type']}</p>
                    <p><strong>Text:</strong> {entry['text'][:50]}...</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🎤 Speech to Text")
        uploaded_file = st.file_uploader("Upload audio file", type=['wav', 'mp3', 'm4a', 'flac'])
        
        if st.button("Record Audio"):
            with st.spinner("🔴 Recording... (5 seconds)"):
                audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
                sd.wait()
                sf.write("temp_recording.wav", audio_data, 16000)
                st.success("Recording completed!")
            
        if uploaded_file is not None or os.path.exists("temp_recording.wav"):
            with st.spinner("Transcribing audio..."):
                if uploaded_file:
                    # Save uploaded file to temporary location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        audio_path = tmp_file.name
                else:
                    audio_path = "temp_recording.wav"
                
                text = speech_to_text(audio_path, model)
                st.text_area("Transcribed Text:", text, height=200)
                save_to_history(text, "Speech to Text")
                
                # Clean up temporary file
                if uploaded_file:
                    os.unlink(audio_path)
    
    with col2:
        st.header("🔊 Text to Speech")
        input_text = st.text_area("Enter text to convert to speech:", height=200)
        
        if st.button("Convert to Speech"):
            if input_text:
                with st.spinner("Generating audio..."):
                    audio_file = text_to_speech(input_text, engine)
                    with open(audio_file, "rb") as f:
                        audio_bytes = f.read()
                    st.audio(audio_bytes, format="audio/wav")
                    save_to_history(input_text, "Text to Speech")
                    os.remove(audio_file)

if __name__ == "__main__":
    main()