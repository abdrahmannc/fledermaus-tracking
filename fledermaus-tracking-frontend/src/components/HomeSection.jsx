import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faHome, 
  faCheckCircle, 
  faVideo,  
  faPlay,
  faChartBar,
  faMap
} from '@fortawesome/free-solid-svg-icons';

const HomeSection = ({ active }) => {
  if (!active) return null;

  return (
    <section id="home" className="section active-section">
      <div className="section-content">
        <h2>
          <FontAwesomeIcon icon={faHome} />
          Willkommen zum Fledermaus-Tracking Tool
        </h2>
        
        <div className="features-container">
          <h3>Funktionen:</h3>
          <ul className="features-list">
            <li>
              <FontAwesomeIcon icon={faCheckCircle} className="feature-icon" />
              Video-Upload und Analyse
            </li>
            <li>
              <FontAwesomeIcon icon={faCheckCircle} className="feature-icon" />
              Erkennung von Fledermausbewegungen
            </li>
            <li>
              <FontAwesomeIcon icon={faCheckCircle} className="feature-icon" />
              Statistische Auswertung der Flugbahnen
            </li>
            <li>
              <FontAwesomeIcon icon={faCheckCircle} className="feature-icon" />
              Visualisierung der Ergebnisse in Diagrammen
            </li>
            <li>
              <FontAwesomeIcon icon={faCheckCircle} className="feature-icon" />
              Quartierpotenzial-Analyse
            </li>
          </ul>
        </div>
        
        <div className="quick-start">
          <h3>Schnellstart:</h3>
          <ol className="quick-start-steps">
            <li>
              <FontAwesomeIcon icon={faVideo} className="step-icon" />
              Video hochladen (Abschnitt "Video Hochladen")
            </li>
            <li>
              <FontAwesomeIcon icon={faPlay} className="step-icon" />
              Analyse starten
            </li>
            <li>
              <FontAwesomeIcon icon={faChartBar} className="step-icon" />
              Ergebnisse im Abschnitt "Ergebnisse" ansehen
            </li>
            <li>
              <FontAwesomeIcon icon={faMap} className="step-icon" />
              Quartierpotenzial auf der Karte analysieren
            </li>
          </ol>
        </div>
      </div>
    </section>
  );
};

export default HomeSection;