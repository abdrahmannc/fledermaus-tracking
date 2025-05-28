import { useState } from 'react';
const useVideoAnalysis = (setAlert) => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const analyzeVideo = async (videoFile, startTime, endTime, uploadSensitivity) => {
    try {
      setLoading(true);
      // Simulate delay
      await new Promise(resolve => setTimeout(resolve, 1500));
        console.log("Hello I reive you request .. I do it .. best gard from analyze()")
      // Dummy result
      const dummyResult = {
          totalFrames: 100,
          batDetected: true,
          detectionCount: 42,
          startPoint: { x: 10, y: 20 },
          endPoint: { x: 80, y: 90 },
          analysisTime: "00:01:23",
          positions: Array.from({ length: 100 }, (_, i) => ({
            frame: i + 1,
            x: Math.floor(Math.random() * 100),
            y: Math.floor(Math.random() * 100),
            width: 15,
            height: 30,
            timestamp: `00:00:${String(i + 1).padStart(2, '0')}`
          })),
          movementsPerFrame: Array.from({ length: 100 }, (_, i) => ({
            frame: i + 1,
            count: Math.floor(Math.random() * 10)
          }))
        };


      setResults(dummyResult);


      setAlert({ message: 'Analyse erfolgreich abgeschlossen', type: 'success' });
      return dummyResult;
    } catch (error) {
      console.error('Analysefehler:', error);
      setAlert({ message: `Fehler: ${error.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return { analyzeVideo, loading, results, setResults };
};

export default useVideoAnalysis;
