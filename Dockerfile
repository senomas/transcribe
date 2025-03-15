# Use official Python image
FROM python:3.11

# Install system dependencies for ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app


# Create a non-root user
ARG USERNAME=appuser
ARG UID=1000
ARG GID=1000

RUN groupadd --gid $GID $USERNAME && \
  useradd --uid $UID --gid $GID --create-home $USERNAME

# Set the working directory
WORKDIR /app/tmp
WORKDIR /app

# Set permissions for the new user
RUN chown -R $USERNAME:$USERNAME /app

# Switch to non-root user
USER $USERNAME

RUN pip install --no-cache-dir openai-whisper
ARG WHISPER_MODEL=medium
# You can use "tiny", "small", "medium", "large"
ENV WHISPER_MODEL=$WHISPER_MODEL
ENV WHISPER_MODEL_DIR=/models
RUN python -c "import whisper; whisper.load_model('$WHISPER_MODEL')"

COPY --chown=$USERNAME:$USERNAME requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=$USERNAME:$USERNAME cookie.txt .
COPY --chown=$USERNAME:$USERNAME *.py .

ENTRYPOINT ["python", "app.py"]

