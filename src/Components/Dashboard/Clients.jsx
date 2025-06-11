import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const Clients = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [clientData, setClientData] = useState([]);
  const [productData, setProductData] = useState([]);
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
      } else {
        console.error('Error al obtener datos');
      }
    } catch (error) {
      console.error('Error de conexión:', error);
    } finally {
      setDataLoading(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'text/csv') {
      setFile(file);
      setMessage('');
    } else {
      setFile(null);
      setMessage('Por favor, selecciona un archivo CSV válido');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Por favor, selecciona un archivo primero');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload-csv', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('Archivo cargado exitosamente');
        setFile(null);
        // Actualizar los datos del dashboard
        fetchClientData();
      } else {
        setMessage(data.detail || 'Error al cargar el archivo');
      }
    } catch (error) {
      setMessage('Error al conectar con el servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="titulo">Análisis de cliente</h1>

      <div className="upload-section">
        <h3>Cargar datos de clientes y productos</h3>
        <p>Selecciona un archivo CSV con las columnas: client_name, product, value (obligatorias), client_type, executive, date, description (opcionales)</p>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          disabled={loading}
        />
        <button 
          onClick={handleUpload} 
          disabled={!file || loading}
          className="upload-button"
        >
          {loading ? 'Cargando...' : 'Cargar CSV'}
        </button>
        {message && <p className={`message ${message.includes('exitosamente') ? 'success' : 'error'}`}>{message}</p>}
      </div>
      
      <div className="dashboard-grid">
        <div className="card">
          <h2>Top clientes por ejecutivo comercial</h2>
          <div className="client-list">
            {dataLoading ? (
              <p>Cargando datos...</p>
            ) : clientData.length > 0 ? (
              clientData.map(client => (
                <div key={client.id} className="client-item">
                  <span className="client-name">{client.name}</span>
                  <span className="client-executive">({client.executive})</span>
                  <span className="client-value">${client.value.toFixed(2)}</span>
                </div>
              ))
            ) : (
              <p>No hay datos disponibles. Carga un archivo CSV.</p>
            )}
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
            {dataLoading ? (
              <p>Cargando datos...</p>
            ) : productData.length > 0 ? (
              productData.map(product => (
                <div key={product.id} className="product-item">
                  <span className="product-name">{product.name}</span>
                  <span className="product-value">${product.value.toFixed(2)}</span>
                </div>
              ))
            ) : (
              <p>No hay datos disponibles. Carga un archivo CSV.</p>
            )}
          </div>
        </div>

        <div className="card">
          <h2>También podría interesarte estos productos...</h2>
          <div className="suggested-products">
            {dataLoading ? (
              <p>Cargando datos...</p>
            ) : productData.length > 0 ? (
              productData.map(product => (
                <div key={product.id} className="suggested-product">
                  <h3>{product.name}</h3>
                  <p>{product.description}</p>
                </div>
              ))
            ) : (
              <p>No hay datos disponibles. Carga un archivo CSV.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Clients;