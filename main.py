import os
import streamlit as st
import asyncio
from twitchio.ext import commands
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# Load environment variables
load_dotenv()
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
TWITCH_TOKEN = os.getenv('TWITCH_TOKEN')  # Ensure this is set in your .env file

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=TWITCH_TOKEN, prefix='!', initial_channels=['gameplayer0618'])

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        if message.author.name.lower() == 'gameplayer0618':
            print(f"Message from StreamElements received: {message.content}")
            await self.text_to_speech(message.content)

    async def text_to_speech(self, text):
        try:
            audio_generator = client.text_to_speech.convert(
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                output_format="mp3_44100_128",
                text=text,
                model_id="eleven_multilingual_v2",
            )
            with open('output.mp3', 'wb') as audio_file:
                for chunk in audio_generator:
                    audio_file.write(chunk)
            print("Audio generated successfully.")
        except Exception as e:
            print(f"Error generating audio: {e}")

def run_bot():
    bot = Bot()
    asyncio.run(bot.start())  # Use asyncio.run to start the bot

# Streamlit UI
st.title("Twitch Bot with Text-to-Speech")

if st.button("Start Bot"):
    # Start the bot
    run_bot()  # This will block the Streamlit app; use carefully
    st.success("Bot started! Check console for messages.")

