# Dockerfile — запускає Dash app, chromium, ffmpeg; встановлює основні python-залежності.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget git build-essential \
    python3 python3-venv python3-pip ffmpeg xvfb \
    chromium-browser gnupg2 libglib2.0-0 libnss3 libx11-6 libxss1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# venv (we'll use system python pip inside container)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# copy project files
COPY . /app

# upgrade pip and install python deps
RUN pip install --upgrade pip

# Note: install torch (cpu) via official PyTorch index for CPU wheels.
# If you want GPU support, replace with appropriate CUDA wheel and base image.
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision --no-cache-dir || true

# install other python deps
RUN pip install -r /app/requirements.txt

# make starter executable
RUN chmod +x /app/start_stream.sh

EXPOSE 8050
ENTRYPOINT ["/app/start_stream.sh"]
