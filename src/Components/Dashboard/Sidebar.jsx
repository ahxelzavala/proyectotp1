import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FaHome, FaUsers, FaBox, FaChartLine, FaCog, FaSignOutAlt } from 'react-icons/fa';
import './Sidebar.css';

const Sidebar = ({ userRole, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { 
      id: 'inicio', 
      label: 'Inicio', 
      path: '/dashboard', 
      icon: FaHome,
      showFor: ['user', 'admin'] 
    },
    { 
      id: 'clientes', 
      label: 'Clientes', 
      path: '/dashboard/clients', 
      icon: FaUsers,
      showFor: ['user', 'admin'] 
    },
    { 
      id: 'productos', 
      label: 'Productos', 
      path: '/dashboard/products', 
      icon: FaBox,
      showFor: ['user', 'admin'] 
    },
    { 
      id: 'analisis', 
      label: 'Análisis', 
      path: '/dashboard/analysis', 
      icon: FaChartLine,
      showFor: ['user', 'admin'] 
    },
  ];

  // Agregar configuración solo para admin
  if (userRole === 'admin') {
    menuItems.push({ 
      id: 'configuracion', 
      label: 'Configuración', 
      path: '/dashboard/configuration', 
      icon: FaCog,
      showFor: ['admin'] 
    });
  }

  const handleNavigation = (path) => {
    navigate(path);
  };

  // Función de logout
  const handleLogout = () => {
    onLogout();  // Llama a la función de logout
    navigate('/');  // Redirige a la página de login/register
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>ANDERS</h2>
      </div>
      
      <nav className="sidebar-nav">
        {menuItems
          .filter(item => item.showFor.includes(userRole))
          .map(item => (
            <button
              key={item.id}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => handleNavigation(item.path)}
            >
              <item.icon className="nav-icon" />
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
      </nav>
      
      <div className="sidebar-footer">
        <button className="nav-item logout-button" onClick={handleLogout}>
          <FaSignOutAlt className="nav-icon" />
          <span className="nav-label">Salir</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
