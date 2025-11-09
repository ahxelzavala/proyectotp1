import React, { useState, useEffect } from 'react';
import { FaUserPlus, FaUsers, FaTrash, FaEdit, FaTimes, FaCheckCircle, FaSave } from 'react-icons/fa';
import Sidebar from './Sidebar';
import { analystService } from '../../services/api';  // ✅ CORREGIDO: DOS niveles arriba
import './Configuration.css';

const Configuration = ({ onLogout }) => {
  const [newAnalystFirstName, setNewAnalystFirstName] = useState('');
  const [newAnalystLastName, setNewAnalystLastName] = useState('');
  const [newAnalystEmail, setNewAnalystEmail] = useState('');
  const [analysts, setAnalysts] = useState([]);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ firstName: '', lastName: '', email: '' });
  const [loading, setLoading] = useState(false);

  // Cargar analistas al iniciar
  useEffect(() => {
    loadAnalysts();
  }, []);

  const loadAnalysts = async () => {
    console.log('🔍 Cargando analistas...');
    setLoading(true);
    
    try {
      const data = await analystService.getAll();
      console.log('📊 Resultado:', data);
      
      // El backend puede devolver array directo o { success, analysts }
      const analystsList = Array.isArray(data) ? data : (data.analysts || []);
      
      console.log('✅ Analistas cargados:', analystsList);
      setAnalysts(analystsList);
    } catch (error) {
      console.error('❌ Error de red:', error);
      setErrorMessage('Error de conexión con el servidor');
    }
    
    setLoading(false);
  };

  const validateEmail = (email) => {
    return email.toLowerCase().endsWith('@anders.com');
  };

  const handleAddAnalyst = async () => {
    setErrorMessage('');
    setShowSuccessMessage(false);

    // Validaciones
    if (!newAnalystFirstName.trim() || !newAnalystLastName.trim()) {
      setErrorMessage('Por favor, ingrese nombre y apellido');
      return;
    }

    if (!newAnalystEmail.trim()) {
      setErrorMessage('Por favor, ingrese el correo electrónico');
      return;
    }

    if (!validateEmail(newAnalystEmail)) {
      setErrorMessage('El correo debe terminar con @anders.com');
      return;
    }

    console.log('📝 Creando analista:', {
      firstName: newAnalystFirstName,
      lastName: newAnalystLastName,
      email: newAnalystEmail
    });

    setLoading(true);

    try {
      const result = await analystService.create(
        newAnalystFirstName.trim(),
        newAnalystLastName.trim(),
        newAnalystEmail.trim().toLowerCase()
      );

      console.log('📊 Resultado creación:', result);

      // Recargar lista
      await loadAnalysts();
      
      // Limpiar formulario
      setNewAnalystFirstName('');
      setNewAnalystLastName('');
      setNewAnalystEmail('');
      
      // Mostrar mensaje de éxito
      setSuccessMessage('Analista Registrado Exitosamente');
      setShowSuccessMessage(true);

      // Ocultar mensaje después de 3 segundos
      setTimeout(() => {
        setShowSuccessMessage(false);
      }, 3000);

    } catch (error) {
      console.error('❌ Error:', error);
      setErrorMessage(error.message || 'Error al crear analista');
    }

    setLoading(false);
  };

  const handleDeleteAnalyst = async (id) => {
    if (!window.confirm('¿Estás seguro de eliminar este analista?')) {
      return;
    }

    setLoading(true);
    
    try {
      await analystService.delete(id);
      
      await loadAnalysts();
      setSuccessMessage('Analista eliminado exitosamente');
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
      
    } catch (error) {
      console.error('❌ Error:', error);
      setErrorMessage(error.message || 'Error al eliminar analista');
    }
    
    setLoading(false);
  };

  const handleEditClick = (analyst) => {
    setEditingId(analyst.id);
    setEditForm({
      firstName: analyst.first_name,
      lastName: analyst.last_name,
      email: analyst.email
    });
  };

  const handleSaveEdit = async (id) => {
    setErrorMessage('');

    if (!editForm.firstName.trim() || !editForm.lastName.trim()) {
      setErrorMessage('Por favor, ingrese nombre y apellido');
      return;
    }

    if (!validateEmail(editForm.email)) {
      setErrorMessage('El correo debe terminar con @anders.com');
      return;
    }

    setLoading(true);

    try {
      await analystService.update(
        id,
        editForm.firstName.trim(),
        editForm.lastName.trim(),
        editForm.email.trim().toLowerCase()
      );

      await loadAnalysts();
      setEditingId(null);
      setSuccessMessage('Analista actualizado exitosamente');
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
      
    } catch (error) {
      console.error('❌ Error:', error);
      setErrorMessage(error.message || 'Error al actualizar analista');
    }

    setLoading(false);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setErrorMessage('');
  };

  return (
    <div className="layout-container">
      <Sidebar userRole="admin" onLogout={onLogout} />
      <div className="configuration-container">
        <div className="configuration-content">
          <h1 className="page-title">Configuración de Analistas</h1>

          {/* Mensaje de éxito */}
          {showSuccessMessage && (
            <div className="success-message">
              <FaCheckCircle className="success-icon" />
              {successMessage}
            </div>
          )}

          {/* Mensaje de error */}
          {errorMessage && (
            <div className="error-message-box">
              <FaTimes className="error-icon" />
              {errorMessage}
            </div>
          )}

          {/* Sección para agregar analista */}
          <div className="section-card">
            <div className="section-header">
              <FaUserPlus className="section-icon" />
              <h2>Agregar Nuevo Analista</h2>
            </div>
            <div className="section-body">
              <div className="input-grid">
                <input
                  type="text"
                  className="analyst-input"
                  placeholder="Nombre"
                  value={newAnalystFirstName}
                  onChange={(e) => setNewAnalystFirstName(e.target.value)}
                  disabled={loading}
                />
                <input
                  type="text"
                  className="analyst-input"
                  placeholder="Apellido"
                  value={newAnalystLastName}
                  onChange={(e) => setNewAnalystLastName(e.target.value)}
                  disabled={loading}
                />
                <input
                  type="email"
                  className="analyst-input"
                  placeholder="Correo del analista (debe terminar con @anders.com)"
                  value={newAnalystEmail}
                  onChange={(e) => setNewAnalystEmail(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !loading) {
                      handleAddAnalyst();
                    }
                  }}
                  disabled={loading}
                />
                <button
                  className="add-analyst-btn"
                  onClick={handleAddAnalyst}
                  disabled={loading || !newAnalystFirstName.trim() || !newAnalystLastName.trim() || !newAnalystEmail.trim()}
                >
                  {loading ? 'Agregando...' : 'Agregar Analista'}
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
              {loading && analysts.length === 0 ? (
                <div className="empty-state">
                  <p>Cargando analistas...</p>
                </div>
              ) : analysts.length === 0 ? (
                <div className="empty-state">
                  <p>No hay analistas registrados</p>
                </div>
              ) : (
                <div className="analysts-table">
                  <div className="table-header">
                    <span>Nombre y Apellido</span>
                    <span>Email</span>
                    <span>Estado</span>
                    <span>Acciones</span>
                  </div>
                  {analysts.map(analyst => (
                    <div key={analyst.id} className="analyst-row">
                      {editingId === analyst.id ? (
                        <>
                          <div className="edit-name-container">
                            <input
                              type="text"
                              className="edit-input"
                              value={editForm.firstName}
                              onChange={(e) => setEditForm({...editForm, firstName: e.target.value})}
                              placeholder="Nombre"
                              disabled={loading}
                            />
                            <input
                              type="text"
                              className="edit-input"
                              value={editForm.lastName}
                              onChange={(e) => setEditForm({...editForm, lastName: e.target.value})}
                              placeholder="Apellido"
                              disabled={loading}
                            />
                          </div>
                          <input
                            type="email"
                            className="edit-input"
                            value={editForm.email}
                            onChange={(e) => setEditForm({...editForm, email: e.target.value})}
                            placeholder="Email"
                            disabled={loading}
                          />
                          <span className={`analyst-status ${analyst.status.toLowerCase()}`}>
                            {analyst.status}
                          </span>
                          <div className="analyst-actions">
                            <button 
                              className="action-btn save-btn" 
                              title="Guardar"
                              onClick={() => handleSaveEdit(analyst.id)}
                              disabled={loading}
                            >
                              <FaSave />
                            </button>
                            <button 
                              className="action-btn cancel-btn" 
                              title="Cancelar"
                              onClick={handleCancelEdit}
                              disabled={loading}
                            >
                              <FaTimes />
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <span className="analyst-name">{analyst.full_name}</span>
                          <span className="analyst-email">{analyst.email}</span>
                          <span className={`analyst-status ${analyst.status.toLowerCase()}`}>
                            {analyst.status}
                          </span>
                          <div className="analyst-actions">
                            <button 
                              className="action-btn edit-btn" 
                              title="Editar"
                              onClick={() => handleEditClick(analyst)}
                              disabled={loading}
                            >
                              <FaEdit />
                            </button>
                            <button
                              className="action-btn delete-btn"
                              title="Eliminar"
                              onClick={() => handleDeleteAnalyst(analyst.id)}
                              disabled={loading}
                            >
                              <FaTrash />
                            </button>
                          </div>
                        </>
                      )}
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