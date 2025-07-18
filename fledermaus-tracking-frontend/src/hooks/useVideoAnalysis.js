import { useState } from 'react';
import { analyzeVideo as analyzeVideoAPI } from '../utils/api-real';

const useVideoAnalysis = (setAlert) => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const analyzeVideo = async (videoFile, startTime, endTime, uploadSensitivity) => {
    try {
      setLoading(true);
      
      // Check if we should use real API or dummy data
      const useRealAPI = process.env.REACT_APP_USE_REAL_API === 'true';
      
      if (useRealAPI) {
        try {
          console.log("Using real API for video analysis...");
          
          // Call real API
          const apiResult = await analyzeVideoAPI(videoFile, startTime, endTime, uploadSensitivity);
          
          setResults(apiResult);
          setAlert({ message: 'Analyse erfolgreich mit Backend abgeschlossen', type: 'success' });
          return apiResult;
          
        } catch (apiError) {
          console.warn("Real API failed, falling back to dummy data:", apiError);
          setAlert({ 
            message: `Backend nicht verfügbar, verwende Demo-Daten: ${apiError.message}`, 
            type: 'warning' 
          });
          // Fall through to dummy data
        }
      }
      
      // Use dummy data (original implementation)
      console.log("Using dummy data for video analysis demo...");
      
      // Simulate delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Enhanced dummy result with more realistic data
      const dummyResult = {
          totalFrames: Math.floor(Math.random() * 500) + 100,
          batDetected: Math.random() > 0.3, // 70% chance of detection
          detectionCount: Math.floor(Math.random() * 50) + 10,
          startPoint: { x: Math.floor(Math.random() * 50) + 10, y: Math.floor(Math.random() * 50) + 20 },
          endPoint: { x: Math.floor(Math.random() * 50) + 60, y: Math.floor(Math.random() * 50) + 70 },
          analysisTime: "00:01:23",
          fps: 30.0, // Safe default FPS
          videoDuration: (Math.floor(Math.random() * 500) + 100) / 30.0,
          positions: Array.from({ length: Math.floor(Math.random() * 50) + 10 }, (_, i) => ({
            frame: i + 1,
            x: Math.floor(Math.random() * 100),
            y: Math.floor(Math.random() * 100),
            width: Math.floor(Math.random() * 20) + 10,
            height: Math.floor(Math.random() * 30) + 15,
            timestamp: `00:00:${String(i + 1).padStart(2, '0')}`
          })),
          movementsPerFrame: Array.from({ length: Math.floor(Math.random() * 100) + 50 }, (_, i) => ({
            frame: i + 1,
            count: Math.floor(Math.random() * 5)
          }))
        };

      setResults(dummyResult);
      setAlert({ message: 'Demo-Analyse erfolgreich abgeschlossen', type: 'success' });
      return dummyResult;
      
    } catch (error) {
      console.error('Analysefehler:', error);
      setAlert({ message: `Fehler: ${error.message}`, type: 'error' });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return { analyzeVideo, loading, results, setResults };
};

export default useVideoAnalysis;
