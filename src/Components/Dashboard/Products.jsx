import React, { useState, useEffect } from 'react';
import './Products.css';
import Sidebar from './Sidebar';

const Products = ({ userRole, onLogout }) => {
  const [productData, setProductData] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    fetchProductData();
  }, []);

  const fetchProductData = async () => {
    setDataLoading(true);
    try {
      const response = await fetch('http://localhost:8000/client-data');
      if (response.ok) {
        const data = await response.json();
        
        // Procesar datos para productos
        const productsByValue = data
          .filter(item => item.product)
          .reduce((acc, item) => {
            if (!acc[item.product]) {
              acc[item.product] = {
                id: item.id,
                name: item.product,
                value: 0,
                description: item.description || 'Sin descripción'
              };
            }
            acc[item.product].value += item.value || 0;
            return acc;
          }, {});
        
        const topProducts = Object.values(productsByValue)
          .sort((a, b) => b.value - a.value);
        
        setProductData(topProducts);
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
        <div className="products-container">
          <h1 className="titulo">Gestión de Productos</h1>
          
          <div className="dashboard-grid">
            <div className="card">
              <h2>Todos los Productos</h2>
              <div className="chart-placeholder">
                {dataLoading ? (
                  <div className="placeholder-text">Cargando datos...</div>
                ) : productData.length > 0 ? (
                  <div className="product-list">
                    {productData.map(product => (
                      <div key={product.id} className="product-item">
                        <span className="product-name">{product.name}</span>
                        <span className="product-value">${product.value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="placeholder-text">No hay datos disponibles</div>
                )}
              </div>
            </div>

            <div className="card">
              <h2>Productos Más Vendidos</h2>
              <div className="chart-placeholder">
                <div className="placeholder-text">Gráfico de productos más vendidos</div>
              </div>
            </div>

            <div className="card">
              <h2>Análisis de Productos</h2>
              <div className="chart-placeholder">
                <div className="placeholder-text">Análisis de rendimiento</div>
              </div>
            </div>

            <div className="card">
              <h2>Productos Recomendados</h2>
              <div className="chart-placeholder">
                <div className="placeholder-text">Sistema de recomendaciones</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Products;