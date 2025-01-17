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
            await self.text_to_speech(message.content)

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
    bot = Bot()
    bot.run()

# Streamlit UI
st.title("Twitch Chat Reader")
st.write("Listening for messages from StreamElements...")

if st.button("Start Bot"):
    # Start the bot in a separate thread
    threading.Thread(target=run_bot, daemon=True).start()
    st.success("Bot has started!")

st.write("Messages:")
# Display messages if you want to maintain state (you can implement a way to display messages)
