import os
import asyncio
import threading
import time
import pyaudio

from dotenv import load_dotenv, find_dotenv
from deepgram import DeepgramClient
from deepgram.core.events import EventType
from groq import Groq


# --------------------------------------------------
# ENV SETUP
# --------------------------------------------------
load_dotenv(find_dotenv())

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --------------------------------------------------
# AUDIO CONFIG
# --------------------------------------------------
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 2560

# --------------------------------------------------
# LLM CONFIG
# --------------------------------------------------
LLM_MODEL = "llama-3.3-70b-versatile"
DEBOUNCE_SECONDS = 0.4   # how often LLM is triggered

#  catching scripts text

catche_txt = {}

if not catche_txt.get("text"):
    with open("script.txt", "r") as file:
        script = file.read()
        catche_txt["text"] = script

# --------------------------------------------------
# CLIENT
# --------------------------------------------------
class RealtimeAssistant:
    def __init__(self, loop):
        self.loop = loop

        # Deepgram
        self.dg = DeepgramClient(api_key=DEEPGRAM_API_KEY)

        # Groq
        self.groq = Groq(api_key=GROQ_API_KEY)

        # Audio
        self.audio = None
        self.stream = None

        # Sync
        self.ready = threading.Event()

        # Transcript state
        self.latest_transcript = ""
        self.last_emit_time = 0

        # Async queue
        self.llm_queue = asyncio.Queue()
        self.llm_task = None

    # --------------------------------------------------
    # AUDIO
    # --------------------------------------------------
    def setup_audio(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

    def cleanup_audio(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

    # --------------------------------------------------
    # DEEPGRAM EVENTS
    # --------------------------------------------------
    def on_open(self, *_):
        print("\n🎤 Connected to Deepgram\n")
        self.ready.set()

    def on_message(self, result):

        transcript = getattr(result, "transcript", None)

        _Event_ = getattr(result, "event", None)

        

        if not transcript:
            return
            
        # Send transcript to asyncio loop when the sst finishes its conversion

        if _Event_ == "EndOfTurn":
            print("last Script :",self.latest_transcript,"")
            asyncio.run_coroutine_threadsafe(
            self.llm_queue.put(transcript),
            self.loop,
        )

        self.latest_transcript = transcript

        now = time.time()
        if now - self.last_emit_time < DEBOUNCE_SECONDS:
            return

        self.last_emit_time = now

        
        

    def on_error(self, err):
        print("\n[Deepgram Error]", err)

    def on_close(self, *_):
        print("\n🔌 Deepgram connection closed")

    # --------------------------------------------------
    # AUDIO STREAM THREAD
    # --------------------------------------------------
    def stream_audio(self, connection):
        self.ready.wait()
        while True:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            connection.send_media(data)

    # --------------------------------------------------
    # GROQ STREAMING LLM
    # --------------------------------------------------
    async def stream_llm(self, text):
        print("\n🤖 LLM:", end=" ", flush=True)

        try:
            stream = self.groq.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                            {
                                "role": "user",
                                "content": f"response :{text} \n instruction :{catche_txt.get('text', ' ')}"
                            }
                        ],
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="", flush=True)
                    await asyncio.sleep(0)

            print("\n")

        except asyncio.CancelledError:
            print("\n⛔ LLM cancelled\n")
            raise

    # --------------------------------------------------
    # ORCHESTRATOR
    # --------------------------------------------------
    async def llm_orchestrator(self):
        while True:
            text = await self.llm_queue.get()

            # cancel previous task
            if self.llm_task and not self.llm_task.done():
                self.llm_task.cancel()
                try:
                    await self.llm_task
                except asyncio.CancelledError:
                    pass

            self.llm_task = asyncio.create_task(self.stream_llm(text))

    # --------------------------------------------------
    # START
    # --------------------------------------------------
    def start(self):
        self.setup_audio()

        with self.dg.listen.v2.connect(
            model="flux-general-en",
            encoding="linear16",
            sample_rate=RATE,
            eot_threshold=0.7,
            eot_timeout_ms=5000
        ) as connection:

            connection.on(EventType.OPEN, self.on_open)
            connection.on(EventType.MESSAGE, self.on_message)
            connection.on(EventType.ERROR, self.on_error)
            connection.on(EventType.CLOSE, self.on_close)

            audio_thread = threading.Thread(
                target=self.stream_audio,
                args=(connection,),
                daemon=True,
            )
            audio_thread.start()

            connection.start_listening()

# --------------------------------------------------
# MAIN
# --------------------------------------------------
async def main():
    loop = asyncio.get_running_loop()
    assistant = RealtimeAssistant(loop)

    orchestrator_task = asyncio.create_task(assistant.llm_orchestrator())

    try:
        await asyncio.to_thread(assistant.start)
    finally:
        orchestrator_task.cancel()
        assistant.cleanup_audio()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
