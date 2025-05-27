import React, { useState, useRef, useEffect } from 'react';
import useVideoAnalysis from '../hooks/useVideoAnalysis';
import LoadingOverlay from './LoadingOverlay';
import Alert from './Alert';

const UploadSection = ({ active, setResults, switchToResults }) => {
  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [startTime, setStartTime] = useState(0);
  const [endTime, setEndTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [alert, setAlert] = useState(null);

  const videoRef = useRef(null);
  const fileInputRef = useRef(null);

  const { analyzeVideo, loading } = useVideoAnalysis(setAlert);

  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const url = URL.createObjectURL(file);
    setVideoFile(file);
    setVideoUrl(url);
    setStartTime(0);
    setEndTime(0);
    setCurrentTime(0);
    setAlert(null);

    if (videoRef.current) {
      videoRef.current.src = url;
      videoRef.current.style.display = 'block';
    }
  };

  const onLoadedMetadata = () => {
    if (videoRef.current) {
      const dur = videoRef.current.duration;
      setDuration(dur);
      setEndTime(dur);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleAnalyze = async () => {
    if (!videoFile) {
      setAlert({ message: 'Bitte wählen Sie zuerst eine Videodatei aus.', type: 'warning' });
      return;
    }

    if (startTime >= endTime) {
      setAlert({ message: 'Startzeit muss kleiner als Endzeit sein.', type: 'warning' });
      return;
    }

    try {
      const analyzeResults = await analyzeVideo(videoFile, startTime, endTime);
      if (analyzeResults) {
        setResults(analyzeResults);      
        switchToResults();              
      }
    } catch (err) {
      setAlert({ message: 'Analyse fehlgeschlagen.', type: 'error' });
    }
  };

  if (!active) return null;

  return (
    <section id="upload" className="section active-section">
      <div className="section-content">
        <h2>Video hochladen</h2>
        <p className="section-description">
          Laden Sie ein Video hoch, wählen Sie einen Ausschnitt und analysieren Sie ihn.
        </p>

        <div className="upload-container">
          <button className="upload-btn" onClick={() => fileInputRef.current.click()}>
            <i className="fas fa-video"></i> Video auswählen
            <input
              type="file"
              ref={fileInputRef}
              accept="video/mp4,video/x-m4v,video/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </button>

          <span className="file-name">
            {videoFile ? videoFile.name : 'Keine Datei ausgewählt'}
          </span>

          <div className="video-preview-container">
            <video
              ref={videoRef}
              className="video-preview"
              controls
              onLoadedMetadata={onLoadedMetadata}
              onTimeUpdate={handleTimeUpdate}
              style={{ display: videoFile ? 'block' : 'none', maxWidth: '100%' }}
            />
          </div>

          {duration > 0 && (
            <div className="segment-controls" style={{ marginTop: '1em' }}>
              <div>
                <label>Startzeit: </label>
                <input
                  type="range"
                  min="0"
                  max={duration}
                  step="0.1"
                  value={startTime}
                  onChange={(e) => setStartTime(parseFloat(e.target.value))}
                />
                <span> {startTime.toFixed(2)}s</span>
              </div>
              <div>
                <label>Endzeit: </label>
                <input
                  type="range"
                  min="0"
                  max={duration}
                  step="0.1"
                  value={endTime}
                  onChange={(e) => setEndTime(parseFloat(e.target.value))}
                />
                <span> {endTime.toFixed(2)}s</span>
              </div>
              <p>
                Segment: {startTime.toFixed(2)}s – {endTime.toFixed(2)}s (
                {(endTime - startTime).toFixed(2)}s)
              </p>
              <p><strong>Aktuelle Zeit:</strong> {currentTime.toFixed(2)}s</p>
            </div>
          )}

          <button
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={!videoFile || loading}
          >
            <i className="fas fa-play"></i> Analyse starten
          </button>

          {alert && <Alert message={alert.message} type={alert.type} />}

          <LoadingOverlay visible={loading} />
        </div>
      </div>
    </section>
  );
};

export default UploadSection;
