import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line
} from 'recharts';
import './Clients.css';
import Sidebar from './Sidebar';

const Clients = ({ userRole, onLogout }) => {
  const [segmentationData, setSegmentationData] = useState([]);
  const [acquisitionData, setAcquisitionData] = useState([]);
  const [profitableData, setProfitableData] = useState([]);
  const [dashboardSummary, setDashboardSummary] = useState({});
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState(null);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  // Cargar datos al montar el componente
  useEffect(() => {
    fetchAllAnalytics();
  }, []);

  const fetchAllAnalytics = async () => {
    try {
      setDataLoading(true);
      setError(null);
      
      // Verificar si la tabla clients existe y está poblada
      let clientsResponse = await fetch('http://localhost:8000/clients');
      if (!clientsResponse.ok || (await clientsResponse.json()).total_count === 0) {
        console.log('Poblando tabla clients...');
        await fetch('http://localhost:8000/clients/populate', { method: 'POST' });
        await new Promise(resolve => setTimeout(resolve, 3000)); // Esperar 3 segundos
      }

      // Obtener datos de análisis (removemos frequency-scatter)
      const [segmentation, acquisition, profitable, summary] = await Promise.all([
        fetch('http://localhost:8000/clients/analytics/segmentation-stacked').then(r => r.json()),
        fetch('http://localhost:8000/clients/analytics/acquisition-trend').then(r => r.json()),
        fetch('http://localhost:8000/clients/analytics/most-profitable?limit=10').then(r => r.json()),
        fetch('http://localhost:8000/clients/analytics/dashboard-summary').then(r => r.json())
      ]);

      setSegmentationData(segmentation.data || []);
      setAcquisitionData(acquisition.data || []);
      setProfitableData(profitable.data || []);
      setDashboardSummary(summary || {});
      
    } catch (err) {
      setError('Error cargando datos de análisis de clientes: ' + err.message);
      console.error('Error:', err);
    } finally {
      setDataLoading(false);
    }
  };

  // Procesar datos para gráfico de segmentación apilada
  const processSegmentationData = () => {
    const processed = {};
    segmentationData.forEach(item => {
      const key = item.categoria || 'Sin categoría';
      if (!processed[key]) {
        processed[key] = { categoria: key };
      }
      processed[key][item.tipo_cliente || 'Sin tipo'] = item.cantidad_clientes;
    });
    return Object.values(processed).slice(0, 8); // Limitar para que se vea bien
  };

  // Procesar datos para tendencia de adquisición
  const processAcquisitionData = () => {
    const monthlyTotals = {};
    acquisitionData.forEach(item => {
      if (!monthlyTotals[item.mes]) {
        monthlyTotals[item.mes] = { mes: item.mes, total: 0 };
      }
      monthlyTotals[item.mes].total += item.nuevos_clientes;
    });
    return Object.values(monthlyTotals)
      .sort((a, b) => a.mes.localeCompare(b.mes))
      .slice(-12); // Últimos 12 meses
  };

  // Componente de tooltip personalizado
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{`${label}`}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.dataKey}: ${entry.value}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (dataLoading) {
    return (
      <div className="dashboard-layout">
        <Sidebar userRole={userRole} onLogout={onLogout} />
        <div className="dashboard-content">
          <div className="clients-container">
            <h1 className="titulo">Análisis de Clientes</h1>
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Cargando análisis de clientes...</p>
              <p>Procesando datos agregados...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-layout">
        <Sidebar userRole={userRole} onLogout={onLogout} />
        <div className="dashboard-content">
          <div className="clients-container">
            <h1 className="titulo">Análisis de Clientes</h1>
            <div className="error-container">
              <h3>Error en Analytics</h3>
              <p>{error}</p>
              <button onClick={fetchAllAnalytics} className="retry-button">
                Reintentar
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      <Sidebar userRole={userRole} onLogout={onLogout} />
      <div className="dashboard-content">
        <div className="clients-container">
          <h1 className="titulo">Análisis de Clientes</h1>
          
          {/* Panel de estadísticas resumidas */}
          {dashboardSummary.summary && (
            <div className="summary-stats">
              <div className="stat-item">
                <h3>{dashboardSummary.summary.total_clients || 0}</h3>
                <p>Total Clientes</p>
              </div>
              <div className="stat-item">
                <h3>${(dashboardSummary.summary.total_sales || 0).toLocaleString()}</h3>
                <p>Ventas Totales</p>
              </div>
              <div className="stat-item">
                <h3>${(dashboardSummary.summary.total_mb || 0).toLocaleString()}</h3>
                <p>Margen Bruto</p>
              </div>
              <div className="stat-item">
                <h3>{(dashboardSummary.summary.avg_frequency || 0).toFixed(1)}</h3>
                <p>Frecuencia Promedio</p>
              </div>
            </div>
          )}
          
          {/* Grid superior con 2 columnas */}
          <div className="dashboard-grid-two-columns">
            
            {/* 1. Segmentación de clientes por tipo y categoría */}
            <div className="card">
              <h2>Segmentación de clientes por tipo y categoría</h2>
              <div className="chart-placeholder">
                {processSegmentationData().length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={processSegmentationData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="categoria" 
                        tick={{ fontSize: 10 }}
                        angle={-45}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Bar dataKey="Nacional" stackId="a" fill="#0088FE" />
                      <Bar dataKey="Exportación" stackId="a" fill="#00C49F" />
                      <Bar dataKey="Otro" stackId="a" fill="#FFBB28" />
                      <Bar dataKey="Sin tipo" stackId="a" fill="#FF8042" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="placeholder-text">No hay datos disponibles</div>
                )}
              </div>
            </div>

            {/* 2. Top 10 clientes más rentables */}
            <div className="card">
              <h2>Top 10 clientes más rentables</h2>
              <div className="chart-placeholder">
                {profitableData.length > 0 ? (
                  <div className="profitable-clients-list">
                    {profitableData.slice(0, 8).map((client, index) => (
                      <div key={index} className="profitable-client-item">
                        <div className="client-info">
                          <span className="client-name">{client.cliente}</span>
                          <span className="client-type">({client.tipo_cliente})</span>
                        </div>
                        <div className="client-metrics">
                          <span className="client-sales">${client.total_ventas.toLocaleString()}</span>
                          <span className="client-margin">{client.rentabilidad_porcentaje}% MB</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="placeholder-text">No hay datos disponibles</div>
                )}
              </div>
            </div>

          </div>

          {/* Gráfico de tendencia extendido - ocupa todo el ancho */}
          <div className="full-width-card">
            <h2>Tendencia de adquisición de nuevos clientes</h2>
            <div className="chart-placeholder">
              {processAcquisitionData().length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={processAcquisitionData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="mes" 
                      tick={{ fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line 
                      type="monotone" 
                      dataKey="total" 
                      stroke="#8884d8" 
                      strokeWidth={3}
                      name="Nuevos clientes"
                      dot={{ r: 5, fill: "#8884d8" }}
                      activeDot={{ r: 8, stroke: "#8884d8", strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="placeholder-text">No hay datos disponibles</div>
              )}
            </div>
          </div>

          {/* Top Ejecutivos */}
          {dashboardSummary.top_executives && dashboardSummary.top_executives.length > 0 && (
            <div className="executives-section">
              <h2>Top Ejecutivos Comerciales</h2>
              <div className="executives-grid">
                {dashboardSummary.top_executives.slice(0, 5).map((exec, index) => (
                  <div key={index} className="executive-card">
                    <h3>{exec.ejecutivo}</h3>
                    <p className="exec-clients">{exec.num_clientes} clientes</p>
                    <p className="exec-sales">${exec.total_ventas.toLocaleString()}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default Clients;