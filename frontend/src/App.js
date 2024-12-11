import React, { useState } from "react";
import "./App.css";

function VideoTranscription() {
  const [videoUrl, setVideoUrl] = useState("");
  const [videoFile, setVideoFile] = useState(null);
  const [status, setStatus] = useState("");
  const [downloadLink, setDownloadLink] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus("");
    setDownloadLink(null);

    if (!videoUrl && !videoFile) {
      setStatus("Please provide a video URL or upload a video/audio file.");
      return;
    }

    const formData = new FormData();

    if (videoUrl) {
      try {
        new URL(videoUrl);
        formData.append("url", videoUrl);
      } catch {
        setStatus("Invalid URL. Please enter a valid video URL.");
        return;
      }
    }

    if (videoFile) {
      const allowedTypes = ["video/mp4", "audio/mp3", "audio/wav", "video/webm"];
      if (!allowedTypes.includes(videoFile.type)) {
        setStatus("Invalid file type. Please upload MP4, MP3, WAV, or WEBM files only.");
        return;
      }
      formData.append("file", videoFile);
    }

    setIsLoading(true);
    setStatus("Processing... This may take a few minutes.");

    try {
      const response = await fetch("http://127.0.0.1:5000/process", {
        method: "POST",
        body: formData,
      });

      setIsLoading(false);

      if (response.ok) {
        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        setDownloadLink(downloadUrl);
        setStatus("Transcription Complete!");
      } else {
        const errorData = await response.json();
        setStatus(`Error: ${errorData.error}`);
      }
    } catch (error) {
      setIsLoading(false);
      setStatus(`An error occurred: ${error.message}`);
    }
  };

  const handleReset = () => {
    setVideoUrl("");
    setVideoFile(null);
    setStatus("");
    setDownloadLink(null);
  };

  return (
    <div className="container">
      <h1>Video/Audio Transcription Service</h1>
      <form onSubmit={handleSubmit} className="form">
        <div className="input-group">
          <label>Enter Video/Audio URL (Optional):</label>
          <input
            type="url"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="Paste YouTube or video/audio URL"
          />
        </div>
        <div className="input-group">
          <label>Or Upload a Video/Audio File:</label>
          <input
            type="file"
            onChange={(e) => setVideoFile(e.target.files[0])}
            accept=".mp4,.mp3,.wav,.webm"
          />
        </div>
        <div className="button-group">
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Processing..." : "Transcribe"}
          </button>
          <button type="button" onClick={handleReset}>
            Reset
          </button>
        </div>
      </form>
      {status && <div className="status-message">{status}</div>}
      {downloadLink && (
        <div>
          <a href={downloadLink} download="transcription.pdf">
            Download Transcription PDF
          </a>
        </div>
      )}
    </div>
  );
}

export default VideoTranscription;
