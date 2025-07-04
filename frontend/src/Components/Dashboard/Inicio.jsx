import React, { useState, useEffect } from 'react';
import './Inicio.css';

const Inicio = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [recentUploads, setRecentUploads] = useState([]);
  const [dataStats, setDataStats] = useState(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://proyectoreact-backend-741997725999.us-central1.run.app';

  // Cargar estadísticas al montar el componente
  useEffect(() => {
    loadDataStats();
  }, []);

  const loadDataStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/client-data`);
      if (response.ok) {
        const data = await response.json();
        setDataStats({
          totalRecords: data.length,
          totalClients: new Set(data.map(item => item.client_name)).size,
          totalProducts: new Set(data.map(item => item.product)).size,
          totalValue: data.reduce((sum, item) => sum + (item.value || 0), 0)
        });
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  // Función para validar archivo CSV
  const validateCSVFile = (file) => {
    const allowedTypes = ['text/csv', 'application/vnd.ms-excel'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.csv')) {
      return 'Por favor, selecciona un archivo CSV válido.';
    }

    if (file.size > maxSize) {
      return 'El archivo es demasiado grande. Máximo 10MB permitido.';
    }

    return null;
  };

  // Función para manejar el cambio de archivo
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setMessage('');
    setUploadProgress(0);

    if (selectedFile) {
      const validationError = validateCSVFile(selectedFile);
      if (validationError) {
        setMessage(validationError);
        setFile(null);
        return;
      }

      setFile(selectedFile);
      setMessage(`Archivo seleccionado: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(2)} KB)`);
    } else {
      setFile(null);
    }
  };

  // Función para cargar el archivo CSV
  const handleUpload = async () => {
    if (!file) {
      setMessage('Por favor, selecciona un archivo primero.');
      return;
    }

    setLoading(true);
    setUploadProgress(0);
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Simular progreso de carga
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const response = await fetch(`${API_BASE_URL}/upload-csv`,  {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      const data = await response.json();

      if (response.ok) {
        setMessage(`✅ ${data.message}`);
        setFile(null);
        
        // Agregar a uploads recientes
        const newUpload = {
          id: Date.now(),
          filename: file.name,
          timestamp: new Date().toLocaleString(),
          status: 'success',
          message: data.message
        };
        setRecentUploads(prev => [newUpload, ...prev.slice(0, 4)]);
        
        // Recargar estadísticas
        setTimeout(() => {
          loadDataStats();
        }, 1000);

        // Limpiar el input file
        const fileInput = document.getElementById('csv-file-input');
        if (fileInput) fileInput.value = '';
      } else {
        setMessage(`❌ ${data.detail || 'Error al cargar el archivo.'}`);
        
        // Agregar a uploads recientes con error
        const newUpload = {
          id: Date.now(),
          filename: file.name,
          timestamp: new Date().toLocaleString(),
          status: 'error',
          message: data.detail || 'Error al cargar el archivo'
        };
        setRecentUploads(prev => [newUpload, ...prev.slice(0, 4)]);
      }
    } catch (error) {
      setMessage('❌ Error al conectar con el servidor. Verifica que el backend esté corriendo.');
      console.error('Upload error:', error);
    } finally {
      setLoading(false);
      setTimeout(() => setUploadProgress(0), 2000);
    }
  };

  // Función para limpiar mensajes
  const clearMessage = () => {
    setMessage('');
    setFile(null);
    const fileInput = document.getElementById('csv-file-input');
    if (fileInput) fileInput.value = '';
  };

  return (
    <div className="inicio-container">
      <div className="inicio-header">
        <h1>🚀 Bienvenido al Sistema de Análisis Anders</h1>
        <p className="subtitle">Importa tus datos CSV y obtén insights valiosos de tu información comercial</p>
      </div>

      {/* Estadísticas actuales */}
      {dataStats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">{dataStats.totalRecords}</div>
            <div className="stat-label">Registros Totales</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{dataStats.totalClients}</div>
            <div className="stat-label">Clientes Únicos</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{dataStats.totalProducts}</div>
            <div className="stat-label">Productos Únicos</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">${dataStats.totalValue.toLocaleString()}</div>
            <div className="stat-label">Valor Total</div>
          </div>
        </div>
      )}

      {/* Sección de carga */}
      <div className="upload-section">
        <h3>📂 Importar Datos CSV</h3>
        
        
        <div className="file-input-container">
          <input 
            id="csv-file-input"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            disabled={loading}
            className="file-input"
          />
          <div className="file-input-buttons">
            <button 
              onClick={handleUpload}
              disabled={!file || loading}
              className={`upload-button ${loading ? 'loading' : ''}`}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Procesando... {uploadProgress}%
                </>
              ) : (
                '⬆️ Importar Archivo'
              )}
            </button>
            
            {(file || message) && (
              <button 
                onClick={clearMessage}
                className="clear-button"
                disabled={loading}
              >
                🗑️ Limpiar
              </button>
            )}
          </div>
        </div>

        {/* Barra de progreso */}
        {loading && (
          <div className="progress-container">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <span className="progress-text">{uploadProgress}%</span>
          </div>
        )}

        {/* Mensaje de estado */}
        {message && (
          <div className={`message ${
            message.includes('✅') ? 'success' : 
            message.includes('❌') ? 'error' : 
            'info'
          }`}>
            {message}
          </div>
        )}
      </div>

      {/* Uploads recientes */}
      {recentUploads.length > 0 && (
        <div className="recent-uploads">
          <h3>📋 Uploads Recientes</h3>
          <div className="uploads-list">
            {recentUploads.map(upload => (
              <div key={upload.id} className={`upload-item ${upload.status}`}>
                <div className="upload-info">
                  <span className="upload-filename">{upload.filename}</span>
                  <span className="upload-timestamp">{upload.timestamp}</span>
                </div>
                <div className="upload-message">{upload.message}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ayuda */}
      <div className="help-section">
        <h3>❓ ¿Necesitas ayuda?</h3>
        <div className="help-content">
          <div className="help-item">
            <strong>Formato CSV:</strong> Asegúrate de que tu archivo tenga las columnas correctas separadas por comas.
          </div>
          <div className="help-item">
            <strong>Codificación:</strong> Guarda tu archivo en UTF-8 para evitar problemas con caracteres especiales.
          </div>
          <div className="help-item">
            <strong>Tamaño:</strong> El archivo no debe exceder los 10MB.
          </div>
        </div>
      </div>
    </div>
  );
};

export default Inicio;