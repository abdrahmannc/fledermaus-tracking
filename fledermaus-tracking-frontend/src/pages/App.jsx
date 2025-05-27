import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import MainContent from '../components/MainContent';

const AppPage = () => {
  const [activeSection, setActiveSection] = useState('home');
  const [results, setResults] = useState(null);

  return (
    <div className="container">
      <Sidebar activeSection={activeSection} setActiveSection={setActiveSection} />
      <MainContent
        activeSection={activeSection}
        setActiveSection={setActiveSection}
        results={results}
        setResults={setResults}
      />
    </div>
  );
};

export default AppPage;
