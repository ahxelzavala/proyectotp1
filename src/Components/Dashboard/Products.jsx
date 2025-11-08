import config from '../../config';
import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, 
  LineChart, Line, ComposedChart, Cell
} from 'recharts';
import './Products.css';
import Sidebar from './Sidebar';

const API_URL = config.API_URL;

const Products = ({ userRole, onLogout }) => {
  const [comparativeData, setComparativeData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [rotationData, setRotationData] = useState([]);
  const [paretoData, setParetoData] = useState([]);
  const [topProducts, setTopProducts] = useState([]); 
  const [dataLoading, setDataLoading] = useState(true);

  const [loadingComparative, setLoadingComparative] = useState(false);
  const [loadingTop, setLoadingTop] = useState(false);
  const [loadingTrend, setLoadingTrend] = useState(false);
  const [loadingRotation, setLoadingRotation] = useState(false);
  const [loadingPareto, setLoadingPareto] = useState(false);


  // Métricas generales
  const [metrics, setMetrics] = useState({
    totalSales: 0,
    totalMargin: 0,
    bestProduct: 'N/A',
    avgProfitability: 0
  });

  useEffect(() => {
    fetchAllData();
        loadComparativeBars();
    loadTopProducts();
    loadTrendData();

  }, []);

  const fetchAllData = async () => {
    setDataLoading(true);
    try {
      await Promise.all([
        fetchComparativeData(),
        fetchTrendData(),
        fetchRotationData(),
        fetchParetoData()
      ]);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setDataLoading(false);
    }
  };

  const fetchComparativeData = async () => {
    try {
      
      const response = await fetch(`${API_URL}/products/analytics/comparative-bars?limit=10`);
      if (response.ok) {
        const data = await response.json();
        setComparativeData(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching comparative data:', error);
    }
  };

  const loadComparativeBars = async () => {
  try {
    setLoadingComparative(true);
    // CAMBIO: Quitar :1 del final
    const response = await fetch(`${API_URL}/products/analytics/comparative-bars?limit=10`);
    
    if (!response.ok) {
      throw new Error('Error cargando datos comparativos');
    }
    
    const data = await response.json();
    console.log('📊 Datos comparative-bars:', data);
    
    // Verificar que haya datos
    if (data && Array.isArray(data) && data.length > 0) {
      setComparativeData(data);
    } else {
      console.warn('⚠️ No hay datos para comparative-bars');
      setComparativeData([]);
    }
  } catch (error) {
    console.error('Error loading comparative data:', error);
    setComparativeData([]);
  } finally {
    setLoadingComparative(false);
  }
};

  const fetchTrendData = async () => {
  setLoadingTrend(true);
  try {
    console.log('📈 [TREND-FRONTEND] Llamando trend-lines...');
    
    const response = await fetch(
      `${API_URL}/products/analytics/trend-lines?top_products=6`
    );
    
    console.log('📡 [TREND-FRONTEND] Status:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    console.log('📊 [TREND-FRONTEND] Data recibida:', data);
    console.log('📊 [TREND-FRONTEND] Es array?', Array.isArray(data));
    console.log('📊 [TREND-FRONTEND] Length:', data?.length);
    
    // Backend devuelve array directo
    if (Array.isArray(data) && data.length > 0) {
      console.log('✅ [TREND-FRONTEND] Seteando', data.length, 'registros');
      console.log('📋 [TREND-FRONTEND] Primeros 3:', data.slice(0, 3));
      setTrendData(data);
    } else if (data && data.trends && Array.isArray(data.trends)) {
      // Por si acaso viene en formato {trends: [...]}
      console.log('✅ [TREND-FRONTEND] Usando data.trends');
      setTrendData(data.trends);
    } else if (data && data.data && Array.isArray(data.data)) {
      // Por si acaso viene en formato {data: [...]}
      console.log('✅ [TREND-FRONTEND] Usando data.data');
      setTrendData(data.data);
    } else {
      console.warn('⚠️ [TREND-FRONTEND] Formato inesperado:', data);
      setTrendData([]);
    }
    
  } catch (error) {
    console.error('❌ [TREND-FRONTEND] Error:', error);
    setTrendData([]);
  } finally {
    setLoadingTrend(false);
  }
};

  const fetchRotationData = async () => {
    try {
      const response = await fetch(`${API_URL}/products/analytics/rotation-speed`);

      if (response.ok) {
        const data = await response.json();
        setRotationData(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching rotation data:', error);
      // Mantener datos de ejemplo si el endpoint no funciona
      setRotationData([
        { producto: 'NATROSOL 250 LR - 25 KG', velocidad_rotacion: 8.5, categoria: 'Rápida' },
        { producto: 'BYK 037 - 185 KG', velocidad_rotacion: 7.2, categoria: 'Rápida' },
        { producto: 'KRONOS 2360 - 25 KG', velocidad_rotacion: 6.8, categoria: 'Media' },
        { producto: 'CLAYTONE APA - 12.500 KG', velocidad_rotacion: 5.4, categoria: 'Media' },
        { producto: 'TEXANOL - 200 KG', velocidad_rotacion: 4.1, categoria: 'Lenta' },
        { producto: 'EPOXI RESIN SM 90FR', velocidad_rotacion: 3.8, categoria: 'Media' },
        { producto: 'TITANIO DIOXIDO', velocidad_rotacion: 3.2, categoria: 'Media' },
        { producto: 'HEXAMETAFOSFATO DE SODIO', velocidad_rotacion: 2.9, categoria: 'Lenta' }
      ]);
    }
  };

  const fetchParetoData = async () => {
    try {
      const response = await fetch(`${API_URL}/products/analytics/pareto-80-20`);
      if (response.ok) {
        const data = await response.json();
        setParetoData(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching pareto data:', error);
    }
  };

  const formatCurrency = (value) => {
    if (typeof value !== 'number') return 'S/ 0';
    return new Intl.NumberFormat('es-PE', {
      style: 'currency',
      currency: 'PEN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatNumber = (value) => {
    if (typeof value !== 'number') return '0';
    return new Intl.NumberFormat('es-PE').format(value);
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="label">{`${label}`}</p>
          {payload.map((pld, index) => (
            <p key={index} style={{ color: pld.color }}>
              {`${pld.dataKey}: ${
                pld.dataKey.includes('ventas') || pld.dataKey.includes('margen') || pld.dataKey.includes('total') 
                ? formatCurrency(pld.value) 
                : typeof pld.value === 'number' 
                ? pld.value.toFixed(1) 
                : pld.value
              }`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#FF7C7C'];

  // Procesar datos de tendencia para el gráfico de líneas
  const processedTrendData = () => {
  console.log('🔄 [PROCESS-TREND] Procesando trendData...', trendData.length, 'registros');
  
  if (!trendData || trendData.length === 0) {
    console.warn('⚠️ [PROCESS-TREND] trendData está vacío');
    return [];
  }
  
  const monthlyData = {};
  
  trendData.forEach((item, index) => {
    if (!item.mes || !item.producto) {
      console.warn('⚠️ [PROCESS-TREND] Item sin mes o producto:', item);
      return;
    }
    
    if (!monthlyData[item.mes]) {
      monthlyData[item.mes] = { mes: item.mes };
    }
    monthlyData[item.mes][item.producto] = item.ventas_mes;
    
    // Log primeros 3 para debug
    if (index < 3) {
      console.log(`  📌 ${item.producto} - ${item.mes}: S/ ${item.ventas_mes}`);
    }
  });
  
  const result = Object.values(monthlyData).sort((a, b) => a.mes.localeCompare(b.mes));
  
  console.log('✅ [PROCESS-TREND] Procesados', result.length, 'meses');
  if (result.length > 0) {
    console.log('📋 [PROCESS-TREND] Primer mes:', result[0]);
  }
  
  return result;
};

  // Obtener productos únicos para las líneas
 const uniqueProducts = React.useMemo(() => {
  console.log('🔄 [UNIQUE-PRODUCTS] Calculando productos únicos...');
  
  if (!trendData || trendData.length === 0) {
    console.warn('⚠️ [UNIQUE-PRODUCTS] trendData vacío');
    return [];
  }
  
  const products = [...new Set(trendData.map(item => item.producto))].slice(0, 6);
  console.log('✅ [UNIQUE-PRODUCTS] Productos:', products);
  
  return products;
}, [trendData]);

  // Preparar datos de Pareto con mejor formato
  const paretoChartData = paretoData.slice(0, 12).map((item, index) => ({
    ...item,
    producto_corto: item.producto?.length > 12 ? item.producto.substring(0, 12) + '...' : item.producto,
    participacion_acumulada_num: parseFloat(item.participacion_acumulada) || 0,
    rank: index + 1
  }));

  // Preparar datos de rotación con nombres cortos y colores individuales
  const rotationChartData = rotationData.slice(0, 8).map(item => {
    let color;
    if (item.categoria === 'Rápida' || item.velocidad_rotacion >= 6.0) {
      color = '#27ae60';
    } else if (item.categoria === 'Media' || (item.velocidad_rotacion >= 3.0 && item.velocidad_rotacion < 6.0)) {
      color = '#f39c12';
    } else {
      color = '#e74c3c';
    }
    
    return {
      ...item,
      producto_corto: item.producto?.length > 15 ? item.producto.substring(0, 15) + '...' : item.producto,
      color: color,
      categoria: item.categoria || (item.velocidad_rotacion >= 6.0 ? 'Rápida' : item.velocidad_rotacion >= 3.0 ? 'Media' : 'Lenta')
    };
  });


const loadTopProducts = async () => {
  try {
    setLoadingTop(true);
    // CAMBIO: Quitar :1 y usar endpoint correcto
    const response = await fetch(`${API_URL}/products/analytics/top_products_6`);
    
    if (!response.ok) {
      throw new Error('Error cargando top productos');
    }
    
    const data = await response.json();
    console.log('🏆 Datos top productos:', data);
    
    // Verificar formato de respuesta
    if (data && data.products && Array.isArray(data.products)) {
      setTopProducts(data.products);
    } else if (Array.isArray(data)) {
      setTopProducts(data);
    } else {
      console.warn('⚠️ No hay datos para top productos');
      setTopProducts([]);
    }
  } catch (error) {
    console.error('Error loading top products:', error);
    setTopProducts([]);
  } finally {
    setLoadingTop(false);
  }
};



const loadTrendData = async () => {
  try {
    setLoadingTrend(true);
    // CAMBIO: Quitar :1
    const response = await fetch(`${API_URL}/products/analytics/trend-lines`);
    
    if (!response.ok) {
      throw new Error('Error cargando tendencias');
    }
    
    const data = await response.json();
    console.log('📈 Datos tendencias:', data);
    
    if (data && data.trends && Array.isArray(data.trends)) {
      setTrendData(data.trends);
    } else if (Array.isArray(data)) {
      setTrendData(data);
    } else {
      console.warn('⚠️ No hay datos de tendencias');
      setTrendData([]);
    }
  } catch (error) {
    console.error('Error loading trend data:', error);
    setTrendData([]);
  } finally {
    setLoadingTrend(false);
  }
};


  // Preparar datos comparativos con nombres cortos
  const comparativeChartData = comparativeData.slice(0, 8).map(item => ({
    ...item,
    producto_corto: item.producto?.length > 12 ? item.producto.substring(0, 12) + '...' : item.producto
  }));

  if (dataLoading) {
    return (
      <div className="dashboard-layout">
        <Sidebar userRole={userRole} onLogout={onLogout} />
        <div className="dashboard-content">
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Cargando análisis de productos...</p>
            <p>Procesando datos...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      <Sidebar userRole={userRole} onLogout={onLogout} />
      <div className="dashboard-content">
        <div className="products-container">
          
          {/* Header Simple */}
          <div className="page-header">
            <h1 className="titulo">Análisis de Productos</h1>
          </div>

          {/* Charts Grid - 4 Gráficos */}
          <div className="charts-grid">
            
            {/* 1. Top Productos por Ventas */}
            <div className="chart-section">
              <h3>🏆 Top Productos por Ventas</h3>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={comparativeChartData} margin={{ top: 20, right: 30, left: 20, bottom: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="producto_corto" 
                    angle={-45} 
                    textAnchor="end" 
                    height={100}
                    fontSize={10}
                    interval={0}
                    tick={{ fontSize: 10 }}
                  />
                  <YAxis tickFormatter={formatCurrency} fontSize={10} />
                  <Tooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="custom-tooltip">
                            <p className="label">{data.producto}</p>
                            <p style={{ color: '#8884d8' }}>{`Ventas: ${formatCurrency(data.total_ventas)}`}</p>
                            <p style={{ color: '#82ca9d' }}>{`Margen: ${formatCurrency(data.total_margen)}`}</p>
                            <p>{`Facturas: ${data.num_facturas || 'N/A'}`}</p>
                            <p>{`Clientes: ${data.num_clientes || 'N/A'}`}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend />
                  <Bar dataKey="total_ventas" fill="#8884d8" name="Ventas" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="total_margen" fill="#82ca9d" name="Margen Bruto" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              
              {/* Estadísticas adicionales */}
              <div className="chart-stats">
                <div className="stat-item">
                  <span className="stat-label">💰 Total Ventas:</span>
                  <span className="stat-value">
                    {formatCurrency(comparativeChartData.reduce((sum, item) => sum + (item.total_ventas || 0), 0))}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">📈 Total Margen:</span>
                  <span className="stat-value">
                    {formatCurrency(comparativeChartData.reduce((sum, item) => sum + (item.total_margen || 0), 0))}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">🏆 Mejor Producto:</span>
                  <span className="stat-value">
                    {comparativeChartData[0]?.producto_corto || 'N/A'}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">📊 Rentabilidad Promedio:</span>
                  <span className="stat-value">
                    {comparativeChartData.length > 0 
                      ? `${((comparativeChartData.reduce((sum, item) => sum + ((item.total_margen || 0) / (item.total_ventas || 1)), 0) / comparativeChartData.length) * 100).toFixed(1)}%`
                      : 'N/A'
                    }
                  </span>
                </div>
              </div>
            </div>

            {/* 2. Tendencias de Ventas */}
            <div className="chart-section">
  <h3>📈 Tendencias de Ventas por Mes</h3>
  
  {loadingTrend ? (
    <div style={{ textAlign: 'center', padding: '50px' }}>
      <p>Cargando tendencias...</p>
    </div>
  ) : trendData.length === 0 ? (
    <div style={{ textAlign: 'center', padding: '50px', color: '#6c757d' }}>
      <p>⚠️ No hay datos de tendencias disponibles</p>
    </div>
  ) : processedTrendData().length === 0 ? (
    <div style={{ textAlign: 'center', padding: '50px', color: '#6c757d' }}>
      <p>⚠️ Error procesando datos de tendencias</p>
      <p style={{ fontSize: '12px' }}>Datos raw: {trendData.length} registros</p>
    </div>
  ) : (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={processedTrendData()}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="mes" 
          fontSize={10}
          angle={-45}
          textAnchor="end"
          height={60}
        />
        <YAxis tickFormatter={formatCurrency} fontSize={10} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        {uniqueProducts.map((product, index) => (
          <Line 
            key={product}
            type="monotone" 
            dataKey={product} 
            stroke={COLORS[index % COLORS.length]}
            strokeWidth={3}
            dot={{ fill: COLORS[index % COLORS.length], r: 4 }}
            activeDot={{ r: 6, strokeWidth: 2 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )}
</div>

            {/* 3. Velocidad de Rotación */}
            <div className="chart-section">
              <h3>⚡ Velocidad de Rotación</h3>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={rotationChartData} margin={{ top: 20, right: 30, left: 20, bottom: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="producto_corto" 
                    angle={-45} 
                    textAnchor="end" 
                    height={100}
                    fontSize={10}
                    interval={0}
                  />
                  <YAxis 
                    label={{ value: 'Rotaciones/mes', angle: -90, position: 'insideLeft' }}
                    fontSize={10}
                  />
                  <Tooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="custom-tooltip">
                            <p className="label">{data.producto}</p>
                            <p style={{ color: data.color }}>
                              {`Velocidad: ${data.velocidad_rotacion.toFixed(1)} rotaciones/mes`}
                            </p>
                            <p>{`Categoría: ${data.categoria}`}</p>
                            <p>{`Facturas: ${data.total_facturas || 'N/A'}`}</p>
                            <p>{`Clientes únicos: ${data.clientes_unicos || 'N/A'}`}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar 
                    dataKey="velocidad_rotacion" 
                    radius={[6, 6, 0, 0]}
                    name="Velocidad de Rotación"
                  >
                    {rotationChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              
              {/* Estadísticas y leyenda mejorada */}
              <div className="rotation-summary">
                <div className="rotation-categories">
                  <div className="category-item rapid">
                    <span className="category-dot rapid"></span>
                    <span className="category-text">
                      <strong>Rápida (&gt;6.0)</strong>
                      <small>{rotationChartData.filter(item => item.categoria === 'Rápida').length} productos</small>
                    </span>
                  </div>
                  <div className="category-item medium">
                    <span className="category-dot medium"></span>
                    <span className="category-text">
                      <strong>Media (3.0-6.0)</strong>
                      <small>{rotationChartData.filter(item => item.categoria === 'Media').length} productos</small>
                    </span>
                  </div>
                  <div className="category-item slow">
                    <span className="category-dot slow"></span>
                    <span className="category-text">
                      <strong>Lenta (&lt;3.0)</strong>
                      <small>{rotationChartData.filter(item => item.categoria === 'Lenta').length} productos</small>
                    </span>
                  </div>
                </div>
                
                <div className="rotation-stats">
                  <div className="stat-group">
                    <span className="stat-label">📊 Velocidad Promedio:</span>
                    <span className="stat-value">
                      {rotationChartData.length > 0 
                        ? `${(rotationChartData.reduce((sum, item) => sum + item.velocidad_rotacion, 0) / rotationChartData.length).toFixed(1)} rot/mes`
                        : 'N/A'
                      }
                    </span>
                  </div>
                  <div className="stat-group">
                    <span className="stat-label">🏆 Más Rápido:</span>
                    <span className="stat-value">
                      {rotationChartData[0]?.producto_corto || 'N/A'} 
                      ({rotationChartData[0]?.velocidad_rotacion.toFixed(1) || '0'})
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* 4. Análisis de Pareto */}
            <div className="chart-section">
              <h3>📊 Análisis de Pareto (Regla 80/20)</h3>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={paretoChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="producto_corto" 
                    angle={-45} 
                    textAnchor="end" 
                    height={120}
                    fontSize={9}
                    interval={0}
                  />
                  <YAxis yAxisId="left" tickFormatter={formatCurrency} fontSize={10} />
                  <YAxis yAxisId="right" orientation="right" domain={[0, 100]} fontSize={10} />
                  <Tooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="custom-tooltip">
                            <p className="label">{data.producto}</p>
                            <p style={{ color: '#8884d8' }}>{`Ventas: ${formatCurrency(data.total_ventas)}`}</p>
                            <p style={{ color: '#ff7300' }}>{`% Acumulado: ${data.participacion_acumulada_num.toFixed(1)}%`}</p>
                            <p>{`Ranking: #${data.rank}`}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend />
                  <Bar 
                    yAxisId="left"
                    dataKey="total_ventas" 
                    fill="#8884d8" 
                    name="Ventas"
                    radius={[4, 4, 0, 0]}
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="participacion_acumulada_num" 
                    stroke="#ff7300" 
                    strokeWidth={3}
                    name="% Acumulado"
                    dot={{ fill: '#ff7300', r: 4 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
              <div style={{ textAlign: 'center', marginTop: '15px', fontSize: '12px', color: '#666' }}>
                <strong>Objetivo:</strong> Identificar el 20% de productos que generan el 80% de las ventas
              </div>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
};

export default Products;