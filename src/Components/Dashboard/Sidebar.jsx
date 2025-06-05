import React from 'react';
import './Sidebar.css';
import { FaHome, FaUser, FaBox, FaChartBar, FaCog, FaSignOutAlt } from 'react-icons/fa';

const Sidebar = ({ userRole, onLogout, onSectionChange, currentSection }) => {
  const menuItems = [
    { icon: FaHome, text: 'Inicio', id: 'inicio', showFor: ['user', 'admin'] },
    { icon: FaUser, text: 'Clientes', id: 'clientes', showFor: ['user', 'admin'] },
    { icon: FaBox, text: 'Productos', id: 'productos', showFor: ['user', 'admin'] },
    { icon: FaChartBar, text: 'Análisis', id: 'analisis', showFor: ['user', 'admin'] },
    { icon: FaCog, text: 'Configuración', id: 'configuracion', showFor: ['admin'] },
    { icon: FaSignOutAlt, text: 'Salir', id: 'salir', showFor: ['user', 'admin'], onClick: onLogout }
  ];

  const handleItemClick = (item) => {
    if (item.onClick) {
      item.onClick();
    } else {
      onSectionChange(item.id);
    }
  };

  return (
    <div className="sidebar">
      <div className="logo">
        <h2>ANDERS</h2>
      </div>

      <nav className="nav-menu">
        <ul>
          {menuItems
            .filter(item => item.showFor.includes(userRole))
            .map((item) => (
              <li 
                key={item.id} 
                className={`nav-item ${currentSection === item.id ? 'active' : ''}`}
                onClick={() => handleItemClick(item)}
                style={{ cursor: 'pointer' }}
              >
                <item.icon className="nav-icon" />
                <span>{item.text}</span>
              </li>
            ))}
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;