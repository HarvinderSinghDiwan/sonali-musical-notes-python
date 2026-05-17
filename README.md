# Sonali Musical Notes

**Transform any song into Indian classical harmonium notation with AI-powered vocal isolation and note detection.**

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

## What is this?

Sonali Musical Notes is a web application that takes any song (MP3, MP4, WAV, or YouTube URL) and automatically generates real-time harmonium notation using Indian classical swaras (Sa, Re, Ga, Ma, Pa, Dha, Ni). Watch a virtual harmonium keyboard light up in sync with the vocals as the song plays.

## Screenshots

### Upload Page
- Beautiful red/gold themed UI with tabla and harmonium background
- Drag & drop file upload
- Scale/tonic selector
- YouTube URL input

### Player Page
- Real-time harmonium keyboard visualization
- Large swara display with glow effects
- Playback controls with speed adjustment
- Stats showing tonic, total notes, and progress

## How It Works Internally

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Upload Audio  │────▶│  Vocal Isolation │────▶│ Note Detection  │
│   (Flask API)   │     │   (Spleeter AI)  │     │  (Basic Pitch)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Real-time Player│◀────│  Swara Mapping  │◀────│   MIDI Notes    │
│  (JavaScript)   │     │ (Sa=Tonic based)│     │   with Timing   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Processing Pipeline

1. **Audio Input**: User uploads MP3/MP4/WAV file or provides YouTube URL
2. **Audio Conversion**: FFmpeg converts input to WAV format (44.1kHz, stereo)
3. **Vocal Isolation**: Spleeter AI (by Deezer) separates vocals from instruments using deep learning
4. **Pitch Detection**: Basic Pitch (by Spotify) uses a neural network to detect musical notes from the isolated vocals
5. **Swara Mapping**: MIDI notes are converted to Indian swaras relative to the detected or user-selected tonic (Sa)
6. **Visualization**: Browser plays the isolated vocals while JavaScript highlights corresponding keys on a virtual harmonium

### AI Models Used

| Model | Provider | Purpose |
|-------|----------|---------|
| **Spleeter** | Deezer | Vocal/instrument separation using U-Net architecture trained on 25,000+ songs |
| **Basic Pitch** | Spotify | Polyphonic pitch detection using lightweight neural network |

### Technology Stack

- **Backend**: Python 3.10, Flask
- **AI/ML**: TensorFlow 2.9, Spleeter 2.4, Basic Pitch 0.4
- **Audio Processing**: FFmpeg, librosa, NumPy
- **Frontend**: Vanilla JavaScript, CSS3 animations
- **Container**: Docker with Python slim base image

## Features

- Upload MP3, MP4, WAV, M4A, FLAC audio files
- YouTube URL support (may be blocked by YouTube)
- AI-powered vocal isolation from background music
- Accurate pitch detection from vocals
- Real-time harmonium keyboard visualization
- Indian classical notation (Sa, Re, Ga, Ma, Pa, Dha, Ni)
- Support for Komal (flat) and Tivra (sharp) swaras
- Manual or auto-detect scale/tonic selection
- Playback speed control (0.5x, 0.75x, 1x, 1.25x)
- Beautiful red/gold themed UI with tabla/harmonium background
- 3-octave keyboard display (Mandra, Madhya, Taar)

## Quick Start

### Run with Docker

```bash
# Pull and run
docker run -d -p 5000:5000 --name sonali singhharvin/sonali-musical-notes-python:v1.1

# Open in browser
http://localhost:5000
```

### Run with Persistent Storage

```bash
docker run -d -p 5000:5000 \
  -v sonali-uploads:/app/webapp/uploads \
  -v sonali-processed:/app/webapp/processed \
  --name sonali singhharvin/sonali-musical-notes-python:v1.1
```

### Docker Compose

```yaml
version: '3.8'
services:
  sonali:
    image: singhharvin/sonali-musical-notes-python:v1.1
    ports:
      - "5000:5000"
    volumes:
      - uploads:/app/webapp/uploads
      - processed:/app/webapp/processed
    restart: unless-stopped

volumes:
  uploads:
  processed:
```

### Build from Source

```bash
# Clone the repository
git clone https://github.com/singhharvin/sonali-musical-notes-python.git
cd sonali-musical-notes

# Build Docker image
docker build -t sonali-musical-notes .

# Run
docker run -d -p 5000:5000 --name sonali sonali-musical-notes
```

### Run without Docker

