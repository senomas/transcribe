import sys
import yt_dlp
import os
import whisper
import openai
import base64
import re
import time
from urllib.parse import urlparse
from pydub import AudioSegment


def remove_files(file_list):
    for file in file_list:
        if os.path.exists(file):
            os.remove(file)
            print(f"{file} deleted.")
        else:
            print(f"{file} does not exist.")


def cleanup_old_files(directory, days=3):
    """Remove files older than specified days from the directory"""
    current_time = time.time()
    max_age = days * 24 * 60 * 60  # Convert days to seconds

    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age:
                try:
                    os.remove(filepath)
                    print(f"Removed old file: {filename}")
                except Exception as e:
                    print(f"Error removing {filename}: {e}")


def get_safe_filename(url):
    """Generate a safe filename from URL using base64 encoding"""
    # Parse the URL to get the path
    parsed = urlparse(url)
    # Get video ID or last part of path
    path = parsed.path
    if "youtube.com" in url or "youtu.be" in url:
        # Extract video ID from query params or path
        video_id = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11}).*", url)
        if video_id:
            path = video_id.group(1)
    # Encode the path to base64 and make it URL safe
    safe_name = base64.urlsafe_b64encode(path.encode()).decode()
    # Remove any padding = signs and limit length
    safe_name = safe_name.rstrip("=")[:32]
    return safe_name


def download_audio(name, youtube_url):
    options = {
        "format": "bestaudio/best",
        "outtmpl": f"/app/tmp/{name}",
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
            max_tokens=5000,
        )
        return response.choices[0].message.content
    raise Exception("AI API KEY not set")


def gen_instruction(text):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is not None:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Create instruction froom text below in a clear, structured Markdown bullet-point format (like Logseq). Use concise phrases.",
                },
                {"role": "user", "content": text},
            ],
            max_tokens=5000,
        )
        return response.choices[0].message.content
    raise Exception("AI API KEY not set")


def read_text_from_file(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} not found")
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python app.py <YouTube_URL> {len(sys.argv)}")
        sys.exit(1)

    # Clean up old files
    cleanup_old_files("/app/data")

    cmd = sys.argv[1]
    url = sys.argv[2]
    name = get_safe_filename(url)

    if not os.path.exists(f"/app/data/{name}.wav"):
        print("Downloading audio...")
        download_audio(name, url)
        print("Converting to WAV...")
        convert_to_wav(f"/app/tmp/{name}.mp3", f"/app/data/{name}.wav")

    if not os.path.exists(f"/app/data/{name}-transcript.txt"):
        print("Transcribing audio...")
        transcript = transcribe_audio(f"/app/data/{name}.wav")
        with open(f"/app/data/{name}-transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript)

    if not os.path.exists(f"/app/data/{name}.txt"):
        transcript = read_text_from_file(f"/app/data/{name}-transcript.txt")
        if cmd == "instruction":
            print("Generate instructions...")
            summary = gen_instruction(transcript)
        else:
            print("Summarizing text...")
            summary = summarize_text(transcript)
        with open(f"/app/data/{name}.txt", "w", encoding="utf-8") as f:
            f.write(summary)

    result = read_text_from_file(f"/app/data/{name}.txt")
    print(result)
