import React, { useState, useEffect } from 'react';
import './Analysis.css';
import Sidebar from './Sidebar';

const Analysis = ({ userRole, onLogout }) => {
  const [analyticsData, setAnalyticsData] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    setDataLoading(true);
    try {
      const response = await fetch('http://localhost:8000/client-data');
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      }
    } catch (error) {
      console.error('Error de conexión:', error);
    } finally {
      setDataLoading(false);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar userRole={userRole} onLogout={onLogout} />
      <div className="dashboard-content">
        <div className="analysis-container">
          <h1 className="titulo">Análisis de Datos</h1>
          
          <div className="dashboard-grid">
            <div className="card">
              <h2>Métricas Generales</h2>
              <div className="chart-placeholder">
                <div className="placeholder-text">Gráfico de métricas generales</div>
              </div>
            </div>

            <div className="card">
              <h2>Tendencias de Ventas</h2>
              <div className="chart-placeholder">
                <div className="placeholder-text">Gráfico de tendencias</div>
              </div>
            </div>

            <div className="card">
              <h2>Análisis por Período</h2>
              <div className="chart-placeholder">
                <div className="placeholder-text">Análisis temporal</div>
              </div>
            </div>

            <div className="card">
              <h2>Predicciones</h2>
              <div className="chart-placeholder">
                <div className="placeholder-text">Modelos predictivos</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;