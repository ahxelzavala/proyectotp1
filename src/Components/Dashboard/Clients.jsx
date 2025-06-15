import React, { useState, useEffect } from 'react';
import './Clients.css';
import Sidebar from './Sidebar';

const Clients = ({ userRole, onLogout }) => {
  const [clientData, setClientData] = useState([]);
  const [productData, setProductData] = useState([]);
  const [clientTypeData, setClientTypeData] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);

  // Cargar datos al montar el componente
  useEffect(() => {
    fetchClientData();
  }, []);

  // Función para obtener datos de clientes y productos
  const fetchClientData = async () => {
    setDataLoading(true);
    try {
      const response = await fetch('http://localhost:8000/client-data');
      if (response.ok) {
        const data = await response.json();
        
        // Procesar datos para clientes (agrupar por ejecutivo)
        const clientsByExecutive = data
          .filter(item => item.executive) // Filtrar elementos con ejecutivo
          .reduce((acc, item) => {
            // Agrupar por ejecutivo y cliente
            const key = `${item.executive}-${item.client_name}`;
            if (!acc[key]) {
              acc[key] = {
                id: item.id,
                name: item.client_name,
                executive: item.executive,
                value: 0
              };
            }
            // Sumar valores
            acc[key].value += item.value || 0;
            return acc;
          }, {});
        
        // Convertir a array y ordenar por valor
        const topClients = Object.values(clientsByExecutive)
          .sort((a, b) => b.value - a.value)
          .slice(0, 5); // Tomar los 5 principales
        
        setClientData(topClients);
        
        // Procesar datos para productos
        const productsByValue = data
          .filter(item => item.product) // Filtrar elementos con producto
          .reduce((acc, item) => {
            // Agrupar por producto
            if (!acc[item.product]) {
              acc[item.product] = {
                id: item.id,
                name: item.product,
                value: 0,
                description: item.description || 'Sin descripción'
              };
            }
            // Sumar valores
            acc[item.product].value += item.value || 0;
            return acc;
          }, {});
        
        // Convertir a array y ordenar por valor
        const topProducts = Object.values(productsByValue)
          .sort((a, b) => b.value - a.value)
          .slice(0, 5); // Tomar los 5 principales
        
        setProductData(topProducts);

        // Procesar datos para tipos de cliente
        const clientsByType = data
          .filter(item => item.client_type) // Filtrar elementos con tipo de cliente
          .reduce((acc, item) => {
            if (!acc[item.client_type]) {
              acc[item.client_type] = 0;
            }
            acc[item.client_type] += 1;
            return acc;
          }, {});
        
        // Convertir a array para el gráfico
        const clientTypes = Object.entries(clientsByType).map(([type, count]) => ({
          type,
          count
        }));
        
        setClientTypeData(clientTypes);
      } else {
        console.error('Error al obtener datos');
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
        <div className="clients-container">
          <h1 className="titulo">Análisis de cliente</h1>
          
          <div className="dashboard-grid">
            <div className="card">
              <h2>Top clientes por ejecutivo comercial</h2>
              <div className="chart-placeholder">
                {dataLoading ? (
                  <div className="placeholder-text">Cargando datos...</div>
                ) : clientData.length > 0 ? (
                  <div className="client-list">
                    {clientData.map(client => (
                      <div key={client.id} className="client-item">
                        <span className="client-name">{client.name}</span>
                        <span className="client-executive">({client.executive})</span>
                        <span className="client-value">${client.value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="placeholder-text">No hay datos disponibles</div>
                )}
              </div>
            </div>

            <div className="card">
              <h2>Cantidad de clientes potenciales por tipo</h2>
              <div className="chart-placeholder">
                {dataLoading ? (
                  <div className="placeholder-text">Cargando datos...</div>
                ) : clientTypeData.length > 0 ? (
                  <div className="client-type-list">
                    {clientTypeData.map((item, index) => (
                      <div key={index} className="client-type-item">
                        <span className="type-name">{item.type}</span>
                        <span className="type-count">{item.count} clientes</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="placeholder-text">Gráfico de barras</div>
                )}
              </div>
            </div>

            <div className="card">
              <h2>Top productos por cada 3, 6, 12 meses</h2>
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
              <h2>También podría interesarte estos productos...</h2>
              <div className="chart-placeholder">
                {dataLoading ? (
                  <div className="placeholder-text">Cargando datos...</div>
                ) : productData.length > 0 ? (
                  <div className="suggested-products">
                    {productData.map(product => (
                      <div key={product.id} className="suggested-product">
                        <h3>{product.name}</h3>
                        <p>{product.description}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="placeholder-text">No hay datos disponibles</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Clients;