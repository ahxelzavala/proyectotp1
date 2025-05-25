import React, { useState } from 'react';
import './LoginRegister.css';
import { FaUser, FaLock, FaEnvelope } from "react-icons/fa";

const LoginRegister = () => {
  const [action, setAction] = useState('');

  const registerLink = (e) => {
    e.preventDefault();
    setAction('active');
  };

  const loginLink = (e) => {
    e.preventDefault();
    setAction('');
  };

  return (
    <div className={`wrapper ${action}`}>
      {/* -- Login -- */}
      <div className="form-box login">
        <form action="">
          <h1>ANDERS</h1>
          <div className="input-box">
            <input type="text" placeholder='Introduce tu e-mail' required />
            <FaUser className='icon' />
          </div>
          <div className="input-box">
            <input type="password" placeholder='Contraseña' required />
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

