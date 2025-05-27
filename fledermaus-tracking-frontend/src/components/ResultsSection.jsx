import React, { useRef } from 'react';
import Charts from './Charts';

import {
  exportAsCSV,
  exportAsJSON,
  exportAsPNG,
  exportAsPDFs
} from '../utils/export';

const ResultsSection = ({ active, results }) => {
  const canvasRef = useRef(null);

  if (!active) return null;

  if (!results) {
    return (
      <section id="results" className="section active-section">
        <p>Keine Analyseergebnisse verfügbar. Bitte laden Sie ein Video hoch und analysieren Sie es.</p>
      </section>
    );
  }



  
  return (
    <section id="results" className="section active-section">
      <h2>Analyseergebnisse</h2>

      <Charts results={results} canvasRef={canvasRef} />

      <div className="export-card" style={{ marginTop: '1em' }}>
        <h3><i className="fas fa-download"></i> Exportiere Ergebnisse</h3>
        <div className="export-buttons">
          <button onClick={() => exportAsCSV(results)}>
            <i className="fas fa-file-csv"></i> CSV
          </button>
          <button onClick={() => exportAsJSON(results)}>
            <i className="fas fa-code"></i> JSON
          </button>
          <button onClick={() => exportAsPDFs()}>
            <i className="fas fa-file-pdf"></i> PDF
          </button>
          <button onClick={() => exportAsPNG(canvasRef)}>
            <i className="fas fa-image"></i> PNG
          </button>
        </div>
      </div>
    </section>
  );
};

export default ResultsSection;
