import streamlit as st
from twitchio.ext import commands
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import atexit

# Streamlit configuration
st.set_page_config(page_title="Twitch TTS Bot", page_icon="🤖")
st.title("Twitch TTS Bot")

# Configuration inputs
with st.sidebar:
    twitch_channel = st.text_input("Twitch Channel Name", "")
    twitch_oauth = st.text_input("Twitch OAuth Token", type="password")
    elevenlabs_api_key = st.text_input("ElevenLabs API Key", type="password")
    voice_id = st.text_input("ElevenLabs Voice ID", "21m00Tcm4TlvDq8ikWAM")
    trigger_word = st.text_input("Trigger Word (e.g., !tts)", "!tts")

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=twitch_oauth,
            prefix='!',
            initial_channels=[twitch_channel]
        )
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._running = True

    async def event_ready(self):
        st.success(f'Bot is running in channel: {twitch_channel}')

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
                temp_file = "temp_audio.mp3"
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                st.audio(temp_file)
                os.remove(temp_file)
            else:
                st.error("TTS API Error")

        except Exception as e:
            st.error("Error generating speech")

    async def close(self):
        self._running = False
        self.executor.shutdown(wait=False)
        await super().close()

def run_bot():
    if not all([twitch_channel, twitch_oauth, elevenlabs_api_key]):
        st.warning("Please fill in all required fields in the sidebar.")
        return

    try:
        bot = Bot()
        st.session_state.bot = bot
        bot.run()
    except Exception as e:
        st.error(f"Bot error: {str(e)}")
    finally:
        if hasattr(st.session_state, 'bot'):
            asyncio.run(st.session_state.bot.close())

if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False

def cleanup():
    if hasattr(st.session_state, 'bot') and st.session_state.bot is not None:
        asyncio.run(st.session_state.bot.close())

atexit.register(cleanup)

if __name__ == "__main__":
    if st.button("Start Bot", disabled=st.session_state.bot_running):
        st.session_state.bot_running = True
        run_bot()
    
    if st.button("Stop Bot", disabled=not st.session_state.bot_running):
        st.session_state.bot_running = False
        cleanup()
        st.experimental_rerun()