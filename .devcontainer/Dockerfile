FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

# Install system deps (ffmpeg, xvfb, chromium)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    xvfb \
    chromium \
    chromium-driver \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
