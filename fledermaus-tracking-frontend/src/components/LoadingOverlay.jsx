import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

const LoadingOverlay = ({ visible, progress = 0, message = "Video wird analysiert..." }) => {
  if (!visible) return null;

  return (
    <div className="loading-overlay">
      <div className="spinner-container">
        <FontAwesomeIcon 
          icon={faSpinner} 
          className="spinner" 
          spin 
          size="2x"
        />
        <p>{message}</p>
        <div className="progress-container">
          <div 
            className="progress-bar"
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div 
              className="progress" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <span className="progress-text">{progress}%</span>
        </div>
      </div>
    </div>
  );
};

export default LoadingOverlay;