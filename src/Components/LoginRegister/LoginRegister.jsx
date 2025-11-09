import React, { useState } from 'react';
import './LoginRegister.css';
import { FaUser, FaLock, FaEnvelope } from "react-icons/fa";

const LoginRegister = ({ onLoginSuccess }) => {
  const [action, setAction] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [registerName, setRegisterName] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

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

  const handleLogin = (e) => {
    e.preventDefault();
    setError('');

    // Usuarios administrativos predefinidos
    const adminUsers = {
      admin: {
        email: 'admin@anders.com',
        password: 'contra123',
        role: 'admin'
      }
    };

    // Verificar si es un usuario admin
    const foundAdmin = Object.values(adminUsers).find(
      user => user.email === email && user.password === password
    );

    if (foundAdmin) {
      onLoginSuccess(foundAdmin.role);
      return;
    }

    // Verificar si es un analista registrado
    const analysts = JSON.parse(localStorage.getItem('analysts') || '[]');
    const foundAnalyst = analysts.find(
      analyst => analyst.email === email && analyst.status === 'Activo' && analyst.registeredPassword
    );

    if (foundAnalyst) {
      // Verificar la contraseña guardada
      const registeredUsers = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
      const registeredUser = registeredUsers.find(user => user.email === email);
      
      if (registeredUser && registeredUser.password === password) {
        onLoginSuccess('user');
        return;
      }
    }

    setError('Credenciales incorrectas o usuario no registrado');
  };

  const handleRegister = (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    // Validaciones
    if (!registerName.trim()) {
      setError('Por favor, ingrese su nombre de usuario');
      return;
    }

    if (!registerEmail.trim()) {
      setError('Por favor, ingrese su correo electrónico');
      return;
    }

    if (!registerPassword.trim()) {
      setError('Por favor, ingrese una contraseña');
      return;
    }

    if (registerPassword.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    if (!acceptTerms) {
      setError('Debe aceptar los términos y condiciones');
      return;
    }

    // Verificar que el email termine con @anders.com
    if (!registerEmail.toLowerCase().endsWith('@anders.com')) {
      setError('Solo se permiten correos @anders.com');
      return;
    }

    // Verificar que el analista esté registrado en la configuración
    const analysts = JSON.parse(localStorage.getItem('analysts') || '[]');
    const analystIndex = analysts.findIndex(
      analyst => analyst.email.toLowerCase() === registerEmail.toLowerCase()
    );

    if (analystIndex === -1) {
      setError('Este correo no está autorizado. Contacte al administrador.');
      return;
    }

    // Verificar si ya está registrado
    const registeredUsers = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
    const existingUser = registeredUsers.find(
      user => user.email.toLowerCase() === registerEmail.toLowerCase()
    );

    if (existingUser) {
      setError('Este correo ya está registrado. Por favor, inicie sesión.');
      return;
    }

    // Registrar el nuevo usuario
    const newUser = {
      name: registerName.trim(),
      email: registerEmail.toLowerCase(),
      password: registerPassword,
      registeredAt: new Date().toISOString()
    };

    registeredUsers.push(newUser);
    localStorage.setItem('registeredUsers', JSON.stringify(registeredUsers));

    // Actualizar el estado del analista a "Activo"
    analysts[analystIndex].status = 'Activo';
    analysts[analystIndex].registeredPassword = true;
    localStorage.setItem('analysts', JSON.stringify(analysts));

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
  };

  return (
    <div className={`wrapper ${action}`}>
      {/* -- Login -- */}
      <div className="form-box login">
        <form onSubmit={handleLogin}>
          <h1>ANDERS</h1>
          {error && !action && <div className="error-message">{error}</div>}
          <div className="input-box">
            <input 
              type="text" 
              placeholder='Introduce tu e-mail' 
              required 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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
          <button type="submit">Iniciar Sesión</button>
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
          {error && action && <div className="error-message">{error}</div>}
          {successMessage && <div className="success-message">{successMessage}</div>}
          <div className="input-box">
            <input 
              type="text" 
              placeholder='Nombre de usuario' 
              required 
              value={registerName}
              onChange={(e) => setRegisterName(e.target.value)}
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
            />
            <FaLock className='icon' />
          </div>
          <div className="remember-forgot">
            <label>
              <input 
                type="checkbox" 
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
              />
              Acepto los términos y condiciones
            </label>
          </div>
          <button type="submit">Registrar</button>
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