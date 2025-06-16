import React, { useState, useEffect } from 'react';
import './Analysis.css';
import Sidebar from './Sidebar';

const Analysis = ({ userRole, onLogout }) => {
  // Estados para datos generales
  const [analyticsData, setAnalyticsData] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  
  // Estados para ML
  const [mlStatus, setMLStatus] = useState(null);
  const [mlRecommendations, setMLRecommendations] = useState([]);
  const [mlMetrics, setMLMetrics] = useState(null);
  const [mlLoading, setMLLoading] = useState(false);
  const [mlError, setMLError] = useState(null);
  
  // Estados para configuración
  const [filters, setFilters] = useState({
    minProbability: 0.6,
    limit: 20
  });

  useEffect(() => {
    fetchAnalyticsData();
    checkMLStatus();
    fetchMLMetrics();
  }, []);

  // Funciones para datos generales
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

  // Funciones para ML
  const checkMLStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/ml/status');
      const data = await response.json();
      setMLStatus(data);
      
      if (data.success && data.model_info.loaded) {
        fetchMLRecommendations();
      }
    } catch (error) {
      console.error('Error verificando ML:', error);
      setMLError('Error conectando con el modelo ML');
    }
  };

  const fetchMLRecommendations = async () => {
    setMLLoading(true);
    setMLError(null);
    try {
      const response = await fetch(
        `http://localhost:8000/ml/cross-sell-recommendations?limit=${filters.limit}&min_probability=${filters.minProbability}`
      );
      const data = await response.json();
      
      if (data.success) {
        setMLRecommendations(data.recommendations || []);
      } else {
        setMLError(data.message || 'Error obteniendo recomendaciones');
      }
    } catch (error) {
      console.error('Error ML:', error);
      setMLError('Error cargando recomendaciones ML');
    } finally {
      setMLLoading(false);
    }
  };

  const fetchMLMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/ml/model-performance');
      const data = await response.json();
      
      if (data.success) {
        setMLMetrics(data.performance);
      }
    } catch (error) {
      console.error('Error métricas ML:', error);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const refreshMLData = () => {
    fetchMLRecommendations();
    fetchMLMetrics();
  };

  // Funciones de utilidad
  const formatProbability = (prob) => `${(prob * 100).toFixed(1)}%`;
  
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'Alta': return '#e74c3c';
      case 'Media': return '#f39c12';
      case 'Baja': return '#3498db';
      default: return '#95a5a6';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-PE', {
      style: 'currency',
      currency: 'PEN'
    }).format(amount || 0);
  };

  return (
    <div className="dashboard-layout">
      <Sidebar userRole={userRole} onLogout={onLogout} />
      <div className="dashboard-content">
        <div className="analysis-container">
          <h1 className="titulo">Análisis de Datos</h1>
          
          {/* Estado del Modelo ML */}
          {mlStatus && (
            <div className={`ml-status-banner ${mlStatus.model_info?.loaded ? 'success' : 'error'}`}>
              {mlStatus.model_info?.loaded ? (
                <span>🤖 Modelo ML Activo - Versión: {mlStatus.model_info?.model_version || 'N/A'}</span>
              ) : (
                <span>⚠️ Modelo ML no disponible</span>
              )}
            </div>
          )}
          
          <div className="dashboard-grid">
            
            {/* Métricas Generales */}
            <div className="card">
              <h2>📊 Métricas Generales</h2>
              {dataLoading ? (
                <div className="loading-placeholder">Cargando métricas...</div>
              ) : (
                <div className="metrics-summary">
                  <div className="metric-item">
                    <span className="metric-value">{analyticsData.total_count || 0}</span>
                    <span className="metric-label">Total Registros</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-value">
                      {analyticsData.data ? 
                        formatCurrency(analyticsData.data.reduce((sum, item) => sum + (item.venta || 0), 0)) 
                        : formatCurrency(0)
                      }
                    </span>
                    <span className="metric-label">Ventas Totales</span>
                  </div>
                </div>
              )}
            </div>

            {/* Rendimiento del Modelo ML */}
            <div className="card">
              <h2>🎯 Rendimiento del Modelo</h2>
              {mlMetrics ? (
                <div className="ml-metrics">
                  <div className="metrics-grid">
                    <div className="metric-item">
                      <span className="metric-value">
                        {(mlMetrics.metrics?.precision * 100 || 0).toFixed(1)}%
                      </span>
                      <span className="metric-label">Precisión</span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-value">
                        {(mlMetrics.metrics?.recall * 100 || 0).toFixed(1)}%
                      </span>
                      <span className="metric-label">Recall</span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-value">
                        {(mlMetrics.metrics?.f1_score * 100 || 0).toFixed(1)}%
                      </span>
                      <span className="metric-label">F1-Score</span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-value">{mlMetrics.threshold}</span>
                      <span className="metric-label">Umbral</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="placeholder-text">
                  {mlStatus?.model_info?.loaded ? 'Cargando métricas...' : 'Modelo ML no disponible'}
                </div>
              )}
            </div>

            {/* Recomendaciones ML */}
            <div className="card full-width">
              <div className="card-header">
                <h2>🎯 Recomendaciones de Venta Cruzada</h2>
                <div className="ml-controls">
                  <label>
                    Probabilidad mín:
                    <select
                      value={filters.minProbability}
                      onChange={(e) => {
                        handleFilterChange('minProbability', parseFloat(e.target.value));
                        setTimeout(fetchMLRecommendations, 100);
                      }}
                    >
                      <option value={0.3}>30%</option>
                      <option value={0.5}>50%</option>
                      <option value={0.6}>60%</option>
                      <option value={0.7}>70%</option>
                    </select>
                  </label>
                  <label>
                    Límite:
                    <select
                      value={filters.limit}
                      onChange={(e) => {
                        handleFilterChange('limit', parseInt(e.target.value));
                        setTimeout(fetchMLRecommendations, 100);
                      }}
                    >
                      <option value={10}>10</option>
                      <option value={20}>20</option>
                      <option value={50}>50</option>
                    </select>
                  </label>
                  <button onClick={refreshMLData} className="refresh-btn" disabled={mlLoading}>
                    {mlLoading ? '⏳' : '🔄'} Actualizar
                  </button>
                </div>
              </div>
              
              {mlError && (
                <div className="error-message">⚠️ {mlError}</div>
              )}
              
              {mlLoading ? (
                <div className="loading-placeholder">Analizando clientes...</div>
              ) : mlRecommendations.length > 0 ? (
                <div className="recommendations-container">
                  <div className="recommendations-grid">
                    {mlRecommendations.slice(0, 6).map((rec, index) => (
                      <div key={index} className="recommendation-card">
                        <div className="card-header">
                          <h4>{rec.client_name}</h4>
                          <div 
                            className="priority-badge"
                            style={{ backgroundColor: getPriorityColor(rec.priority) }}
                          >
                            {rec.priority}
                          </div>
                        </div>
                        <div className="recommendation-details">
                          <div className="probability-display">
                            <span className="probability-label">Probabilidad:</span>
                            <span className="probability-value">{formatProbability(rec.probability)}</span>
                          </div>
                          <div className="client-info">
                            <p><strong>Tipo:</strong> {rec.tipo_cliente}</p>
                            <p><strong>Categoría:</strong> {rec.categoria}</p>
                            <p><strong>Venta Actual:</strong> {formatCurrency(rec.venta_actual)}</p>
                            <p><strong>Comercial:</strong> {rec.comercial}</p>
                          </div>
                        </div>
                        <div className="recommendation-actions">
                          <button className="action-btn primary">📞 Contactar</button>
                          <button className="action-btn secondary">📋 Ver Más</button>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {mlRecommendations.length > 6 && (
                    <div className="show-more">
                      <p>+ {mlRecommendations.length - 6} recomendaciones más</p>
                      <button 
                        className="show-all-btn"
                        onClick={() => {
                          // Aquí podrías abrir un modal o expandir la vista
                          console.log('Mostrar todas las recomendaciones');
                        }}
                      >
                        Ver Todas
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="placeholder-text">
                  {mlStatus?.model_info?.loaded ? 
                    'No hay recomendaciones con los filtros actuales' : 
                    'Modelo ML no disponible'
                  }
                </div>
              )}
            </div>

            {/* Importancia de Features */}
            <div className="card">
              <h2>📈 Factores Más Importantes</h2>
              {mlMetrics?.feature_importance ? (
                <div className="feature-importance">
                  {mlMetrics.feature_importance.slice(0, 6).map((feature, index) => (
                    <div key={index} className="feature-item">
                      <span className="feature-name">{feature.feature}</span>
                      <div className="feature-bar">
                        <div 
                          className="feature-fill"
                          style={{ width: `${feature.importance_percentage}%` }}
                        ></div>
                      </div>
                      <span className="feature-percentage">{feature.importance_percentage}%</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="placeholder-text">
                  {mlStatus?.model_info?.loaded ? 'Cargando importancia...' : 'Modelo ML no disponible'}
                </div>
              )}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;