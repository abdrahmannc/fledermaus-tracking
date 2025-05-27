import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

const Charts = ({ results }) => {
  const trackingChartRef = useRef(null);
  const movementChartRef = useRef(null);
  
  useEffect(() => {
    if (!results) return;
    // Initialize or update charts
    const trackingCtx = trackingChartRef.current.getContext('2d');
    const movementCtx = movementChartRef.current.getContext('2d');

    const trackingChart = new Chart(trackingCtx, {
      type: 'line',
      data: {
        labels: results.positions.map(p => p.frame),
        datasets: [
          {
            label: 'X-Position',
            data: results.positions.map(p => p.x),
            borderColor: 'rgba(54, 162, 235, 1)',
            fill: false
          },
          {
            label: 'Y-Position',
            data: results.positions.map(p => p.y),
            borderColor: 'rgba(255, 99, 132, 1)',
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        scales: {
          x: { title: { display: true, text: 'Frame' } },
          y: { title: { display: true, text: 'Position' } }
        }
      }
    });

    const movementChart = new Chart(movementCtx, {
      type: 'bar',
      data: {
        labels: results.movementsPerFrame.map(m => m.frame),
        datasets: [{
          label: 'Bewegungen pro Frame',
          data: results.movementsPerFrame.map(m => m.count),
          backgroundColor: 'rgba(75, 192, 192, 0.7)'
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: { title: { display: true, text: 'Frame' } },
          y: { 
            title: { display: true, text: 'Anzahl Bewegungen' },
            beginAtZero: true
          }
        }
      }
    });

    return () => {
      trackingChart.destroy();
      movementChart.destroy();
    };
  }, [results]);

  return (
    <div className="charts-container">
      <div className="chart-card">
        <h3><i className="fas fa-route"></i> Flugbahn der Fledermaus</h3>
        <div className="chart-wrapper">
          <canvas ref={trackingChartRef}></canvas>
        </div>
      </div>
      <div className="chart-card">
        <h3><i className="fas fa-running"></i> Bewegungen pro Frame</h3>
        <div className="chart-wrapper">
          <canvas ref={movementChartRef}></canvas>
        </div>
      </div>
    </div>
  );
};

export default Charts;