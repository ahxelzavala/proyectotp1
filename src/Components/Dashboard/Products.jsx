import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, 
  LineChart, Line, ComposedChart 
} from 'recharts';
import './Products.css';
import Sidebar from './Sidebar';

const Products = ({ userRole, onLogout }) => {
  const [comparativeData, setComparativeData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [rotationData, setRotationData] = useState([]);
  const [paretoData, setParetoData] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('12m');

  useEffect(() => {
    fetchAllData();
  }, [selectedPeriod]);

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
      const response = await fetch(`http://localhost:8000/products/analytics/comparative-bars?period=${selectedPeriod}&limit=10`);
      if (response.ok) {
        const data = await response.json();
        setComparativeData(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching comparative data:', error);
    }
  };

  const fetchTrendData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/products/analytics/trend-lines?top_products=6&period=${selectedPeriod}`);
      if (response.ok) {
        const data = await response.json();
        setTrendData(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching trend data:', error);
    }
  };

  const fetchRotationData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/products/analytics/rotation-speed?period=${selectedPeriod}&limit=10`);
      if (response.ok) {
        const data = await response.json();
        setRotationData(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching rotation data:', error);
      // Simular datos de rotación si no existe el endpoint
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
      const response = await fetch(`http://localhost:8000/products/analytics/pareto-80-20?period=${selectedPeriod}`);
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
    const monthlyData = {};
    
    trendData.forEach(item => {
      if (!monthlyData[item.mes]) {
        monthlyData[item.mes] = { mes: item.mes };
      }
      monthlyData[item.mes][item.producto] = item.ventas_mes;
    });
    
    return Object.values(monthlyData).sort((a, b) => a.mes.localeCompare(b.mes));
  };

  // Obtener productos únicos para las líneas
  const uniqueProducts = [...new Set(trendData.map(item => item.producto))].slice(0, 6);

  // Preparar datos de Pareto con mejor formato
  const paretoChartData = paretoData.slice(0, 12).map((item, index) => ({
    ...item,
    producto_corto: item.producto?.length > 12 ? item.producto.substring(0, 12) + '...' : item.producto,
    participacion_acumulada_num: parseFloat(item.participacion_acumulada) || 0,
    rank: index + 1
  }));

  // Preparar datos de rotación con nombres cortos
  const rotationChartData = rotationData.slice(0, 8).map(item => ({
    ...item,
    producto_corto: item.producto?.length > 15 ? item.producto.substring(0, 15) + '...' : item.producto,
    color: item.categoria === 'Rápida' ? '#27ae60' : item.categoria === 'Media' ? '#f39c12' : '#e74c3c'
  }));

  // Preparar datos comparativos con nombres cortos
  const comparativeChartData = comparativeData.slice(0, 8).map(item => ({
    ...item,
    producto_corto: item.producto?.length > 12 ? item.producto.substring(0, 12) + '...' : item.producto
  }));

  const getPeriodLabel = () => {
    switch(selectedPeriod) {
      case '3m': return 'Últimos 3 meses';
      case '6m': return 'Últimos 6 meses';
      case '12m': return 'Últimos 12 meses';
      default: return 'Período seleccionado';
    }
  };

  if (dataLoading) {
    return (
      <div className="dashboard-layout">
        <Sidebar userRole={userRole} onLogout={onLogout} />
        <div className="dashboard-content">
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Cargando análisis de productos...</p>
            <p>Aplicando filtros de {getPeriodLabel().toLowerCase()}...</p>
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
          
          {/* Header Simple como en Clientes */}
          <div className="page-header">
            <h1 className="titulo">Análisis de Productos</h1>
          </div>
          
          {/* Period Selector */}
          <div className="period-selector-container">
            <select 
              value={selectedPeriod} 
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="period-selector"
            >
              <option value="3m">Últimos 3 meses</option>
              <option value="6m">Últimos 6 meses</option>
              <option value="12m">Últimos 12 meses</option>
            </select>
          </div>

          {/* Charts Grid - 4 Gráficos */}
          <div className="charts-grid">
            
            {/* 1. Top Productos por Ventas */}
            <div className="chart-section">
              <h3>🏆 Top Productos por Ventas</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={comparativeChartData} margin={{ top: 20, right: 30, left: 20, bottom: 120 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="producto_corto" 
                    angle={-45} 
                    textAnchor="end" 
                    height={120}
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
            </div>

            {/* 2. Tendencias de Ventas */}
            <div className="chart-section">
              <h3>📈 Tendencias de Ventas por Mes</h3>
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
            </div>

            {/* 3. Velocidad de Rotación */}
            <div className="chart-section">
              <h3>⚡ Velocidad de Rotación</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={rotationChartData} margin={{ top: 20, right: 30, left: 20, bottom: 120 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="producto_corto" 
                    angle={-45} 
                    textAnchor="end" 
                    height={120}
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
                            <p style={{ color: data.color }}>{`Velocidad: ${data.velocidad_rotacion.toFixed(1)} rotaciones/mes`}</p>
                            <p>{`Categoría: ${data.categoria}`}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar 
                    dataKey="velocidad_rotacion" 
                    fill="#4ECDC4"
                    radius={[6, 6, 0, 0]}
                    name="Velocidad de Rotación"
                  />
                </BarChart>
              </ResponsiveContainer>
              <div style={{ textAlign: 'center', marginTop: '15px', fontSize: '12px', color: '#666' }}>
                <span style={{ color: '#27ae60', fontWeight: 'bold' }}>● Rápida (&gt;6)</span>{' '}
                <span style={{ color: '#f39c12', fontWeight: 'bold' }}>● Media (3-6)</span>{' '}
                <span style={{ color: '#e74c3c', fontWeight: 'bold' }}>● Lenta (&lt;3)</span>
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