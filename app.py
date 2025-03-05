import os
from fastrtc import ReplyOnPause, Stream, get_stt_model, get_tts_model
from fastapi import FastAPI, WebSocket, Request
from ollama import Client

# Define configuration variables
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL_NAME = os.getenv('OLLAMA_MODEL_NAME', 'llama3.2')

SYSTEM_MESSAGE = """You are a voice assistant that can help with anything you need.
Keep the converation more humorous and engaging.

- Maintain a fun, lighthearted vibe—say things like “Umm...”, “Well...”, or “I mean...” 
- Keep responses concise, as it's a voice conversation—avoid long monologues.
"""


# Initialize FastAPI app
app = FastAPI()

# Initialize STT and TTS models
stt_model = get_stt_model()
tts_model = get_tts_model()
# Initialize Ollama client
client = Client(
    host=OLLAMA_URL,
    headers={'x-some-header': 'some-value'}
)

# Define the echo function that will be used to handle incoming audio
def echo(audio):
    prompt = stt_model.stt(audio)

    response = client.chat(
            model=OLLAMA_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt}
            ]
        )
    
    response_text = response['message']['content']

    for audio_chunk in tts_model.stream_tts_sync(response_text):
        yield audio_chunk

# Initialize the Media Stream
stream = Stream(ReplyOnPause(echo), modality="audio", mode="send-receive")


# Define the root route for the FastAPI app
@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = await stream.handle_incoming_call(request)
    return response


# Define the handler route for Media Stream
@app.websocket("/telephone/handler")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and Media Stream."""
    await stream.telephone_handler(websocket)
