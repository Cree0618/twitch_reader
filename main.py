import os
import requests
import queue
import threading
from twitchio.ext import commands
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
import streamlit as st

# Load environment variables
load_dotenv()
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

message_queue = queue.Queue()
# Function to initialize and run the bot
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token='llfzk70gvunu5z5iwwfq5bakcnc04s', prefix='!', initial_channels=['gameplayer0618'])

    async def event_ready(self):
        message_queue.put(f"Logged in as: {self.nick}")
        print(f"Logged in as | {self.nick}")

    async def event_message(self, message):
        # Ignore messages from the bot itself
        # if message.author.name.lower() == self.nick.lower(): #     return
        # Check if the message is from the target user
        if message.author.name.lower() == 'gameplayer0618':
            message_queue.put(f"Received message: {message.content}")
            print(f"Message from {message.author.name}: {message.content}")
            await self.text_to_speech(message.content)

    async def text_to_speech(self, text):
        try:
            # Generate audio using ElevenLabs API
            audio_generator = client.text_to_speech.convert(
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                output_format="mp3_44100_128",
                text=text,
                model_id="eleven_multilingual_v2",
            )
            with open('output.mp3', 'wb') as audio_file:
                for chunk in audio_generator:
                    audio_file.write(chunk)
            message_queue.put("Audio generated successfully.")
            
        except Exception as e:
            message_queue.put(f"Error generating audio: {e}")
            

def run_bot_in_thread():
    """
    Run the bot in a separate thread to avoid blocking Streamlit's main execution.
    """
    bot = Bot()
    bot.run()

# Streamlit UI
st.title("Twitch Bot with Text-to-Speech")

if st.button("Start Bot"):
    st.write("Starting Twitch bot...")
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()
    st.success("Bot is running in the background!")
    
st.write("### Bot Logs")
while True:
    try:
        log_message = message_queue.get_nowait()
        st.write(log_message)
    except queue.Empty:
        break
