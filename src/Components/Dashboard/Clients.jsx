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
      
      console.log('🔄 Iniciando carga de analytics de clientes...');
      
      // Verificar conectividad del backend
      try {
        const healthCheck = await fetch('http://localhost:8000/health');
        if (!healthCheck.ok) {
          throw new Error('Backend no disponible');
        }
        console.log('✅ Backend conectado');
      } catch (err) {
        throw new Error('No se puede conectar con el backend');
      }

      // Poblar tabla clients si es necesario
      try {
        const clientsResponse = await fetch('http://localhost:8000/clients');
        const clientsData = await clientsResponse.json();
        
        if (clientsData.total_count === 0) {
          console.log('🔄 Poblando tabla clients...');
          await fetch('http://localhost:8000/clients/populate', { method: 'POST' });
          await new Promise(resolve => setTimeout(resolve, 2000)); // Esperar 2 segundos
        }
      } catch (err) {
        console.warn('⚠️ Error poblando tabla clients:', err);
      }

      // Obtener datos de análisis con manejo robusto de errores
      const endpoints = [
        'http://localhost:8000/clients/analytics/segmentation-stacked',
        'http://localhost:8000/clients/analytics/acquisition-trend',
        'http://localhost:8000/clients/analytics/most-profitable?limit=15',
        'http://localhost:8000/clients/analytics/dashboard-summary'
      ];

      const results = await Promise.allSettled(
        endpoints.map(url => 
          fetch(url)
            .then(response => {
              if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
              }
              return response.json();
            })
            .catch(error => {
              console.error(`Error en ${url}:`, error);
              return { success: false, data: [], error: error.message };
            })
        )
      );

      // Procesar resultados con validación robusta
      const [segmentation, acquisition, profitable, summary] = results;

      // Segmentación
      if (segmentation.status === 'fulfilled' && segmentation.value?.success) {
        console.log('✅ Datos de segmentación cargados:', segmentation.value.data?.length || 0);
        setSegmentationData(segmentation.value.data || []);
      } else {
        console.warn('⚠️ Error en segmentación:', segmentation.reason || segmentation.value?.error);
        setSegmentationData([]);
      }
      
      // Adquisición
      if (acquisition.status === 'fulfilled' && acquisition.value?.success) {
        console.log('✅ Datos de adquisición cargados:', acquisition.value.data?.length || 0);
        setAcquisitionData(acquisition.value.data || []);
      } else {
        console.warn('⚠️ Error en adquisición:', acquisition.reason || acquisition.value?.error);
        setAcquisitionData([]);
      }
      
      // Rentables
      if (profitable.status === 'fulfilled' && profitable.value?.success) {
        console.log('✅ Datos de clientes rentables cargados:', profitable.value.data?.length || 0);
        setProfitableData(profitable.value.data || []);
      } else {
        console.warn('⚠️ Error en clientes rentables:', profitable.reason || profitable.value?.error);
        setProfitableData([]);
      }
      
      // Summary
      if (summary.status === 'fulfilled' && summary.value?.success) {
        console.log('✅ Resumen del dashboard cargado');
        setDashboardSummary(summary.value || {});
      } else {
        console.warn('⚠️ Error en resumen:', summary.reason || summary.value?.error);
        setDashboardSummary({});
      }

      console.log('✅ Carga de analytics completada');
      
    } catch (err) {
      console.error('❌ Error general:', err);
      setError('Error cargando datos de análisis de clientes: ' + err.message);
    } finally {
      setDataLoading(false);
    }
  };

  // Procesar datos para gráfico de segmentación apilada
  const processSegmentationData = () => {
    if (!segmentationData || segmentationData.length === 0) {
      return [];
    }

    const processed = {};
    segmentationData.forEach(item => {
      const key = item.categoria || 'Sin categoría';
      if (!processed[key]) {
        processed[key] = { categoria: key };
      }
      processed[key][item.tipo_cliente || 'Sin tipo'] = item.cantidad_clientes || 0;
    });
    
    return Object.values(processed).slice(0, 8); // Limitar para mejor visualización
  };

  // Procesar datos para tendencia de adquisición
  const processAcquisitionData = () => {
    if (!acquisitionData || acquisitionData.length === 0) {
      return [];
    }

    const monthlyTotals = {};
    acquisitionData.forEach(item => {
      if (item.mes) {
        if (!monthlyTotals[item.mes]) {
          monthlyTotals[item.mes] = { mes: item.mes, total: 0 };
        }
        monthlyTotals[item.mes].total += item.nuevos_clientes || 0;
      }
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

  // Función para formatear moneda
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-PE', {
      style: 'currency',
      currency: 'PEN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  // Componente de carga
  const LoadingComponent = () => (
    <div className="dashboard-layout">
      <Sidebar userRole={userRole} onLogout={onLogout} />
      <div className="dashboard-content">
        <div className="clients-container">
          <h1 className="titulo">Análisis de Clientes</h1>
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Cargando análisis de clientes...</p>
            <p>Procesando datos y conectando con la base de datos...</p>
          </div>
        </div>
      </div>
    </div>
  );

  // Componente de error
  const ErrorComponent = () => (
    <div className="dashboard-layout">
      <Sidebar userRole={userRole} onLogout={onLogout} />
      <div className="dashboard-content">
        <div className="clients-container">
          <h1 className="titulo">Análisis de Clientes</h1>
          <div className="error-container">
            <h3>Error en Analytics</h3>
            <p>{error}</p>
            <button onClick={fetchAllAnalytics} className="retry-button">
              🔄 Reintentar
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  if (dataLoading) return <LoadingComponent />;
  if (error) return <ErrorComponent />;

  const processedSegmentation = processSegmentationData();
  const processedAcquisition = processAcquisitionData();

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
                <h3>{formatCurrency(dashboardSummary.summary.total_sales || 0)}</h3>
                <p>Ventas Totales</p>
              </div>
              <div className="stat-item">
                <h3>{formatCurrency(dashboardSummary.summary.total_mb || 0)}</h3>
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
                {processedSegmentation.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={processedSegmentation}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="categoria" 
                        tick={{ fontSize: 10 }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
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
                  <div className="placeholder-text">
                    📊 No hay datos de segmentación disponibles
                  </div>
                )}
              </div>
            </div>

            {/* 2. Top 10 clientes más rentables */}
            <div className="card">
              <h2>Top 10 clientes más rentables</h2>
              <div className="chart-placeholder">
                {profitableData.length > 0 ? (
                  <div className="profitable-clients-list">
                    {profitableData.slice(0, 10).map((client, index) => (
                      <div key={index} className="profitable-client-item">
                        <div className="client-info">
                          <span className="client-name">
                            {client.cliente || 'Cliente sin nombre'}
                          </span>
                          <span className="client-type">
                            ({client.tipo_cliente || 'Sin tipo'})
                          </span>
                        </div>
                        <div className="client-metrics">
                          <span className="client-sales">
                            {formatCurrency(client.total_ventas || 0)}
                          </span>
                          <span className="client-margin">
                            {(client.rentabilidad_porcentaje || 0).toFixed(1)}% MB
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="placeholder-text">
                    💰 No hay datos de clientes rentables disponibles
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* Gráfico de tendencia extendido - ocupa todo el ancho */}
          <div className="full-width-card">
            <h2>Tendencia de adquisición de nuevos clientes</h2>
            <div className="chart-placeholder">
              {processedAcquisition.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={processedAcquisition}>
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
                <div className="placeholder-text">
                  📈 No hay datos de tendencia de adquisición disponibles
                </div>
              )}
            </div>
          </div>

          {/* Top Ejecutivos */}
          {dashboardSummary.top_executives && dashboardSummary.top_executives.length > 0 && (
            <div className="executives-section">
              <h2>Top Ejecutivos Comerciales</h2>
              <div className="executives-grid">
                {dashboardSummary.top_executives.slice(0, 6).map((exec, index) => (
                  <div key={index} className="executive-card">
                    <h3>{exec.ejecutivo || 'Sin nombre'}</h3>
                    <p className="exec-clients">{exec.num_clientes || 0} clientes</p>
                    <p className="exec-sales">
                      {formatCurrency(exec.total_ventas || 0)}
                    </p>
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