```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask numpy<2 spleeter basic-pitch yt-dlp
pip install typer>=0.9.0 --upgrade

# Install FFmpeg (Ubuntu/Debian)
sudo apt-get install ffmpeg libsndfile1

# Run the app
cd webapp
python app.py
```

## How to Use

1. **Open the app** at http://localhost:5000

2. **Upload a song**: Drag & drop or click to browse (MP3, MP4, WAV, M4A, FLAC)

3. **Select scale** (optional): Choose the tonic note (Sa) or leave on "Auto Detect"

4. **Wait for processing**:
   - Vocal separation: 1-3 minutes
   - Note detection: 1-2 minutes

5. **View the player**:
   - Press Play to start
   - Watch the harmonium keys light up in real-time
   - The large swara display shows the current note

6. **Controls**:
   - Skip forward/backward: -10s, -5s, +5s, +10s
   - Speed: 0.5x (slow practice), 0.75x, 1x, 1.25x

## Indian Classical Notation Guide

| Swara | Hindi | Western Equivalent | Type |
|-------|-------|-------------------|------|
| Sa | सा | Tonic (C/D/E etc.) | Shuddha |
| re | रे॒ | Minor 2nd | Komal |
| Re | रे | Major 2nd | Shuddha |
| ga | ग॒ | Minor 3rd | Komal |
| Ga | ग | Major 3rd | Shuddha |
| Ma | म | Perfect 4th | Shuddha |
| Ma' | म॑ | Augmented 4th | Tivra |
| Pa | प | Perfect 5th | Shuddha |
| dha | ध॒ | Minor 6th | Komal |
| Dha | ध | Major 6th | Shuddha |
| ni | नि॒ | Minor 7th | Komal |
| Ni | नि | Major 7th | Shuddha |

### Octave Notation

- **Mandra Saptak** (Lower octave): Sa. Re. Ga. etc. (dot below)
- **Madhya Saptak** (Middle octave): Sa Re Ga etc. (no marking)
- **Taar Saptak** (Upper octave): Sa' Re' Ga' etc. (apostrophe/dot above)

## Project Structure

```
sonali-musical-notes/
├── Dockerfile
├── README.md
├── requirements.txt
├── .dockerignore
└── webapp/
    ├── app.py              # Flask backend
    ├── templates/
    │   ├── index.html      # Upload page
    │   └── player.html     # Visualization player
    ├── uploads/            # Uploaded files (runtime)
    └── processed/          # Processed results (runtime)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page (upload form) |
| `/upload` | POST | Upload file or YouTube URL |
| `/status/<job_id>` | GET | Check processing status |
| `/player/<job_id>` | GET | Player page with visualization |
| `/audio/<job_id>` | GET | Stream processed vocals |

## System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 5GB for image + space for uploads
- **Port**: 5000 (configurable)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_APP` | `webapp/app.py` | Flask application path |
| `PYTHONUNBUFFERED` | `1` | Python output buffering |

### Ports

| Port | Description |
|------|-------------|
| 5000 | HTTP web interface |

### Volumes

| Path | Description |
|------|-------------|
| `/app/webapp/uploads` | Uploaded audio files |
| `/app/webapp/processed` | Processed results and vocals |

## Limitations

- Processing time depends on song length (typically 2-5 minutes)
- YouTube downloads may be blocked due to bot detection
- Works best with clear vocal tracks
- Accuracy depends on audio quality and vocal clarity
- First run downloads Spleeter models (~100MB)
- Not suitable for AWS Lambda (use ECS/App Runner instead)

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs sonali

# Ensure port 5000 is free
lsof -i :5000
```

### Processing fails
- Ensure the audio file is not corrupted
- Try a different format (MP3 works best)
- Check container has enough memory (4GB+)

### YouTube download fails
- YouTube actively blocks automated downloads
- Download the song manually and upload the file instead

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - Free to use and modify.

## Credits

- **Spleeter**: [Deezer Research](https://github.com/deezer/spleeter) - Vocal separation
- **Basic Pitch**: [Spotify Research](https://github.com/spotify/basic-pitch) - Pitch detection
- **FFmpeg**: Audio processing
- **Flask**: Web framework
- **TensorFlow**: ML framework

## Acknowledgments

Built with love for Indian Classical Music lovers. This tool is designed to help musicians learn and practice harmonium by visualizing the notes of their favorite songs.

---

**Tags**: `harmonium` `indian-classical-music` `swaras` `notation` `vocal-isolation` `pitch-detection` `music-transcription` `flask` `tensorflow` `spleeter`
