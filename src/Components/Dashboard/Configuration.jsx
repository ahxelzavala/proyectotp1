import React, { useState, useEffect } from 'react';
import { FaUserPlus, FaUsers, FaTrash, FaEdit, FaTimes, FaCheckCircle, FaSave } from 'react-icons/fa';
import Sidebar from './Sidebar';
import './Configuration.css';

const Configuration = () => {
  const [newAnalystFirstName, setNewAnalystFirstName] = useState('');
  const [newAnalystLastName, setNewAnalystLastName] = useState('');
  const [newAnalystEmail, setNewAnalystEmail] = useState('');
  const [analysts, setAnalysts] = useState([]);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ firstName: '', lastName: '', email: '' });

  // Cargar analistas desde localStorage al iniciar
  useEffect(() => {
    const storedAnalysts = localStorage.getItem('analysts');
    if (storedAnalysts) {
      setAnalysts(JSON.parse(storedAnalysts));
    }
  }, []);

  // Guardar analistas en localStorage cuando cambian
  useEffect(() => {
    if (analysts.length > 0) {
      localStorage.setItem('analysts', JSON.stringify(analysts));
    }
  }, [analysts]);

  // Validar email que termine con @anders.com
  const validateEmail = (email) => {
    return email.toLowerCase().endsWith('@anders.com');
  };

  const handleAddAnalyst = () => {
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

    // Verificar si el email ya existe
    if (analysts.some(analyst => analyst.email.toLowerCase() === newAnalystEmail.toLowerCase())) {
      setErrorMessage('Este correo ya está registrado');
      return;
    }

    const newAnalyst = {
      id: Date.now(),
      firstName: newAnalystFirstName.trim(),
      lastName: newAnalystLastName.trim(),
      email: newAnalystEmail.trim().toLowerCase(),
      fullName: `${newAnalystFirstName.trim()} ${newAnalystLastName.trim()}`,
      status: 'Inactivo',
      registeredPassword: false
    };

    setAnalysts([...analysts, newAnalyst]);
    setNewAnalystFirstName('');
    setNewAnalystLastName('');
    setNewAnalystEmail('');
    setShowSuccessMessage(true);

    // Ocultar mensaje después de 3 segundos
    setTimeout(() => {
      setShowSuccessMessage(false);
    }, 3000);
  };

  const handleDeleteAnalyst = (id) => {
    const updatedAnalysts = analysts.filter(analyst => analyst.id !== id);
    setAnalysts(updatedAnalysts);
    
    // Si no quedan analistas, limpiar localStorage
    if (updatedAnalysts.length === 0) {
      localStorage.removeItem('analysts');
    }
  };

  const handleEditClick = (analyst) => {
    setEditingId(analyst.id);
    setEditForm({
      firstName: analyst.firstName,
      lastName: analyst.lastName,
      email: analyst.email
    });
  };

  const handleSaveEdit = (id) => {
    setErrorMessage('');

    // Validaciones
    if (!editForm.firstName.trim() || !editForm.lastName.trim()) {
      setErrorMessage('Por favor, ingrese nombre y apellido');
      return;
    }

    if (!validateEmail(editForm.email)) {
      setErrorMessage('El correo debe terminar con @anders.com');
      return;
    }

    // Verificar si el email ya existe (excepto el actual)
    if (analysts.some(analyst => analyst.id !== id && analyst.email.toLowerCase() === editForm.email.toLowerCase())) {
      setErrorMessage('Este correo ya está registrado');
      return;
    }

    const updatedAnalysts = analysts.map(analyst => {
      if (analyst.id === id) {
        return {
          ...analyst,
          firstName: editForm.firstName.trim(),
          lastName: editForm.lastName.trim(),
          email: editForm.email.trim().toLowerCase(),
          fullName: `${editForm.firstName.trim()} ${editForm.lastName.trim()}`
        };
      }
      return analyst;
    });

    setAnalysts(updatedAnalysts);
    setEditingId(null);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setErrorMessage('');
  };

  return (
    <div className="layout-container">
      <Sidebar userRole="admin" onLogout={() => {}} />
      <div className="configuration-container">
        <div className="configuration-content">
          <h1 className="page-title">Configuración de Analistas</h1>

          {/* Mensaje de éxito */}
          {showSuccessMessage && (
            <div className="success-message">
              <FaCheckCircle className="success-icon" />
              Analista Registrado Exitosamente
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
                />
                <input
                  type="text"
                  className="analyst-input"
                  placeholder="Apellido"
                  value={newAnalystLastName}
                  onChange={(e) => setNewAnalystLastName(e.target.value)}
                />
                <input
                  type="email"
                  className="analyst-input"
                  placeholder="Correo del analista (debe terminar con @anders.com)"
                  value={newAnalystEmail}
                  onChange={(e) => setNewAnalystEmail(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && newAnalystFirstName.trim() && newAnalystLastName.trim() && newAnalystEmail.trim()) {
                      handleAddAnalyst();
                    }
                  }}
                />
                <button
                  className="add-analyst-btn"
                  onClick={handleAddAnalyst}
                  disabled={!newAnalystFirstName.trim() || !newAnalystLastName.trim() || !newAnalystEmail.trim()}
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
                            />
                            <input
                              type="text"
                              className="edit-input"
                              value={editForm.lastName}
                              onChange={(e) => setEditForm({...editForm, lastName: e.target.value})}
                              placeholder="Apellido"
                            />
                          </div>
                          <input
                            type="email"
                            className="edit-input"
                            value={editForm.email}
                            onChange={(e) => setEditForm({...editForm, email: e.target.value})}
                            placeholder="Email"
                          />
                          <span className={`analyst-status ${analyst.status.toLowerCase()}`}>
                            {analyst.status}
                          </span>
                          <div className="analyst-actions">
                            <button 
                              className="action-btn save-btn" 
                              title="Guardar"
                              onClick={() => handleSaveEdit(analyst.id)}
                            >
                              <FaSave />
                            </button>
                            <button 
                              className="action-btn cancel-btn" 
                              title="Cancelar"
                              onClick={handleCancelEdit}
                            >
                              <FaTimes />
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <span className="analyst-name">{analyst.fullName}</span>
                          <span className="analyst-email">{analyst.email}</span>
                          <span className={`analyst-status ${analyst.status.toLowerCase()}`}>
                            {analyst.status}
                          </span>
                          <div className="analyst-actions">
                            <button 
                              className="action-btn edit-btn" 
                              title="Editar"
                              onClick={() => handleEditClick(analyst)}
                            >
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