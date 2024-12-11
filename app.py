from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from moviepy.audio.io.AudioFileClip import AudioFileClip
import speech_recognition as sr
import os
import uuid
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route("/process", methods=["POST"])
def process_media():
    file_path = None
    audio_path = None

    # Check if a URL is provided
    if "url" in request.form and request.form["url"]:
        video_url = request.form["url"]
        print(f"Processing video URL: {video_url}")
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': './uploads/%(id)s.%(ext)s',
                'noplaylist': True,
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Downloading audio via yt_dlp...")
                info_dict = ydl.extract_info(video_url, download=True)
                file_path = f"./uploads/{info_dict['id']}.webm"
                if not os.path.exists(file_path):
                    raise Exception("Downloaded file not found.")
        except Exception as e:
            print(f"Failed to process video URL: {e}")
            return jsonify({"error": f"Failed to process video URL: {e}"}), 500

    # Check if a file is uploaded
    elif "file" in request.files:
        file = request.files["file"]
        allowed_audio_extensions = [".mp3", ".wav"]
        allowed_video_extensions = [".mp4", ".webm"]
        
        if any(file.filename.endswith(ext) for ext in allowed_audio_extensions):
            # Handle audio files directly
            file_extension = os.path.splitext(file.filename)[1]
            file_path = f"./uploads/{uuid.uuid4()}{file_extension}"
            os.makedirs("./uploads", exist_ok=True)
            file.save(file_path)
        elif any(file.filename.endswith(ext) for ext in allowed_video_extensions):
            # Handle video files and extract audio
            file_extension = os.path.splitext(file.filename)[1]
            file_path = f"./uploads/{uuid.uuid4()}{file_extension}"
            os.makedirs("./uploads", exist_ok=True)
            file.save(file_path)
        else:
            return jsonify({"error": "Invalid file type. Please upload .mp4, .mp3, or .wav only."}), 400
    else:
        return jsonify({"error": "No video URL or file provided"}), 400

    # Extract audio if the file is a video
    if file_path.endswith(".mp4") or file_path.endswith(".webm"):
        audio_path = file_path.replace(".webm", ".wav").replace(".mp4", ".wav")
        print(f"Extracting audio to {audio_path}...")
        try:
            video_clip = AudioFileClip(file_path)
            video_clip.write_audiofile(audio_path, fps=16000)
            video_clip.close()
        except Exception as e:
            print(f"Failed to extract audio: {e}")
            return jsonify({"error": f"Failed to extract audio: {e}"}), 500
    else:
        audio_path = file_path

    # Transcribe audio using SpeechRecognition
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            print("Recognizing speech...")
            audio_data = recognizer.record(source)
            transcription = recognizer.recognize_google(audio_data)
            if not transcription.strip():
                return jsonify({"error": "No speech detected in audio"}), 400

            # Generate PDF with transcription
            pdf_bytes = create_pdf(transcription)
            return send_file(
                pdf_bytes,
                as_attachment=True,
                download_name="transcription.pdf",
                mimetype="application/pdf"
            )
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand audio"}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Google Speech Recognition service error: {e}"}), 500

# Helper function to create a PDF file from transcription
def create_pdf(text):
    pdf_stream = BytesIO()
    doc = SimpleDocTemplate(pdf_stream, pagesize=letter)
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    paragraphs = [Paragraph(line, normal_style) for line in text.split("\n")]
    doc.build(paragraphs)
    pdf_stream.seek(0)
    return pdf_stream

if __name__ == "__main__":
    os.makedirs("./uploads", exist_ok=True)
    app.run(debug=True)
