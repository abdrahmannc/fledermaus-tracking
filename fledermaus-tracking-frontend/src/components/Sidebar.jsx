import React from 'react';

const Sidebar = ({ activeSection, setActiveSection }) => {
  const sections = [
    { id: 'home', icon: 'fa-home', label: 'Startseite' },
    { id: 'upload', icon: 'fa-upload', label: 'Video Hochladen' },
    { id: 'results', icon: 'fa-chart-bar', label: 'Ergebnisse' },
    { id: 'settings', icon: 'fa-cog', label: 'Einstellungen' },
    { id: 'map', icon: 'fa-map', label: 'Quartieranalyse' }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2><i className="fas fa-bat"></i> Fledermaus-Tracker</h2>
      </div>
      <nav>
        <ul>
          {sections.map((section) => (
            <li key={section.id}>
              <a 
                href="#" 
                className={`nav-link ${activeSection === section.id ? 'active' : ''}`}
                onClick={(e) => {
                  e.preventDefault();
                  setActiveSection(section.id);
                }}
              >
                <i className={`fas ${section.icon}`}></i> {section.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <div className="sidebar-footer">
        <p>Betreuer: Prof. Dr. B. W.</p>
        <p>Erstellt von: A. Cheikh</p>
        <p>Fach:Sondergebiete der Info.</p>
        <p>Unternehmen: IfAÖ GmbH</p>
        <p>Version 1.0.0</p>
      </div>

    </aside>
  );
};

export default Sidebar;