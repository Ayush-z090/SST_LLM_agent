# Voice Transcription with Deepgram

Real-time audio transcription using PyAudio and Deepgram with Voice Activity Detection (VAD).

## Features

- 🎤 Real-time audio capture from microphone using PyAudio
- 🔊 Streaming transcription to Deepgram API
- 🎯 Voice Activity Detection (VAD) - automatically detects when you stop speaking
- 📝 Prints transcripts each time speech ends (after 1 second of silence)

## Setup

### 1. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

**Note for PyAudio installation:**
- **Windows**: Usually installs directly with pip
- **macOS**: You may need PortAudio first: `brew install portaudio`
- **Linux**: Install system dependencies: `sudo apt-get install portaudio19-dev python3-pyaudio` (Debian/Ubuntu) or equivalent for your distribution

### 2. Get Deepgram API Key

1. Sign up for a free account at [Deepgram Console](https://console.deepgram.com/)
2. Create an API key
3. Set the API key as an environment variable:

   **Windows (PowerShell):**
   ```powershell
   $env:DEEPGRAM_API_KEY="your_api_key_here"
   ```

   **Windows (Command Prompt):**
   ```cmd
   set DEEPGRAM_API_KEY=your_api_key_here
   ```

   **Linux/macOS:**
   ```bash
   export DEEPGRAM_API_KEY="your_api_key_here"
   ```

   Alternatively, you can directly edit `app.py` and replace `'YOUR_DEEPGRAM_API_KEY'` with your actual API key (though using environment variables is more secure).

### 3. Run the Application

```bash
python app.py
```

## Usage

1. Run the application
2. Speak into your microphone
3. When you stop speaking (after ~1 second of silence), the transcript will be printed
4. Press `Ctrl+C` to stop

## Configuration

You can modify the following settings in `app.py`:

- **Audio Format**: Currently set to 16-bit PCM, mono, 16kHz (supported by Deepgram)
- **Endpointing/VAD**: Currently set to 1000ms (1 second) of silence to detect end of speech
- **Model**: Currently using `nova-2` (you can change to `nova`, `base`, etc.)
- **Language**: Currently set to `en-US` (English US)

## How It Works

1. **Audio Capture**: PyAudio captures audio from your microphone in real-time
2. **Streaming**: Audio is sent to Deepgram via WebSocket connection
3. **VAD (Voice Activity Detection)**: Deepgram's endpointing feature detects when you stop speaking (1000ms of silence)
4. **Transcription**: When speech ends, the final transcript is printed

## Troubleshooting

- **"Please set your DEEPGRAM_API_KEY"**: Make sure you've set the API key as an environment variable or edited it in `app.py`
- **Audio errors**: Ensure your microphone is connected and not being used by another application
- **Connection errors**: Check your internet connection and API key validity








