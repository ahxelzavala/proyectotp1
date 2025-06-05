import React, { useState, useEffect } from 'react';
import './Configuration.css';

const Configuration = () => {
  const [analysts, setAnalysts] = useState([]);
  const [newEmail, setNewEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchAnalysts();
  }, []);

  const fetchAnalysts = async () => {
    try {
      const response = await fetch('http://localhost:8000/analysts');
      const data = await response.json();
      setAnalysts(data);
    } catch (error) {
      setError('Error al cargar los analistas');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!newEmail.endsWith('@anders.com')) {
      setError('El correo debe ser del dominio @anders.com');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/analysts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: newEmail }),
      });

      if (response.ok) {
        setSuccess('Analista agregado correctamente');
        setNewEmail('');
        fetchAnalysts();
      } else {
        const data = await response.json();
        setError(data.detail || 'Error al agregar el analista');
      }
    } catch (error) {
      setError('Error al conectar con el servidor');
    }
  };

  return (
    <div className="configuration-container">
      <h2>Configuración de Analistas</h2>
      
      <form onSubmit={handleSubmit} className="analyst-form">
        <div className="input-group">
          <input
            type="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            placeholder="Correo del analista"
            required
          />
          <button type="submit">Agregar Analista</button>
        </div>
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
      </form>

      <div className="analysts-list">
        <h3>Analistas Registrados</h3>
        {analysts.length > 0 ? (
          <ul>
            {analysts.map((email, index) => (
              <li key={index}>{email}</li>
            ))}
          </ul>
        ) : (
          <p>No hay analistas registrados</p>
        )}
      </div>
    </div>
  );
};

export default Configuration;