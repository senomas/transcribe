import sys
import yt_dlp
import os
import whisper
import openai
from pydub import AudioSegment


def download_audio(youtube_url):
    options = {
        "format": "bestaudio/best",
        "outtmpl": "/app/tmp/output",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    options["cookiefile"] = "cookie.txt"

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([youtube_url])


def convert_to_wav(mp3_file, wav_file):
    audio = AudioSegment.from_mp3(mp3_file)
    audio.export(wav_file, format="wav")


def transcribe_audio(wav_file):
    model = whisper.load_model(os.getenv("WHISPER_MODEL"))
    result = model.transcribe(wav_file, fp16=False)
    return result["text"]


def summarize_text(text):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is not None:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Summarize the following text in a clear, structured Markdown bullet-point format (like Logseq). Use concise phrases.",
                },
                {"role": "user", "content": text},
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    raise Exception("OPENAI_API_KEY not set")


def read_text_from_file(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} not found")
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python app.py <YouTube_URL>")
        sys.exit(1)

    url = sys.argv[1]

    if not os.path.exists("/app/data/output.wav"):
        print("Downloading audio...")
        download_audio(url)

        print("Converting to WAV...")
        convert_to_wav("/app/tmp/output.mp3", "/app/data/output.wav")

    if not os.path.exists("/app/data/transcript.txt"):
        print("Transcribing audio...")
        transcript = transcribe_audio("/app/data/output.wav")
        with open("/app/data/transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript)

    if not os.path.exists("/app/data/summary.txt"):
        print("Summarizing text...")
        transcript = read_text_from_file("/app/data/transcript.txt")
        summary = summarize_text(transcript)
        print(summary)
        with open("/app/data/summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)
