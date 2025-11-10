import React, { useState } from 'react';
import './LoginRegister.css';
import { FaUser, FaLock, FaEnvelope } from "react-icons/fa";
import { authService } from '../../services/api';

const LoginRegister = ({ onLoginSuccess }) => {
  const [action, setAction] = useState('');
  
  // Estados para Login
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  // Estados para Registro
  const [registerName, setRegisterName] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  
  // Estados para mensajes y loading
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const registerLink = (e) => {
    e.preventDefault();
    setAction('active');
    setError('');
    setSuccessMessage('');
  };

  const loginLink = (e) => {
    e.preventDefault();
    setAction('');
    setError('');
    setSuccessMessage('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Validaciones básicas
      if (!email.trim()) {
        setError('Por favor, ingrese su correo electrónico');
        setLoading(false);
        return;
      }

      if (!password.trim()) {
        setError('Por favor, ingrese su contraseña');
        setLoading(false);
        return;
      }

      console.log('🔐 Intentando login con:', email);

      // Llamar al servicio de autenticación del backend
      const result = await authService.login(email, password);

      if (result.success) {
        console.log('✅ Login exitoso:', result.data.user);
        
        // Limpiar formulario
        setEmail('');
        setPassword('');
        
        // Notificar al App.js del login exitoso
        onLoginSuccess(result.data.user.role);
      } else {
        console.error('❌ Login fallido:', result.error);
        setError(result.error);
      }
    } catch (error) {
      console.error('❌ Error inesperado en login:', error);
      setError('Error de conexión con el servidor');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setLoading(true);

    try {
      // Validaciones
      if (!registerName.trim()) {
        setError('Por favor, ingrese su nombre completo');
        setLoading(false);
        return;
      }

      if (!registerEmail.trim()) {
        setError('Por favor, ingrese su correo electrónico');
        setLoading(false);
        return;
      }

      // Validar formato de email
      if (!registerEmail.includes('@')) {
        setError('El correo debe ser un email válido (ejemplo: juan@anders.com)');
        setLoading(false);
        return;
      }

      if (!registerEmail.toLowerCase().endsWith('@anders.com')) {
        setError('Solo se permiten correos @anders.com');
        setLoading(false);
        return;
      }

      if (!registerPassword.trim()) {
        setError('Por favor, ingrese una contraseña');
        setLoading(false);
        return;
      }

      if (registerPassword.length < 6) {
        setError('La contraseña debe tener al menos 6 caracteres');
        setLoading(false);
        return;
      }

      if (!acceptTerms) {
        setError('Debe aceptar los términos y condiciones');
        setLoading(false);
        return;
      }

      console.log('📝 Intentando registro con:', { name: registerName, email: registerEmail });

      // Llamar al servicio de registro del backend
      const result = await authService.register(
        registerName,
        registerEmail,
        registerPassword
      );

      if (result.success) {
        console.log('✅ Registro exitoso');
        
        // Mostrar mensaje de éxito
        setSuccessMessage('¡Registro exitoso! Ahora puede iniciar sesión.');
        
        // Limpiar formulario
        setRegisterName('');
        setRegisterEmail('');
        setRegisterPassword('');
        setAcceptTerms(false);

        // Cambiar a login después de 2 segundos
        setTimeout(() => {
          setAction('');
          setSuccessMessage('');
        }, 2000);
      } else {
        console.error('❌ Registro fallido:', result.error);
        setError(result.error);
      }
    } catch (error) {
      console.error('❌ Error inesperado en registro:', error);
      setError('Error de conexión con el servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`wrapper ${action}`}>
      {/* Login Form */}
      <div className="form-box login">
        <form onSubmit={handleLogin}>
          <h1>ANDERS</h1>
          
          {error && !action && (
            <div className="error-message">{error}</div>
          )}
          
          <div className="input-box">
            <input 
              type="email" 
              placeholder='Email' 
              required 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              autoComplete="email"
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
              autoComplete="current-password"
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
            {loading ? 'Iniciando...' : 'Iniciar Sesión'}
          </button>
          
          <div className="register-link">
            <p>
              ¿No tienes una cuenta?{' '}
              <a href="#" onClick={registerLink}>¡Regístrate!</a>
            </p>
          </div>
        </form>
      </div>

      {/* Register Form */}
      <div className="form-box register">
        <form onSubmit={handleRegister}>
          <h1>Registro</h1>
          
          {error && action && (
            <div className="error-message">{error}</div>
          )}
          
          {successMessage && (
            <div className="success-message">{successMessage}</div>
          )}
          
          {/* CAMPO 1: NOMBRE COMPLETO */}
          <div className="input-box">
            <input 
              type="text" 
              placeholder='Nombre completo'
              required 
              value={registerName}
              onChange={(e) => setRegisterName(e.target.value)}
              disabled={loading}
              autoComplete="name"
            />
            <FaUser className='icon' />
            <div className="input-hint">Ejemplo: Juan Pérez</div>
          </div>
          
          {/* CAMPO 2: EMAIL (CON AYUDA VISUAL) */}
          <div className="input-box">
            <input 
              type="email" 
              placeholder='Email (ej: juan@anders.com)'
              required 
              value={registerEmail}
              onChange={(e) => setRegisterEmail(e.target.value)}
              disabled={loading}
              autoComplete="email"
            />
            <FaEnvelope className='icon' />
            <div className="input-hint">⚠️ Debe ser un email válido @anders.com</div>
          </div>
          
          {/* CAMPO 3: CONTRASEÑA */}
          <div className="input-box">
            <input 
              type="password" 
              placeholder='Contraseña (mín. 6 caracteres)' 
              required 
              value={registerPassword}
              onChange={(e) => setRegisterPassword(e.target.value)}
              disabled={loading}
              autoComplete="new-password"
            />
            <FaLock className='icon' />
          </div>
          
          <div className="remember-forgot">
            <label>
              <input 
                type="checkbox" 
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
                disabled={loading}
              />
              Acepto los términos y condiciones
            </label>
          </div>
          
          <button type="submit" disabled={loading}>
            {loading ? 'Registrando...' : 'Registrar'}
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