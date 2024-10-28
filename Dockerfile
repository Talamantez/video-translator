FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    tesseract-ocr \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python packages and spaCy models
RUN pip install -r requirements.txt && \
    python -m spacy download en_core_web_sm && \
    python -m spacy download fr_core_news_sm && \
    python -m spacy download es_core_news_sm && \
    python -m spacy download de_core_news_sm

# Create necessary directories
RUN mkdir -p output uploads saved_results

# Copy application code
COPY . .

# Environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]