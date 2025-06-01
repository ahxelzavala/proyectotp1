import React from 'react';
import './Dashboard.css';
import Sidebar from './Sidebar';

const Dashboard = () => {
  const clientData = [
    { id: 1, name: 'Cliente1', value: '1658.00' },
    { id: 2, name: 'Cliente2', value: '1658.00' },
    { id: 3, name: 'Cliente3', value: '1658.00' },
    { id: 4, name: 'Cliente4', value: '1658.00' }
  ];

  const productData = [
    { id: 1, name: 'Producto1', value: '1658.00', description: 'Descripción' },
    { id: 2, name: 'Producto2', value: '1658.00', description: 'Descripción' },
    { id: 3, name: 'Producto3', value: '1658.00', description: 'Descripción' },
    { id: 4, name: 'Producto4', value: '1658.00', description: 'Descripción' },
    { id: 5, name: 'Producto5', value: '1658.00', description: 'Descripción' }
  ];

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <div className="dashboard-content">
        <h1>Análisis de cliente</h1>
        
        <div className="dashboard-grid">
          <div className="card">
            <h2>Top clientes por ejecutivo comercial</h2>
            <div className="client-list">
              {clientData.map(client => (
                <div key={client.id} className="client-item">
                  <span className="client-name">{client.name}</span>
                  <span className="client-value">${client.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h2>Cantidad de clientes potenciales por tipo</h2>
            <div className="chart-placeholder">
              {/* Aquí irá el gráfico de barras */}
              <div className="placeholder-text">Gráfico de barras</div>
            </div>
          </div>

          <div className="card">
            <h2>Top productos por cada 3, 6, 12 meses</h2>
            <div className="product-list">
              {productData.map(product => (
                <div key={product.id} className="product-item">
                  <span className="product-name">{product.name}</span>
                  <span className="product-value">${product.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h2>También podría interesarte estos productos...</h2>
            <div className="suggested-products">
              {productData.map(product => (
                <div key={product.id} className="suggested-product">
                  <h3>{product.name}</h3>
                  <p>{product.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;