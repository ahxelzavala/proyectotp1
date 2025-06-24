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
  const [salesByTypeDetailed, setSalesByTypeDetailed] = useState(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState(null);
  const [acquisitionDebug, setAcquisitionDebug] = useState(null);

  const COLORS = ['#8884D8', '#82CA9D', '#FFC658', '#FF7C7C', '#8DD1E1', '#D084D0'];

  // Cargar datos al montar el componente
  useEffect(() => {
    fetchAllAnalytics();
  }, []);

  // Función para debuggear adquisición
  const debugAcquisition = async () => {
    try {
      console.log('🔍 Ejecutando debug de adquisición...');
      const response = await fetch('http://localhost:8000/debug/test-acquisition');
      if (response.ok) {
        const debugData = await response.json();
        console.log('🐛 Debug data:', debugData);
        setAcquisitionDebug(debugData);
        return debugData;
      }
    } catch (err) {
      console.error('❌ Error en debug:', err);
    }
    return null;
  };

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

      // Primero ejecutar debug para entender los datos
      await debugAcquisition();
  
      // Endpoints para cargar datos
      const endpoints = [
        'http://localhost:8000/clients/analytics/sales-by-type-detailed',
        'http://localhost:8000/clients/analytics/acquisition-trend',
        'http://localhost:8000/clients/analytics/top-profitable-detailed?limit=10'
      ];
  
      const results = await Promise.allSettled(
        endpoints.map(async (url, index) => {
          try {
            console.log(`🌐 Cargando ${url}...`);
            const response = await fetch(url);
            
            if (!response.ok) {
              throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log(`✅ Respuesta de endpoint ${index + 1}:`, data);
            return data;
          } catch (error) {
            console.error(`❌ Error en ${url}:`, error);
            return { success: false, data: [], error: error.message };
          }
        })
      );
  
      // Procesar resultados
      const [salesDetailed, acquisition, profitable] = results;
  
      // Procesar datos de ventas por tipo (sin cambios)
      if (salesDetailed.status === 'fulfilled' && salesDetailed.value?.success) {
        console.log('✅ Datos detallados de ventas por tipo cargados:', salesDetailed.value);
        setSalesByTypeDetailed(salesDetailed.value);
        setClientTypeData(salesDetailed.value.data || []);
      } else {
        console.warn('⚠️ Error en datos detallados:', salesDetailed.reason || salesDetailed.value?.error);
        await fetchClientTypeFallback();
      }
      
      // PROCESAMIENTO MEJORADO PARA ADQUISICIÓN CON DEBUGGING EXTENSO
      if (acquisition.status === 'fulfilled') {
        const acqData = acquisition.value;
        console.log('📊 === DEBUGGING ADQUISICIÓN COMPLETO ===');
        console.log('📊 Respuesta completa:', JSON.stringify(acqData, null, 2));
        console.log('📊 Tipo de respuesta:', typeof acqData);
        console.log('📊 Es objeto:', acqData && typeof acqData === 'object');
        console.log('📊 Tiene success:', 'success' in acqData);
        console.log('📊 Valor de success:', acqData?.success);
        console.log('📊 Tiene data:', 'data' in acqData);
        console.log('📊 Tipo de data:', Array.isArray(acqData?.data));
        console.log('📊 Longitud de data:', acqData?.data?.length);
        
        if (acqData?.success === true) {
          if (Array.isArray(acqData.data) && acqData.data.length > 0) {
            console.log('✅ DATOS DE ADQUISICIÓN VÁLIDOS:');
            acqData.data.forEach((item, index) => {
              console.log(`   ${index + 1}. ${JSON.stringify(item)}`);
            });
            setAcquisitionData(acqData.data);
          } else {
            console.warn('⚠️ SUCCESS=true pero array vacío o inválido');
            console.log('   - Array.isArray(data):', Array.isArray(acqData.data));
            console.log('   - data.length:', acqData.data?.length);
            console.log('   - data content:', acqData.data);
            setAcquisitionData([]);
          }
        } else {
          console.warn('⚠️ RESPUESTA CON SUCCESS=false');
          console.log('   - Message:', acqData?.message);
          console.log('   - Error type:', acqData?.error_type);
          console.log('   - Diagnostic:', acqData?.diagnostic);
          setAcquisitionData([]);
        }
      } else {
        console.error('❌ ENDPOINT DE ADQUISICIÓN FALLÓ COMPLETAMENTE');
        console.error('   - Status:', acquisition.status);
        console.error('   - Reason:', acquisition.reason);
        setAcquisitionData([]);
      }
      
      // Rentables detallados (sin cambios)
      if (profitable.status === 'fulfilled' && profitable.value?.success) {
        console.log('✅ Datos de clientes rentables detallados cargados:', profitable.value.data?.length || 0);
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

  // Función fallback (sin cambios)
  const fetchClientTypeFallback = async () => {
    try {
      console.log('🔄 Intentando obtener datos desde client-type-analysis...');
      
      const response = await fetch('http://localhost:8000/clients/analytics/client-type-analysis');
      if (response.ok) {
        const data = await response.json();
        
        if (data.success && data.data?.length > 0) {
          setClientTypeData(data.data);
          
          const totalVentas = data.data.reduce((sum, item) => sum + item.total_ventas, 0);
          const mockResumen = {
            total_tipos: data.data.length,
            total_ventas: totalVentas
          };
          
          setSalesByTypeDetailed({ 
            data: data.data, 
            resumen: mockResumen,
            success: true 
          });
          
          console.log('✅ Datos cargados via fallback');
        }
      }
    } catch (err) {
      console.warn('⚠️ Error en fallback:', err);
      setClientTypeData([]);
      setSalesByTypeDetailed(null);
    }
  };

  // Funciones de formato (sin cambios)
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-PE', {
      style: 'currency',
      currency: 'PEN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const formatCurrencyShort = (amount) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `$${Math.round(amount / 1000)}K`;
    }
    return formatCurrency(amount);
  };

  // Función processPieData (sin cambios)
  const processPieData = () => {
    if (salesByTypeDetailed?.pie_data && salesByTypeDetailed.pie_data.length > 0) {
      return salesByTypeDetailed.pie_data.map(item => ({
        name: item.name,
        value: item.value,
        percentage: item.percentage,
        color: item.color,
        num_clientes: item.num_clientes,
        num_transacciones: item.num_transacciones,
        total_mb: item.total_mb,
        is_others: item.is_others || false,
        otros_count: item.otros_count || 0,
        formattedValue: formatCurrency(item.value),
        shortValue: formatCurrencyShort(item.value)
      }));
    }
    
    if (salesByTypeDetailed?.data && salesByTypeDetailed.data.length > 0) {
      const allData = salesByTypeDetailed.data;
      const totalVentas = allData.reduce((sum, item) => sum + (item.total_ventas || 0), 0);
      
      const top5 = allData.slice(0, 5);
      const otros = allData.slice(5);
      
      let pieData = top5.map((item, index) => ({
        name: item.tipo_cliente || 'Sin categoría',
        value: item.total_ventas || 0,
        percentage: totalVentas > 0 ? ((item.total_ventas || 0) / totalVentas * 100).toFixed(1) : 0,
        color: COLORS[index % COLORS.length],
        num_clientes: item.num_clientes || 0,
        num_transacciones: item.num_transacciones || 0,
        total_mb: item.total_mb || 0,
        is_others: false,
        otros_count: 0,
        formattedValue: formatCurrency(item.total_ventas || 0),
        shortValue: formatCurrencyShort(item.total_ventas || 0)
      }));
      
      if (otros.length > 0) {
        const otrosTotal = otros.reduce((sum, item) => sum + (item.total_ventas || 0), 0);
        const otrosClientes = otros.reduce((sum, item) => sum + (item.num_clientes || 0), 0);
        const otrosTransacciones = otros.reduce((sum, item) => sum + (item.num_transacciones || 0), 0);
        const otrosMB = otros.reduce((sum, item) => sum + (item.total_mb || 0), 0);
        
        pieData.push({
          name: 'Otros',
          value: otrosTotal,
          percentage: totalVentas > 0 ? (otrosTotal / totalVentas * 100).toFixed(1) : 0,
          color: COLORS[5 % COLORS.length],
          num_clientes: otrosClientes,
          num_transacciones: otrosTransacciones,
          total_mb: otrosMB,
          is_others: true,
          otros_count: otros.length,
          formattedValue: formatCurrency(otrosTotal),
          shortValue: formatCurrencyShort(otrosTotal)
        });
      }
      
      return pieData;
    }
    
    return [];
  };
  
  // Tooltip pie (sin cambios)
  const PieTooltipEnhanced = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip pie-tooltip-enhanced">
          <div className="tooltip-header">
            <div 
              className="tooltip-color-indicator" 
              style={{ backgroundColor: data.color }}
            ></div>
            <span className="tooltip-title">{data.name}</span>
          </div>
          
          <div className="tooltip-body">
            <div className="tooltip-row primary">
              <span className="tooltip-label">Ventas:</span>
              <span className="tooltip-value">{data.formattedValue}</span>
            </div>
            
            <div className="tooltip-row">
              <span className="tooltip-label">Porcentaje:</span>
              <span className="tooltip-value bold">{data.percentage}%</span>
            </div>
            
            <div className="tooltip-row">
              <span className="tooltip-label">Clientes:</span>
              <span className="tooltip-value">{data.num_clientes}</span>
            </div>
            
            <div className="tooltip-row">
              <span className="tooltip-label">Transacciones:</span>
              <span className="tooltip-value">{data.num_transacciones}</span>
            </div>
            
            {data.is_others && (
              <div className="tooltip-footer">
                <small>Agrupa {data.otros_count} tipos de cliente</small>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };
  
  // Función renderPieLabel (sin cambios)
  const renderPieLabel = ({ name, percentage, shortValue }) => {
    if (parseFloat(percentage) < 3) return '';
    return `${name.length > 15 ? name.substring(0, 12) + '...' : name}: ${shortValue}`;
  };

  // FUNCIÓN MEJORADA PARA PROCESAR DATOS DE ADQUISICIÓN CON DEBUGGING
  const processAcquisitionData = () => {
    console.log('🔍 === PROCESANDO DATOS DE ADQUISICIÓN ===');
    console.log('📊 acquisitionData:', acquisitionData);
    console.log('📊 Tipo:', typeof acquisitionData);
    console.log('📊 Es array:', Array.isArray(acquisitionData));
    console.log('📊 Longitud:', acquisitionData?.length);
    
    if (!acquisitionData || !Array.isArray(acquisitionData) || acquisitionData.length === 0) {
      console.warn('⚠️ No hay datos de adquisición válidos para procesar');
      return [];
    }

    const formatMonthName = (monthString) => {
      if (!monthString) return 'Mes desconocido';
      
      // Si ya viene formateado
      if (monthString.length < 7 && monthString.includes(' ')) {
        return monthString;
      }
      
      // Formato YYYY-MM
      if (monthString.length >= 7 && monthString.includes('-')) {
        const [year, month] = monthString.split('-');
        const monthNames = [
          'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
          'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
        ];
        
        const monthIndex = parseInt(month) - 1;
        if (monthIndex >= 0 && monthIndex < 12) {
          return `${monthNames[monthIndex]} ${year.slice(-2)}`;
        }
      }
      
      return monthString;
    };

    // Procesar cada elemento con logging extenso
    const processedData = acquisitionData.map((item, index) => {
      console.log(`📊 Procesando item ${index + 1}:`, item);
      
      // Extraer datos con múltiples fallbacks
      const mes = item.mes || item.month || item.periodo || '';
      const nuevosClientes = item.nuevos_clientes || item.total || item.clientes || item.value || 0;
      
      const processed = {
        mes: mes,
        mesFormateado: formatMonthName(mes),
        total: parseInt(nuevosClientes) || 0,
        nuevos_clientes: parseInt(nuevosClientes) || 0
      };
      
      console.log(`   ➤ Procesado:`, processed);
      return processed;
    });

    // Filtrar elementos válidos
    const validData = processedData.filter(item => {
      const isValid = item.total > 0 && item.mes;
      console.log(`📊 Item ${item.mes}: válido=${isValid} (total=${item.total})`);
      return isValid;
    });

    // Ordenar por mes
    const sortedData = validData.sort((a, b) => a.mes.localeCompare(b.mes));
    
    console.log('✅ DATOS FINALES PARA RENDERIZAR:', sortedData);
    return sortedData.slice(-12); // Últimos 12 meses
  };

  // Tooltip personalizado para adquisición
  const AcquisitionTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="custom-tooltip acquisition-tooltip">
          <div className="tooltip-label">{label}</div>
          <div className="tooltip-metric primary">
            <span style={{ color: data.color }}>●</span>
            Nuevos Clientes: <strong>{data.value}</strong>
          </div>
          <div className="tooltip-footer">
            <small>Datos reales del CSV cargado</small>
          </div>
        </div>
      );
    }
    return null;
  };

  // Componentes de carga y error (sin cambios)
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

  const processedAcquisition = processAcquisitionData();

  return (
    <div className="dashboard-layout">
      <Sidebar userRole={userRole} onLogout={onLogout} />
      <div className="dashboard-content">
        <div className="clients-container">
          <h1 className="titulo">Análisis de Clientes</h1>
          
         
          
          {/* Grid superior con 2 columnas - SIN CAMBIOS */}
          <div className="dashboard-grid-two-columns">
            
            {/* 1. Ventas por tipo de cliente MEJORADO - SIN CAMBIOS */}
            <div className="card">
              <h2>Ventas por Tipo de Cliente</h2>
              
              {/* Estadísticas superiores mejoradas */}
              {salesByTypeDetailed?.resumen && (
                <div className="pie-stats-header enhanced">
                  <div className="pie-stat-item enhanced">
                    <div className="pie-stat-value enhanced">{salesByTypeDetailed.resumen.total_tipos}</div>
                    <div className="pie-stat-label enhanced">TOTAL TIPOS</div>
                  </div>
                  <div className="pie-stat-item enhanced">
                    <div className="pie-stat-value enhanced">{formatCurrency(salesByTypeDetailed.resumen.total_ventas)}</div>
                    <div className="pie-stat-label enhanced">VENTAS TOTALES</div>
                  </div>
                </div>
              )}
              
              <div className="chart-placeholder pie-chart-container">
                {(() => {
                  const pieData = processPieData();
                  console.log('🔍 Datos procesados para pie:', pieData);
                  
                  return pieData.length > 0 ? (
                    <div className="pie-chart-wrapper">
                      <ResponsiveContainer width="100%" height={320}>
                        <PieChart margin={{ top: 20, right: 20, left: 20, bottom: 20 }}>
                          <Pie
                            data={pieData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={renderPieLabel}
                            outerRadius={100}
                            innerRadius={30}
                            fill="#8884d8"
                            dataKey="value"
                            stroke="#fff"
                            strokeWidth={2}
                          >
                            {pieData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip content={<PieTooltipEnhanced />} />
                        </PieChart>
                      </ResponsiveContainer>
                      
                      {/* Leyenda personalizada como en la imagen */}
                      <div className="pie-legend-custom">
                        {pieData.map((entry, index) => (
                          <div key={index} className="pie-legend-item">
                            <div 
                              className="pie-legend-color" 
                              style={{ backgroundColor: entry.color }}
                            ></div>
                            <div className="pie-legend-content">
                              <span className="pie-legend-name">
                                {entry.name}{entry.is_others ? ` (${entry.otros_count} tipos)` : ''}
                              </span>
                              <span className="pie-legend-value">
                                {entry.shortValue}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="placeholder-text">
                      📊 No hay datos de tipos de cliente disponibles
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* 2. Top 10 clientes más rentables - SIN CAMBIOS */}
            <div className="card">
              <h2>Top 10 clientes más rentables</h2>
              
              {/* Estadísticas de resumen */}
              {profitableData.length > 0 && (
                <div className="profitable-stats-header">
                  <div className="profitable-stat">
                    <span className="stat-value">
                      {formatCurrency(profitableData.reduce((sum, client) => sum + client.total_ventas, 0))}
                    </span>
                    <span className="stat-label">VENTAS TOP 10</span>
                  </div>
                  <div className="profitable-stat">
                    <span className="stat-value">
                      {profitableData.length > 0 ? 
                        (profitableData.reduce((sum, client) => sum + client.rentabilidad_porcentaje, 0) / profitableData.length).toFixed(1) 
                        : 0}%
                    </span>
                    <span className="stat-label">MARGEN PROMEDIO</span>
                  </div>
                </div>
              )}
              
              <div className="chart-placeholder">
                {profitableData.length > 0 ? (
                  <div className="profitable-clients-list enhanced">
                    {profitableData.slice(0, 10).map((client, index) => (
                      <div key={index} className={`profitable-client-item enhanced rank-${index + 1}`}>
                        <div className="client-info enhanced">
                          <div className="client-ranking">#{client.ranking}</div>
                          <div className="client-details">
                            <span className="client-name enhanced">
                              {client.cliente || 'Cliente sin nombre'}
                            </span>
                            <span className="client-type enhanced">
                              ({client.tipo_cliente || 'Sin tipo'})
                            </span>
                          </div>
                        </div>
                        <div className="client-metrics enhanced">
                          <span className="client-sales enhanced">
                            {formatCurrency(client.total_ventas || 0)}
                          </span>
                          <span className="client-margin enhanced">
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


          {/* GRÁFICO DE TENDENCIA ESTRUCTURADO COMO EN LA IMAGEN */}
          <div className="full-width-card acquisition-chart">
            <h2>Tendencia de Adquisición de Nuevos Clientes</h2>
            
            <div className="chart-placeholder">
              {processedAcquisition.length > 0 ? (
                <>
                  {/* Estadísticas superiores restructuradas */}
                  <div className="acquisition-stats-header">
                    <div className="acquisition-stat-item total">
                      <div className="stat-number">{processedAcquisition.reduce((sum, item) => sum + item.total, 0)}</div>
                      <div className="stat-label">TOTAL NUEVOS CLIENTES</div>
                    </div>
                    <div className="acquisition-stat-item average">
                      <div className="stat-number">{Math.round(processedAcquisition.reduce((sum, item) => sum + item.total, 0) / processedAcquisition.length)}</div>
                      <div className="stat-label">PROMEDIO MENSUAL</div>
                    </div>
                    <div className="acquisition-stat-item best">
                      <div className="stat-number">{Math.max(...processedAcquisition.map(item => item.total))}</div>
                      <div className="stat-label">MEJOR MES</div>
                    </div>
                    <div className="acquisition-stat-item trend">
                      <div className={`stat-number ${(() => {
                        if (processedAcquisition.length >= 2) {
                          const first = processedAcquisition[0].total;
                          const last = processedAcquisition[processedAcquisition.length - 1].total;
                          return (last - first) >= 0 ? 'trend-positive' : 'trend-negative';
                        }
                        return 'trend-neutral';
                      })()}`}>
                        {(() => {
                          if (processedAcquisition.length >= 2) {
                            const first = processedAcquisition[0].total;
                            const last = processedAcquisition[processedAcquisition.length - 1].total;
                            const change = ((last - first) / first * 100);
                            return `${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
                          }
                          return '0.0%';
                        })()}
                      </div>
                      <div className="stat-label">TENDENCIA GENERAL</div>
                    </div>
                  </div>

                  {/* Gráfico principal restructurado */}
                  <div className="acquisition-chart-main">
                    {(() => {
                      // Calcular promedio móvil de 3 meses
                      const dataWithMovingAvg = processedAcquisition.map((item, index) => {
                        let promedioMovil;
                        if (index < 2) {
                          promedioMovil = item.total;
                        } else {
                          const avg = (
                            processedAcquisition[index - 2].total + 
                            processedAcquisition[index - 1].total + 
                            item.total
                          ) / 3;
                          promedioMovil = Math.round(avg);
                        }
                        
                        return {
                          ...item,
                          promedioMovil: promedioMovil
                        };
                      });

                      return (
                        <ResponsiveContainer width="100%" height={400}>
                          <LineChart 
                            data={dataWithMovingAvg}
                            margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                          >
                            {/* Grid más sutil */}
                            <CartesianGrid strokeDasharray="1 1" />
                            
                            {/* Ejes limpios */}
                            <XAxis 
                              dataKey="mesFormateado"
                              tick={{ fontSize: 11, fill: '#8e9aaf', fontWeight: 500 }}
                              angle={-45}
                              textAnchor="end"
                              height={80}
                              interval={0}
                              axisLine={{ stroke: '#e4e6ea', strokeWidth: 1 }}
                              tickLine={{ stroke: '#e4e6ea', strokeWidth: 1 }}
                            />
                            <YAxis 
                              tick={{ fontSize: 11, fill: '#8e9aaf', fontWeight: 500 }}
                              axisLine={{ stroke: '#e4e6ea', strokeWidth: 1 }}
                              tickLine={{ stroke: '#e4e6ea', strokeWidth: 1 }}
                              domain={[0, 'dataMax + 1']}
                              label={{ 
                                value: 'Nuevos Clientes', 
                                angle: -90, 
                                position: 'insideLeft',
                                style: { textAnchor: 'middle', fill: '#8e9aaf', fontSize: '12px', fontWeight: 500 }
                              }}
                            />
                            
                            {/* Tooltip estructurado */}
                            <Tooltip 
                              content={({ active, payload, label }) => {
                                if (active && payload && payload.length) {
                                  const nuevosData = payload.find(p => p.dataKey === 'total');
                                  const promedioData = payload.find(p => p.dataKey === 'promedioMovil');
                                  
                                  return (
                                    <div className="acquisition-tooltip-structured">
                                      <div className="tooltip-header-structured">
                                        {label}
                                      </div>
                                      <div className="tooltip-metrics-structured">
                                        {nuevosData && (
                                          <div className="tooltip-metric-structured">
                                            <div className="metric-indicator nuevos"></div>
                                            <span className="metric-text">Nuevos clientes:</span>
                                            <span className="metric-value">{nuevosData.value}</span>
                                          </div>
                                        )}
                                        {promedioData && (
                                          <div className="tooltip-metric-structured">
                                            <div className="metric-indicator promedio"></div>
                                            <span className="metric-text">Promedio móvil (3m):</span>
                                            <span className="metric-value">{promedioData.value}</span>
                                          </div>
                                        )}
                                        {nuevosData && (
                                          <div className="tooltip-metric-structured">
                                            <span className="metric-text">Crecimiento:</span>
                                            <span className="metric-value">
                                              {(() => {
                                                const currentIndex = dataWithMovingAvg.findIndex(d => d.mesFormateado === label);
                                                if (currentIndex > 0) {
                                                  const prev = dataWithMovingAvg[currentIndex - 1].total;
                                                  const current = nuevosData.value;
                                                  const growth = ((current - prev) / prev * 100);
                                                  return `${growth > 0 ? '+' : ''}${growth.toFixed(1)}%`;
                                                }
                                                return '0.0%';
                                              })()}
                                            </span>
                                          </div>
                                        )}
                                      </div>
                                      <div className="tooltip-growth-structured">
                                        Comparado con el mes anterior
                                      </div>
                                    </div>
                                  );
                                }
                                return null;
                              }}
                            />
                            
                            {/* Línea principal - Nuevos Clientes */}
                            <Line 
                              type="monotone" 
                              dataKey="total" 
                              stroke="#2E8B57" 
                              strokeWidth={3}
                              name="Nuevos clientes por mes"
                              dot={{ 
                                r: 4, 
                                fill: "#2E8B57", 
                                stroke: "#ffffff", 
                                strokeWidth: 3
                              }}
                              activeDot={{ 
                                r: 6, 
                                stroke: "#2E8B57", 
                                strokeWidth: 3, 
                                fill: "#ffffff"
                              }}
                            />
                            
                            {/* Línea de tendencia suavizada */}
                            <Line 
                              type="monotone" 
                              dataKey="promedioMovil"
                              stroke="#4A90E2" 
                              strokeWidth={2}
                              strokeDasharray="5 5"
                              name="Tendencia suavizada (promedio 3 meses)"
                              dot={false}
                              activeDot={{ 
                                r: 4, 
                                stroke: "#4A90E2", 
                                strokeWidth: 2, 
                                fill: "#ffffff"
                              }}
                            />
                            
                          </LineChart>
                        </ResponsiveContainer>
                      );
                    })()}
                  </div>

                  {/* Leyenda restructurada */}
                  <div className="acquisition-legend-structured">
                    <div className="legend-item-structured">
                      <div className="legend-line-structured solid"></div>
                      <span className="legend-text-structured">Nuevos clientes por mes</span>
                    </div>
                    <div className="legend-item-structured">
                      <div className="legend-line-structured dashed"></div>
                      <span className="legend-text-structured">Tendencia suavizada (promedio 3 meses)</span>
                    </div>
                  </div>

                  {/* Footer restructurado */}
                  <div className="acquisition-footer-structured">
                    <div className="footer-tip-structured">
                      💡 Pasa el cursor sobre los puntos para ver detalles y crecimiento mensual
                    </div>
                  </div>
                </>
              ) : (
                <div className="enhanced-placeholder">
                  <div className="placeholder-icon">📈</div>
                  <div className="placeholder-title">
                    No hay datos de tendencia disponibles
                  </div>
                  <div className="placeholder-subtitle">
                    El CSV cargado no contiene fechas válidas para análisis temporal.
                  </div>
                  
                  {/* Información de debug */}
                  {acquisitionDebug && (
                    <div className="debug-info-placeholder">
                      <strong>📋 Información de diagnóstico:</strong>
                      <ul>
                        <li>Registros totales: {acquisitionDebug.total_records}</li>
                        <li>Fechas únicas: {acquisitionDebug.sample_dates?.length || 0}</li>
                        <li>Clientes con fechas: {acquisitionDebug.first_purchases_sample?.length || 0}</li>
                      </ul>
                      
                      {acquisitionDebug.sample_dates?.length > 0 && (
                        <div>
                          <strong>Ejemplos de fechas encontradas:</strong>
                          <ul>
                            {acquisitionDebug.sample_dates.slice(0, 3).map((item, index) => (
                              <li key={index}>"{item.fecha}" ({item.count} veces)</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className="placeholder-action">
                    <p><strong>Para mostrar la tendencia:</strong></p>
                    <ul>
                      <li>Asegúrate de que el CSV tenga una columna 'Fecha'</li>
                      <li>Las fechas deben estar en formato válido (YYYY-MM-DD o DD/MM/YYYY)</li>
                      <li>Debe haber clientes distribuidos en diferentes meses</li>
                    </ul>
                    <div className="placeholder-buttons">
                      <button onClick={fetchAllAnalytics} className="retry-button primary">
                        🔄 Recargar datos
                      </button>
                      <button onClick={debugAcquisition} className="retry-button secondary">
                        🐛 Debug adicional
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Clients;