import React, { useState } from 'react';
import './LoginRegister.css';
import { FaUser, FaLock, FaEnvelope } from "react-icons/fa";
import config from '../../config';

const LoginRegister = ({ onLoginSuccess }) => {
  const [action, setAction] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const registerLink = (e) => {
    e.preventDefault();
    setAction('active');
    setError('');
  };

  const loginLink = (e) => {
    e.preventDefault();
    setAction('');
    setError('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${config.API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Guardar token en localStorage
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('userRole', data.role);
        
        // Llamar a la función de éxito con el rol
        onLoginSuccess(data.role);
      } else {
        setError(data.detail || 'Credenciales incorrectas');
      }
    } catch (error) {
      console.error('Error en login:', error);
      setError('Error de conexión con el servidor');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${config.API_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          email: registerEmail,
          password: registerPassword
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Registro exitoso, cambiar a login
        setError('');
        alert('Registro exitoso. Por favor inicia sesión.');
        loginLink(e);
      } else {
        setError(data.detail || 'Error en el registro');
      }
    } catch (error) {
      console.error('Error en registro:', error);
      setError('Error de conexión con el servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`wrapper ${action}`}>
      {/* -- Login -- */}
      <div className="form-box login">
        <form onSubmit={handleLogin}>
          <h1>ANDERS</h1>
          {error && action === '' && <div className="error-message">{error}</div>}
          <div className="input-box">
            <input 
              type="email" 
              placeholder='Introduce tu e-mail' 
              required 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
            <FaUser className='icon' />
          </div>
          <div className="input-box">
            <input 
              type="password" 
              placeholder='Contraseña' 
              required 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            <FaLock className='icon' />
          </div>
          <div className="remember-forgot">
            <label>
              <input type="checkbox" />
              Recuerdame
            </label>
            <a href="#">¿Has olvidado tu contraseña?</a>
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Cargando...' : 'Iniciar Sesión'}
          </button>
          <div className="register-link">
            <p>
              ¿No tienes una cuenta?{' '}
              <a href="#" onClick={registerLink}>¡Regístrate!</a>
            </p>
          </div>
        </form>
      </div>

      {/* -- Register -- */}
      <div className="form-box register">
        <form onSubmit={handleRegister}>
          <h1>Registro</h1>
          {error && action === 'active' && <div className="error-message">{error}</div>}
          <div className="input-box">
            <input 
              type="text" 
              placeholder='Nombre de usuario' 
              required 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
            />
            <FaUser className='icon' />
          </div>
          <div className="input-box">
            <input 
              type="email" 
              placeholder='E-mail' 
              required 
              value={registerEmail}
              onChange={(e) => setRegisterEmail(e.target.value)}
              disabled={loading}
            />
            <FaEnvelope className='icon' />
          </div>
          <div className="input-box">
            <input 
              type="password" 
              placeholder='Contraseña' 
              required 
              value={registerPassword}
              onChange={(e) => setRegisterPassword(e.target.value)}
              disabled={loading}
            />
            <FaLock className='icon' />
          </div>
          <div className="remember-forgot">
            <label>
              <input type="checkbox" required />
              Acepto los términos y condiciones
            </label>
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Cargando...' : 'Registrar'}
          </button>
          <div className="register-link">
            <p>
              ¿Ya tienes una cuenta?{' '}
              <a href="#" onClick={loginLink}>Iniciar Sesión</a>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginRegister;