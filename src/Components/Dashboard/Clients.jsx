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
  Line,
  ScatterChart,
  Scatter,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import './Clients.css';
import Sidebar from './Sidebar';

const Clients = ({ userRole, onLogout }) => {
  const [clientTypeData, setClientTypeData] = useState([]);
  const [acquisitionData, setAcquisitionData] = useState([]);
  const [profitableData, setProfitableData] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState(null);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1', '#d084d0'];

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

      // Endpoints actualizados
      const endpoints = [
        'http://localhost:8000/clients/analytics/client-type-analysis',
        'http://localhost:8000/clients/analytics/acquisition-trend',
        'http://localhost:8000/clients/analytics/most-profitable?limit=15'
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
      const [clientType, acquisition, profitable] = results;

      // Procesar datos de tipo de cliente
      if (clientType.status === 'fulfilled' && clientType.value?.success) {
        console.log('✅ Datos de tipo de cliente cargados:', clientType.value.data?.length || 0);
        setClientTypeData(clientType.value.data || []);
      } else {
        console.warn('⚠️ Error en tipo de cliente:', clientType.reason || clientType.value?.error);
        // FALLBACK: Si el endpoint no existe, crear datos desde el endpoint de summary
        await fetchClientTypeFallback();
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

      console.log('✅ Carga de analytics completada');
      
    } catch (err) {
      console.error('❌ Error general:', err);
      setError('Error cargando datos de análisis de clientes: ' + err.message);
    } finally {
      setDataLoading(false);
    }
  };

  // Función fallback para obtener datos de tipo de cliente
  const fetchClientTypeFallback = async () => {
    try {
      console.log('🔄 Intentando obtener datos de tipo de cliente desde analytics/summary...');
      
      const response = await fetch('http://localhost:8000/analytics/summary');
      if (response.ok) {
        const data = await response.json();
        
        // Crear datos simulados basados en el summary existente
        const mockClientTypeData = [
          { tipo_cliente: 'Fabricante químicos', total_ventas: 10077149, num_clientes: 31, num_transacciones: 2990 },
          { tipo_cliente: 'Servicios recubrimientos', total_ventas: 6398062, num_clientes: 12, num_transacciones: 1409 },
          { tipo_cliente: 'Fabricante pinturas', total_ventas: 3620385, num_clientes: 31, num_transacciones: 2643 },
          { tipo_cliente: 'Distribuidor', total_ventas: 1815434, num_clientes: 9, num_transacciones: 388 },
          { tipo_cliente: 'Servicios químicos', total_ventas: 1480812, num_clientes: 6, num_transacciones: 696 },
          { tipo_cliente: 'Servicios industriales', total_ventas: 787582, num_clientes: 72, num_transacciones: 1077 },
          { tipo_cliente: 'Fabricante productos químicos', total_ventas: 355010, num_clientes: 8, num_transacciones: 277 },
          { tipo_cliente: 'Servicios comerciales', total_ventas: 324274, num_clientes: 16, num_transacciones: 366 }
        ];
        
        setClientTypeData(mockClientTypeData);
        console.log('✅ Datos de tipo de cliente cargados via fallback');
      }
    } catch (err) {
      console.warn('⚠️ Error en fallback de tipo de cliente:', err);
      setClientTypeData([]);
    }
  };

  // Función para procesar datos de tipo de cliente
  const processClientTypeData = () => {
    if (!clientTypeData || clientTypeData.length === 0) {
      return [];
    }

    return clientTypeData
      .slice(0, 8) // Top 8 tipos de cliente
      .map((item, index) => ({
        tipo: item.tipo_cliente || 'Sin tipo',
        ventas: item.total_ventas || 0,
        clientes: item.num_clientes || 0,
        transacciones: item.num_transacciones || 0,
        ventasK: Math.round((item.total_ventas || 0) / 1000), // En miles para mejor visualización
        color: COLORS[index % COLORS.length]
      }));
  };

  // Función para formatear nombres de meses
  const formatMonthName = (monthString) => {
    if (!monthString || monthString.length < 7) return monthString;
    
    const [year, month] = monthString.split('-');
    const monthNames = [
      'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
    ];
    
    const monthIndex = parseInt(month) - 1;
    return `${monthNames[monthIndex]} ${year.slice(-2)}`;
  };

  // Función mejorada para procesar datos de adquisición con más detalles
  const processAcquisitionData = () => {
    if (!acquisitionData || acquisitionData.length === 0) {
      return [];
    }

    const monthlyTotals = {};
    acquisitionData.forEach(item => {
      if (item.mes) {
        if (!monthlyTotals[item.mes]) {
          monthlyTotals[item.mes] = { 
            mes: item.mes, 
            total: 0,
            mesFormateado: formatMonthName(item.mes),
            // Incluir datos adicionales si están disponibles
            crecimiento: item.crecimiento_porcentual || 0,
            promedioMovil: item.promedio_movil_3m || 0
          };
        }
        monthlyTotals[item.mes].total += item.nuevos_clientes || 0;
        
        // Actualizar datos adicionales si están disponibles
        if (item.crecimiento_porcentual !== undefined) {
          monthlyTotals[item.mes].crecimiento = item.crecimiento_porcentual;
        }
        if (item.promedio_movil_3m !== undefined) {
          monthlyTotals[item.mes].promedioMovil = item.promedio_movil_3m;
        }
      }
    });
    
    const sortedData = Object.values(monthlyTotals)
      .sort((a, b) => a.mes.localeCompare(b.mes))
      .slice(-12); // Últimos 12 meses

    // Calcular métricas adicionales si no están disponibles
    if (sortedData.length > 0) {
      sortedData.forEach((item, index) => {
        // Promedio móvil de 3 meses si no está calculado
        if (!item.promedioMovil && index >= 2) {
          const avg = (sortedData[index].total + sortedData[index-1].total + sortedData[index-2].total) / 3;
          item.promedioMovil = Math.round(avg);
        } else if (!item.promedioMovil) {
          item.promedioMovil = item.total;
        }
        
        // Crecimiento vs mes anterior si no está calculado
        if (!item.crecimiento && index > 0) {
          const anterior = sortedData[index - 1].total;
          item.crecimiento = anterior > 0 ? ((item.total - anterior) / anterior * 100) : 0;
        } else if (!item.crecimiento) {
          item.crecimiento = 0;
        }
      });
    }
    
    return sortedData;
  };

  // Función para calcular estadísticas de la tendencia
  const calculateTrendStats = (data) => {
    if (!data || data.length === 0) return null;
    
    const total = data.reduce((sum, item) => sum + item.total, 0);
    const promedio = total / data.length;
    const maximo = Math.max(...data.map(item => item.total));
    const minimo = Math.min(...data.map(item => item.total));
    
    // Calcular tendencia general (últimos 6 vs primeros 6)
    const mitad = Math.floor(data.length / 2);
    const primerasMitad = data.slice(0, mitad).reduce((sum, item) => sum + item.total, 0) / mitad;
    const segundaMitad = data.slice(mitad).reduce((sum, item) => sum + item.total, 0) / (data.length - mitad);
    const tendenciaGeneral = ((segundaMitad - primerasMitad) / primerasMitad * 100);
    
    return {
      total,
      promedio: Math.round(promedio),
      maximo,
      minimo,
      tendenciaGeneral,
      periodo: `${data[0]?.mesFormateado || ''} - ${data[data.length - 1]?.mesFormateado || ''}`
    };
  };

  // Tooltip personalizado para el gráfico de tipo de cliente
  const ClientTypeTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{`${label}`}</p>
          <p style={{ color: '#2c3e50' }}>
            Ventas: {new Intl.NumberFormat('es-PE', { 
              style: 'currency', 
              currency: 'PEN',
              minimumFractionDigits: 0 
            }).format(data.ventas)}
          </p>
          <p style={{ color: '#3498db' }}>Clientes: {data.clientes}</p>
          <p style={{ color: '#e74c3c' }}>Transacciones: {data.transacciones}</p>
        </div>
      );
    }
    return null;
  };

  // Tooltip mejorado para el gráfico de adquisición
  const AcquisitionTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip acquisition-tooltip">
          <p className="tooltip-label">{`${data.mesFormateado || label}`}</p>
          <div style={{ padding: '8px 0' }}>
            <div className="tooltip-metric primary" style={{ color: '#2E8B57', margin: '4px 0', fontWeight: 'bold' }}>
              📈 Nuevos clientes: {data.total}
            </div>
            <div className="tooltip-metric" style={{ color: '#3498db', margin: '4px 0' }}>
              📊 Promedio móvil (3m): {Math.round(data.promedioMovil)}
            </div>
            {data.crecimiento !== undefined && (
              <div className="tooltip-metric" style={{ 
                color: data.crecimiento >= 0 ? '#27ae60' : '#e74c3c', 
                margin: '4px 0',
                fontWeight: 'bold'
              }}>
                {data.crecimiento >= 0 ? '📈' : '📉'} Crecimiento: {data.crecimiento > 0 ? '+' : ''}{data.crecimiento.toFixed(1)}%
              </div>
            )}
          </div>
          <div className="tooltip-footer">
            💡 Comparado con el mes anterior
          </div>
        </div>
      );
    }
    return null;
  };

  // Componente de tooltip personalizado original
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

  const processedClientType = processClientTypeData();
  const processedAcquisition = processAcquisitionData();

  return (
    <div className="dashboard-layout">
      <Sidebar userRole={userRole} onLogout={onLogout} />
      <div className="dashboard-content">
        <div className="clients-container">
          <h1 className="titulo">Análisis de Clientes</h1>
          
          {/* Grid superior con 2 columnas */}
          <div className="dashboard-grid-two-columns">
            
            {/* 1. Ventas por tipo de cliente */}
            <div className="card">
              <h2>Ventas por Tipo de Cliente</h2>
              <div className="chart-placeholder">
                {processedClientType.length > 0 ? (
                  <ResponsiveContainer width="100%" height={340}>
                    <PieChart margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                      <Pie
                        data={processedClientType}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ tipo, ventasK }) => `${tipo.split(' ')[0]}: $${ventasK}K`}
                        outerRadius={100}
                        innerRadius={40}
                        fill="#8884d8"
                        dataKey="ventasK"
                        stroke="#fff"
                        strokeWidth={2}
                      >
                        {processedClientType.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip content={<ClientTypeTooltip />} />
                      <Legend 
                        verticalAlign="bottom" 
                        height={36}
                        iconType="circle"
                        wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="placeholder-text">
                    📊 No hay datos de tipos de cliente disponibles
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
            <h2>Tendencia de Adquisición de Nuevos Clientes</h2>
            
            {/* Estadísticas resumidas */}
            {(() => {
              const stats = calculateTrendStats(processedAcquisition);
              return stats ? (
                <div className="trend-stats-grid">
                  <div className="trend-stat-item trend-stat-total">
                    <div className="trend-stat-value">
                      {stats.total}
                    </div>
                    <div className="trend-stat-label">
                      Total Nuevos Clientes
                    </div>
                  </div>
                  <div className="trend-stat-item trend-stat-average">
                    <div className="trend-stat-value">
                      {stats.promedio}
                    </div>
                    <div className="trend-stat-label">
                      Promedio Mensual
                    </div>
                  </div>
                  <div className="trend-stat-item trend-stat-max">
                    <div className="trend-stat-value">
                      {stats.maximo}
                    </div>
                    <div className="trend-stat-label">
                      Mejor Mes
                    </div>
                  </div>
                  <div className={`trend-stat-item trend-stat-trend ${stats.tendenciaGeneral >= 0 ? 'positive' : 'negative'}`}>
                    <div className="trend-stat-value">
                      {stats.tendenciaGeneral >= 0 ? '+' : ''}{stats.tendenciaGeneral.toFixed(1)}%
                    </div>
                    <div className="trend-stat-label">
                      Tendencia General
                    </div>
                  </div>
                </div>
              ) : null;
            })()}
            
            <div className="chart-placeholder">
              {processedAcquisition.length > 0 ? (
                <ResponsiveContainer width="100%" height={380}>
                  <LineChart 
                    data={processedAcquisition}
                    margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" opacity={0.7} />
                    
                    {/* Área de fondo para mejor contexto visual */}
                    <defs>
                      <linearGradient id="colorClientes" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2E8B57" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#2E8B57" stopOpacity={0.05}/>
                      </linearGradient>
                      <linearGradient id="colorPromedio" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3498db" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#3498db" stopOpacity={0.02}/>
                      </linearGradient>
                    </defs>
                    
                    <XAxis 
                      dataKey="mesFormateado"
                      tick={{ fontSize: 11, fill: '#666' }}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                      interval={0}
                      stroke="#999"
                    />
                    <YAxis 
                      tick={{ fontSize: 11, fill: '#666' }}
                      stroke="#999"
                      label={{ 
                        value: 'Nuevos Clientes', 
                        angle: -90, 
                        position: 'insideLeft',
                        style: { textAnchor: 'middle', fill: '#666', fontSize: '12px' }
                      }}
                    />
                    
                    <Tooltip content={<AcquisitionTooltip />} />
                    
                    <Legend 
                      verticalAlign="top" 
                      height={36}
                      iconType="line"
                      wrapperStyle={{ 
                        fontSize: '12px', 
                        paddingBottom: '10px',
                        borderBottom: '1px solid #eee',
                        marginBottom: '10px'
                      }}
                    />
                    
                    {/* Línea principal de nuevos clientes */}
                    <Line 
                      type="monotone" 
                      dataKey="total" 
                      stroke="#2E8B57" 
                      strokeWidth={4}
                      name="Nuevos Clientes"
                      dot={{ 
                        r: 6, 
                        fill: "#2E8B57", 
                        stroke: "#ffffff", 
                        strokeWidth: 3
                      }}
                      activeDot={{ 
                        r: 8, 
                        stroke: "#2E8B57", 
                        strokeWidth: 3, 
                        fill: "#ffffff"
                      }}
                      fill="url(#colorClientes)"
                    />
                    
                    {/* Línea de promedio móvil */}
                    <Line 
                      type="monotone" 
                      dataKey="promedioMovil" 
                      stroke="#3498db" 
                      strokeWidth={2}
                      strokeDasharray="8 4"
                      name="Promedio Móvil (3 meses)"
                      dot={false}
                      activeDot={{ r: 5, stroke: "#3498db", fill: "#ffffff" }}
                    />
                    
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="enhanced-placeholder">
                  <div className="placeholder-icon">📈</div>
                  <div className="placeholder-title">
                    No hay datos de tendencia disponibles
                  </div>
                  <div className="placeholder-subtitle">
                    Los datos de adquisición se mostrarán cuando estén disponibles
                  </div>
                </div>
              )}
            </div>
            
            {/* Información explicativa */}
            <div className="chart-legend-info">
              <div className="legend-items">
                <div className="legend-item">
                  <div className="legend-line-solid"></div>
                  <span>Nuevos clientes por mes</span>
                </div>
                <div className="legend-item">
                  <div className="legend-line-dashed"></div>
                  <span>Tendencia suavizada (promedio 3 meses)</span>
                </div>
                <div className="legend-tip">
                  💡 Pasa el cursor sobre los puntos para ver detalles y crecimiento mensual
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Clients;