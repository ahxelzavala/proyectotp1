import React, { useState } from 'react';
import './LoginRegister.css';
import { FaUser, FaLock, FaEnvelope } from "react-icons/fa";

const LoginRegister = ({ onLoginSuccess }) => {
  const [action, setAction] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

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

  const handleLogin = (e) => {
    e.preventDefault();
    setError('');

    const users = {
      admin: {
        email: 'admin@anders.com',
        password: 'contra123',
        role: 'admin'
      },
      user: {
        email: 'user@anders.com',
        password: 'contra456',
        role: 'user'
      }
    };

    const foundUser = Object.values(users).find(
      user => user.email === email && user.password === password
    );

    if (foundUser) {
      onLoginSuccess(foundUser.role);
    } else {
      setError('Credenciales incorrectas');
    }
  };

  return (
    <div className={`wrapper ${action}`}>
      {/* -- Login -- */}
      <div className="form-box login">
        <form onSubmit={handleLogin}>
          <h1>ANDERS</h1>
          {error && <div className="error-message">{error}</div>}
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
        <form action="">
          <h1>Registro</h1>
          <div className="input-box">
            <input type="text" placeholder='Nombre de usuario' required />
            <FaUser className='icon' />
          </div>
          <div className="input-box">
            <input type="email" placeholder='E-mail' required />
            <FaEnvelope className='icon' />
          </div>
          <div className="input-box">
            <input type="password" placeholder='Contraseña' required />
            <FaLock className='icon' />
          </div>
          <div className="remember-forgot">
            <label>
              <input type="checkbox" />
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
