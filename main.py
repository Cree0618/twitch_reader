import os
import requests
from twitchio.ext import commands
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from threading import Lock

# Load environment variables
load_dotenv()
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
TWITCH_ACCESS_TOKEN = os.getenv('TWITCH_ACCESS_TOKEN')
# Initialize ElevenLabs client with the API key
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Create a lock for thread-safe access to shared resources
audio_generation_lock = Lock()

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=TWITCH_ACCESS_TOKEN, prefix='!', initial_channels=['gameplayer0618'])

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        # Ignore messages from the bot itself
        if message.author.name.lower() == self.nick.lower():
            return
        
        # Check if the message is from StreamElements (replace 'gameplayer0618' with the correct name)
        if message.author.name.lower() == 'gameplayer0618':
            print(f"Message from StreamElements received: {message.content}")
            
            # Delegate text-to-speech generation to a separate thread
            await self.loop.run_in_executor(None, self.text_to_speech, message.content)

    def text_to_speech(self, text):
        """
        Converts text to speech using ElevenLabs API in a thread-safe manner.
        """
        with audio_generation_lock:  # Acquire lock for thread safety
            try:
                # Generate audio using ElevenLabs API
                audio_generator = client.text_to_speech.convert(
                    voice_id="JBFqnCBsd6RMkjVDRZzb",
                    output_format="mp3_44100_128",
                    text=text,
                    model_id="eleven_multilingual_v2",
                )
                # Save audio to a file
                with open('output.mp3', 'wb') as audio_file:
                    for chunk in audio_generator:
                        audio_file.write(chunk)
                print("Audio generated successfully.")
            except Exception as e:
                print(f"Error generating audio: {e}")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
