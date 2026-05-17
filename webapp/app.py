#!/usr/bin/env python3
"""
Harmonium Notation Web App
Upload audio/video or paste YouTube link to get visual harmonium notation
"""

import os
import json
import uuid
import subprocess
import threading
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory
import numpy as np

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / 'uploads'
PROCESSED_DIR = BASE_DIR / 'processed'

UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# Store processing status
processing_status = {}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
SEMITONE_TO_SWARA = {
    0: 'Sa', 1: 're', 2: 'Re', 3: 'ga', 4: 'Ga', 5: 'Ma',
    6: "Ma'", 7: 'Pa', 8: 'dha', 9: 'Dha', 10: 'ni', 11: 'Ni',
}


def hz_to_midi(freq):
    if freq <= 0:
        return 0
    return 69 + 12 * np.log2(freq / 440.0)


def midi_to_note_name(midi):
    midi_int = int(round(midi))
    octave = (midi_int // 12) - 1
    note = NOTE_NAMES[midi_int % 12]
    return f"{note}{octave}"


NOTE_TO_MIDI = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}

def process_audio(job_id, input_path, is_youtube=False, scale='auto'):
    """Process audio in background thread"""
    try:
        job_dir = PROCESSED_DIR / job_id
        job_dir.mkdir(exist_ok=True)

        processing_status[job_id] = {'status': 'processing', 'step': 'Starting...', 'progress': 0}

        # Step 1: Download YouTube if needed
        if is_youtube:
            processing_status[job_id]['step'] = 'Downloading from YouTube...'
            processing_status[job_id]['progress'] = 10

            output_path = job_dir / 'original.%(ext)s'
            cmd = [
                'yt-dlp', '-x', '--audio-format', 'wav',
                '--audio-quality', '0', '-o', str(output_path), input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                error_msg = result.stderr
                if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
                    processing_status[job_id] = {
                        'status': 'error',
                        'error': '🚫 YouTube is blocking automated downloads (bot detection). Please download the song manually from YouTube and upload the MP3/MP4 file instead.'
                    }
                else:
                    processing_status[job_id] = {
                        'status': 'error',
                        'error': f'YouTube download failed. Please download manually and upload the file.'
                    }
                return

            # Find downloaded file
            audio_file = None
            for f in job_dir.iterdir():
                if f.name.startswith('original.'):
                    audio_file = f
                    break

            if not audio_file:
                processing_status[job_id] = {'status': 'error', 'error': 'Downloaded file not found'}
                return
        else:
            audio_file = Path(input_path)

        # Step 2: Convert to WAV if needed
        processing_status[job_id]['step'] = 'Converting audio...'
        processing_status[job_id]['progress'] = 20

        wav_file = job_dir / 'audio.wav'
        if not str(audio_file).lower().endswith('.wav'):
            cmd = ['ffmpeg', '-y', '-i', str(audio_file), '-ar', '44100', '-ac', '2', str(wav_file)]
            subprocess.run(cmd, capture_output=True, check=True)
        else:
            import shutil
            shutil.copy(audio_file, wav_file)

        # Step 3: Separate vocals using Spleeter
        processing_status[job_id]['step'] = 'Separating vocals (this takes a while)...'
        processing_status[job_id]['progress'] = 30

        separated_dir = job_dir / 'separated'
        separated_dir.mkdir(exist_ok=True)

        try:
            from spleeter.separator import Separator
            separator = Separator('spleeter:2stems')
            separator.separate_to_file(str(wav_file), str(separated_dir))
        except Exception as e:
            processing_status[job_id] = {'status': 'error', 'error': f'Vocal separation failed: {str(e)}'}
            return

        vocals_file = separated_dir / 'audio' / 'vocals.wav'
        if not vocals_file.exists():
            # Try alternate path
            for p in separated_dir.rglob('vocals.wav'):
                vocals_file = p
                break

        if not vocals_file.exists():
            processing_status[job_id] = {'status': 'error', 'error': 'Vocals file not found after separation'}
            return

        # Step 4: Transcribe vocals
        processing_status[job_id]['step'] = 'Transcribing notes from vocals...'
        processing_status[job_id]['progress'] = 60

        # Import here to avoid loading TF at startup
        from basic_pitch.inference import predict

        model_output, midi_data, note_events = predict(str(vocals_file))

        processing_status[job_id]['step'] = 'Processing notes...'
        processing_status[job_id]['progress'] = 80

        # Extract notes with timing
        notes = []
        for event in note_events:
            start_time, end_time, pitch, amplitude, _ = event
            if amplitude > 0.3:  # Filter low confidence
                notes.append({
                    'start': round(float(start_time), 3),
                    'end': round(float(end_time), 3),
                    'midi': int(pitch),
                    'velocity': round(float(amplitude), 2)
                })

        # Detect or set Sa (tonic)
        if scale != 'auto' and scale in NOTE_TO_MIDI:
            # Manual scale selection
            sa_pitch_class = NOTE_TO_MIDI[scale]
            sa_midi = 48 + sa_pitch_class  # Octave 3
            scale_method = 'manual'
        elif notes:
            # Auto-detect from most common pitch
            midi_notes = [n['midi'] for n in notes]
            pitch_classes = [m % 12 for m in midi_notes]
            from collections import Counter
            pc_counts = Counter(pitch_classes)
            most_common_pc = pc_counts.most_common(1)[0][0]
            sa_midi = 48 + most_common_pc
            scale_method = 'auto'
        else:
            sa_midi = 60  # Default C4
            scale_method = 'default'

        # Step 5: Save results
        processing_status[job_id]['step'] = 'Finalizing...'
        processing_status[job_id]['progress'] = 90

        # Copy vocals to processed folder for playback
        final_vocals = job_dir / 'vocals.wav'
        import shutil
        shutil.copy(vocals_file, final_vocals)

        # Save notes data
        result_data = {
            'notes': notes,
            'sa_midi': sa_midi,
            'sa_note': midi_to_note_name(sa_midi),
            'total_notes': len(notes),
            'scale_method': scale_method
        }

        with open(job_dir / 'notes.json', 'w') as f:
            json.dump(result_data, f)

        processing_status[job_id] = {
            'status': 'complete',
            'step': 'Done!',
            'progress': 100,
            'result': result_data
        }

    except Exception as e:
        processing_status[job_id] = {'status': 'error', 'error': str(e)}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    job_id = str(uuid.uuid4())[:8]
    scale = request.form.get('scale', 'auto')

    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        filename = f"{job_id}_{file.filename}"
        filepath = UPLOAD_DIR / filename
        file.save(filepath)

        # Start processing in background
        thread = threading.Thread(target=process_audio, args=(job_id, str(filepath), False, scale))
        thread.start()

        return jsonify({'job_id': job_id, 'status': 'started'})

    elif 'youtube_url' in request.form and request.form['youtube_url']:
        url = request.form['youtube_url']

        # Start processing in background
        thread = threading.Thread(target=process_audio, args=(job_id, url, True, scale))
        thread.start()

        return jsonify({'job_id': job_id, 'status': 'started'})

    return jsonify({'error': 'No file or URL provided'}), 400


@app.route('/status/<job_id>')
def get_status(job_id):
    if job_id in processing_status:
        return jsonify(processing_status[job_id])
    return jsonify({'status': 'unknown', 'error': 'Job not found'}), 404


@app.route('/player/<job_id>')
def player(job_id):
    job_dir = PROCESSED_DIR / job_id
    notes_file = job_dir / 'notes.json'

    if not notes_file.exists():
        return "Processing not complete", 404

    with open(notes_file) as f:
        data = json.load(f)

    return render_template('player.html',
                         job_id=job_id,
                         notes=json.dumps(data['notes']),
                         sa_midi=data['sa_midi'],
                         sa_note=data['sa_note'],
                         total_notes=data['total_notes'])


@app.route('/audio/<job_id>')
def get_audio(job_id):
    job_dir = PROCESSED_DIR / job_id
    return send_from_directory(job_dir, 'vocals.wav')


if __name__ == '__main__':
    print("\n" + "="*55)
    print("  🎹 Sonali Musical Notes")
    print("  Transform any song into harmonium notation")
    print("="*55)
    print("\n  🌐 Open in browser: http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
