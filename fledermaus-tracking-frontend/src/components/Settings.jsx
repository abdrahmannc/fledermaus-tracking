import React, { useState, useEffect, useRef } from 'react';

function Settings({ active, sensitivity, setSensitivity }) {
  const [tempSensitivity, setTempSensitivity] = useState(sensitivity);
  const debounceTimeout = useRef(null);

  useEffect(() => {
    setTempSensitivity(sensitivity);
  }, [sensitivity]);

  const handleChange = (e) => {
    const value = parseFloat(e.target.value);
    setTempSensitivity(value);

    // Debounce: Warte 300ms, bevor setSensitivity aufgerufen wird
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }
    debounceTimeout.current = setTimeout(() => {
      setSensitivity(value);
    }, 300);
  };

  if (!active) return null;

  return (
    <div style={{ padding: "1rem", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h2>Einstellungen</h2>
      <label htmlFor="sensitivity">Empfindlichkeit: {tempSensitivity.toFixed(2)}</label>
      <input
        type="range"
        id="sensitivity"
        min="0.1"
        max="1.0"
        step="0.05"
        value={tempSensitivity}
        onChange={handleChange}
        style={{ width: "100%" }}
      />
      <p style={{ fontSize: "0.9rem", color: "#666" }}>
        Höhere Werte erkennen auch kleine Bewegungen (z. B. flatternde Flügel).
      </p>
    </div>
  );
}

export default Settings;
