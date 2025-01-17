import streamlit as st
import twitchio
import requests
import asyncio
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor

# Streamlit configuration
st.set_page_config(page_title="Twitch Chat TTS Bot", page_icon="🤖")

# Streamlit UI elements
st.title("Twitch Chat to Speech Bot")

# Sidebar for configuration
with st.sidebar:
    twitch_channel = st.text_input("Twitch Channel Name", "")
    twitch_oauth = st.text_input("Twitch OAuth Token", type="password")
    elevenlabs_api_key = st.text_input("ElevenLabs API Key", type="password")
    voice_id = st.text_input("ElevenLabs Voice ID", "21m00Tcm4TlvDq8ikWAM")
    trigger_word = st.text_input("Trigger Word (e.g., !tts)", "!tts")

# Main chat display area
chat_container = st.empty()
messages = []

class TwitchBot(twitchio.Client):
    def __init__(self, token: str, trigger: str):
        super().__init__(token=token)
        self.trigger = trigger
        self.executor = ThreadPoolExecutor(max_workers=1)

    async def event_ready(self):
        st.success(f"Bot is ready! Connected to Twitch as {self.nick}")
        await self.join_channels([twitch_channel])

    async def event_message(self, message):
        if message.content.startswith(self.trigger):
            # Extract the message content after the trigger
            tts_text = message.content[len(self.trigger):].strip()
            
            if tts_text:
                # Add message to display
                timestamp = datetime.now().strftime("%H:%M:%S")
                messages.append(f"{timestamp} - {message.author.name}: {tts_text}")
                
                # Keep only last 10 messages
                if len(messages) > 10:
                    messages.pop(0)
                
                # Update chat display
                chat_display = "\n".join(messages)
                chat_container.text_area("Recent TTS Messages", chat_display, height=200)
                
                # Convert to speech using ElevenLabs
                self.executor.submit(
                    self.generate_speech,
                    tts_text
                )

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
                # Save audio to temp file
                temp_file = "temp_audio.mp3"
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                
                # Play audio using streamlit
                st.audio(temp_file)
                
                # Clean up temp file
                os.remove(temp_file)
            else:
                st.error(f"Error generating speech: {response.status_code}")

        except Exception as e:
            st.error(f"Error: {str(e)}")

async def main():
    if not all([twitch_channel, twitch_oauth, elevenlabs_api_key]):
        st.warning("Please fill in all required fields in the sidebar.")
        return
    
    bot = TwitchBot(twitch_oauth, trigger_word)
    await bot.connect()

if __name__ == "__main__":
    if st.button("Start Bot"):
        asyncio.run(main())