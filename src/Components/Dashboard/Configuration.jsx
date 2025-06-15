import React, { useState } from 'react';
import { FaUserPlus, FaUsers, FaTrash, FaEdit } from 'react-icons/fa';
import Sidebar from './Sidebar'; // Importa el Sidebar si no lo has hecho ya
import './Configuration.css';

const Configuration = () => {
  const [newAnalystEmail, setNewAnalystEmail] = useState('');
  const [analysts, setAnalysts] = useState([
    { id: 1, email: 'analyst1@company.com', name: 'Ana García', status: 'Activo' },
    { id: 2, email: 'analyst2@company.com', name: 'Carlos López', status: 'Activo' },
    { id: 3, email: 'analyst3@company.com', name: 'María Rodríguez', status: 'Inactivo' }
  ]);

  const handleAddAnalyst = () => {
    if (newAnalystEmail.trim()) {
      const newAnalyst = {
        id: analysts.length + 1,
        email: newAnalystEmail,
        name: 'Nuevo Analista',
        status: 'Pendiente'
      };
      setAnalysts([...analysts, newAnalyst]);
      setNewAnalystEmail('');
    }
  };

  const handleDeleteAnalyst = (id) => {
    setAnalysts(analysts.filter(analyst => analyst.id !== id));
  };

  return (
    <div className="layout-container">
      <Sidebar userRole="admin" onLogout={() => {}} /> {/* Sidebar importado */}
      <div className="configuration-container">
        <div className="configuration-content">
          <h1 className="page-title">Configuración de Analistas</h1>

          {/* Sección para agregar analista */}
          <div className="section-card">
            <div className="section-header">
              <FaUserPlus className="section-icon" />
              <h2>Agregar Nuevo Analista</h2>
            </div>
            <div className="section-body">
              <div className="input-group">
                <input
                  type="email"
                  className="analyst-input"
                  placeholder="Correo del analista"
                  value={newAnalystEmail}
                  onChange={(e) => setNewAnalystEmail(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddAnalyst()}
                />
                <button
                  className="add-analyst-btn"
                  onClick={handleAddAnalyst}
                  disabled={!newAnalystEmail.trim()}
                >
                  Agregar Analista
                </button>
              </div>
            </div>
          </div>

          {/* Sección de analistas registrados */}
          <div className="section-card">
            <div className="section-header">
              <FaUsers className="section-icon" />
              <h2>Analistas Registrados</h2>
              <span className="analysts-count">{analysts.length} analistas</span>
            </div>
            <div className="section-body">
              {analysts.length === 0 ? (
                <div className="empty-state">
                  <p>No hay analistas registrados</p>
                </div>
              ) : (
                <div className="analysts-table">
                  <div className="table-header">
                    <span>Nombre</span>
                    <span>Email</span>
                    <span>Estado</span>
                    <span>Acciones</span>
                  </div>
                  {analysts.map(analyst => (
                    <div key={analyst.id} className="analyst-row">
                      <span className="analyst-name">{analyst.name}</span>
                      <span className="analyst-email">{analyst.email}</span>
                      <span className={`analyst-status ${analyst.status.toLowerCase()}`}>
                        {analyst.status}
                      </span>
                      <div className="analyst-actions">
                        <button className="action-btn edit-btn" title="Editar">
                          <FaEdit />
                        </button>
                        <button
                          className="action-btn delete-btn"
                          title="Eliminar"
                          onClick={() => handleDeleteAnalyst(analyst.id)}
                        >
                          <FaTrash />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Configuration;
