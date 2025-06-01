import React from 'react';
import './Sidebar.css';
import { FaHome, FaUser, FaBox, FaChartBar, FaCog } from 'react-icons/fa';
import { FaC } from 'react-icons/fa6';

const Sidebar = () => {
  return (
    <div className="sidebar">

      <div className="logo">
        <h2>ANDERS</h2>
      </div>

      {/* <div className="menu--list">
        <a href="#" className="nav-icon"> 
          <FaHome />
          Inicio
        </a>
        <a href="#" className="nav-icon"> 
          <FaUser />
          Clientes
        </a>
        <a href="#" className="nav-icon"> 
          <FaBox />
          Productos
        </a>
        <a href="#" className="nav-icon"> 
          <FaChartBar />
          Análisis
        </a>
        <a href="#" className="nav-icon">
          <FaCog />
          Configuración
        </a>
      </div> */}

      <nav className="nav-menu">
        <ul>
          <li className="nav-item active">
            <FaHome className="nav-icon" />
            <span>Inicio</span>
          </li>
          <li className="nav-item">
            <FaUser className="nav-icon" />
            <span>Clientes</span>
          </li>
          <li className="nav-item">
            <FaBox className="nav-icon" />
            <span>Productos</span>
          </li>
          <li className="nav-item">
            <FaChartBar className="nav-icon" />
            <span>Análisis</span>
          </li>
          <li className="nav-item">
            <FaCog className="nav-icon" />
            <span>Configuración</span>
          </li>
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;