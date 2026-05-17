FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies in correct order to avoid conflicts
# Spleeter needs typer<0.4 but Flask needs click>=8 which conflicts
# Solution: install spleeter first, then upgrade typer
RUN pip install --no-cache-dir "numpy<2" && \
    pip install --no-cache-dir spleeter>=2.4.0 && \
    pip install --no-cache-dir "typer>=0.9.0" --upgrade && \
    pip install --no-cache-dir flask>=2.3.0 basic-pitch>=0.3.0 yt-dlp>=2024.1.0

# Copy application code
COPY webapp/ ./webapp/

# Create directories for uploads and processed files
RUN mkdir -p webapp/uploads webapp/processed

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=webapp/app.py
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "webapp/app.py"]
