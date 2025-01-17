import os
import requests
import asyncio
import threading
import streamlit as st
from twitchio.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Load your ElevenLabs API key from the environment variable
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token='c95ap3chzt6x3lnc0gc5r691hgegof', prefix='!', initial_channels=['sutsuno'])
        self.messages = []

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        # Ignore messages from the bot itself
        if message.author.name.lower() == self.nick.lower():
            return

        # Check if the message is from StreamElements
        if message.author.name.lower() == 'streamelements':
            self.messages.append(message.content)
            asyncio.create_task(self.text_to_speech(message.content))  # Run TTS task asynchronously

    async def text_to_speech(self, text):
        url = "https://api.elevenlabs.io/v1/text-to-speech/generate"
        headers = {
            'Authorization': f'Bearer {ELEVENLABS_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            "text": text,
            "voice": "your_voice_choice"  # Specify the voice you want to use
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            audio_content = response.content
            with open('output.mp3', 'wb') as audio_file:
                audio_file.write(audio_content)
            print("Audio generated successfully.")
        else:
            print(f"Error: {response.status_code} - {response.text}")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = Bot()
    loop.run_until_complete(bot.run())

# Streamlit UI
st.title("Twitch Chat Reader")
st.write("Listening for messages from StreamElements...")

if 'bot_thread' not in st.session_state:
    st.session_state.bot_thread = None

if st.button("Start Bot"):
    if st.session_state.bot_thread is None or not st.session_state.bot_thread.is_alive():
        # Start the bot in a separate thread
        st.session_state.bot_thread = threading.Thread(target=run_bot, daemon=True)
        st.session_state.bot_thread.start()
        st.success("Bot has started!")
    else:
        st.warning("Bot is already running!")

st.write("Messages:")
# Messages from the bot can be displayed using session state or Streamlit's experimental features
