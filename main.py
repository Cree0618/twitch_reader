import streamlit as st
from twitchio.ext import commands
import requests
import asyncio
import nest_asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import atexit
from queue import Queue
import threading

# Enable nested event loops
nest_asyncio.apply()

# Create a queue for audio files
if 'audio_queue' not in st.session_state:
    st.session_state.audio_queue = Queue()

# Streamlit configuration
st.set_page_config(page_title="Twitch TTS Bot", page_icon="🤖")
st.title("Twitch TTS Bot")

# Configuration inputs
with st.sidebar:
    twitch_channel = st.text_input("Twitch Channel Name", "")
    access_token = st.text_input("Twitch Access Token", type="password", help="Enter your Twitch access token without the 'oauth:' prefix")
    elevenlabs_api_key = st.text_input("ElevenLabs API Key", type="password")
    voice_id = st.text_input("ElevenLabs Voice ID", "21m00Tcm4TlvDq8ikWAM")
    trigger_word = st.text_input("Trigger Word (e.g., !tts)", "!tts")

# Status indicator placeholder
status_placeholder = st.empty()

# Audio player placeholder
audio_placeholder = st.empty()

class Bot(commands.Bot):
    def __init__(self):
        # Add 'oauth:' prefix to the access token if it's not already there
        token = f"oauth:{access_token}" if not access_token.startswith("oauth:") else access_token
        
        super().__init__(
            token=token,
            prefix='!',
            initial_channels=[twitch_channel]
        )
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._running = True

    async def event_ready(self):
        print(f'Bot is running in channel: {twitch_channel}')

    async def event_message(self, ctx):
        if not self._running or ctx.echo:
            return

        if ctx.content.startswith(trigger_word):
            tts_text = ctx.content[len(trigger_word):].strip()
            if tts_text:
                self.executor.submit(self.generate_speech, tts_text)

    def generate_speech(self, text):
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": elevenlabs_api_key
            }

            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }

            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Put the audio data in the queue
                st.session_state.audio_queue.put(response.content)
            else:
                print("TTS API Error")

        except Exception as e:
            print(f"Error generating speech: {str(e)}")

    async def close(self):
        self._running = False
        self.executor.shutdown(wait=False)
        await super().close()

def init_asyncio_patch():
    """Create new event loop and set it as the default for the thread"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def run_bot():
    if not all([twitch_channel, access_token, elevenlabs_api_key]):
        st.warning("Please fill in all required fields in the sidebar.")
        return

    try:
        # Initialize asyncio loop
        loop = init_asyncio_patch()
        
        # Create and run bot
        bot = Bot()
        st.session_state.bot = bot
        
        # Run the bot using the event loop
        loop.run_until_complete(bot.start())
    except Exception as e:
        print(f"Bot error: {str(e)}")
    finally:
        if hasattr(st.session_state, 'bot'):
            loop.run_until_complete(st.session_state.bot.close())
            loop.close()

def cleanup():
    if hasattr(st.session_state, 'bot') and st.session_state.bot is not None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(st.session_state.bot.close())
        loop.close()

# Register the cleanup function
atexit.register(cleanup)

# Bot control
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False

if st.button("Start Bot", disabled=st.session_state.bot_running):
    st.session_state.bot_running = True
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    status_placeholder.success("Bot is running")

if st.button("Stop Bot", disabled=not st.session_state.bot_running):
    st.session_state.bot_running = False
    cleanup()
    status_placeholder.warning("Bot stopped")
    st.experimental_rerun()

# Audio player loop
if st.session_state.bot_running:
    try:
        # Check for new audio in the queue
        if not st.session_state.audio_queue.empty():
            audio_data = st.session_state.audio_queue.get()
            # Save temporary file
            temp_file = "temp_audio.mp3"
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            # Play audio
            audio_placeholder.audio(temp_file)
            # Clean up
            os.remove(temp_file)
    except Exception as e:
        print(f"Error playing audio: {str(e)}")