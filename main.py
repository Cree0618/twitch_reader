import os
import threading
import streamlit as st
import asyncio
from twitchio.ext import commands
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# Load environment variables
load_dotenv()
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token='llfzk70gvunu5z5iwwfq5bakcnc04s', prefix='!', initial_channels=['gameplayer0618'])

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
            return 'output.mp3'  # Return the path of the generated file
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None

def run_bot():
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = Bot()
    loop.run_until_complete(bot.start())  # Use start() instead of run()

# Streamlit UI
st.title("Twitch Bot with Text-to-Speech")

if st.button("Start Bot"):
    # Start the bot in a separate thread
    threading.Thread(target=run_bot, daemon=True).start()
    st.success("Bot started!")

if st.button("Generate TTS"):
    text = st.text_input("Enter text for TTS:")
    if text:
        audio_file_path = asyncio.run(bot.text_to_speech(text))  # Call the TTS function asynchronously
        if audio_file_path:
            st.audio(audio_file_path)  # Play the generated audio file
