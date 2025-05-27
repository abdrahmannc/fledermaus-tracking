import React from 'react';
import HomeSection from './HomeSection';
import UploadSection from './UploadSection';
import ResultsSection from './ResultsSection';
import Settings from './Settings';

const MainContent = ({ activeSection, setActiveSection, results, setResults }) => {
  return (
    <main className="main-content">
      <header className="main-header">
        <h1>Fledermaus-Tracking Analyse</h1>
        <p>Analyse von IR- oder Wärmebildvideos zur Fledermaus-Erkennung</p>
      </header>

      <HomeSection active={activeSection === 'home'} />
      <UploadSection
        active={activeSection === 'upload'}
        setResults={setResults}
        switchToResults={() => setActiveSection('results')}
      />
      {results && (
        <ResultsSection
          active={activeSection === 'results'}
          results={results}
        />
      )}
      <Settings active={activeSection === 'settings'} />
    </main>
  );
};

export default MainContent;
