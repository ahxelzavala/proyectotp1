import React, { useState } from 'react';
import './Dashboard.css';
import Sidebar from './Sidebar';
import Configuration from './Configuration';
import Clients from './Clients';
import Inicio from './Inicio';  // Importar Inicio.jsx

const Dashboard = ({ userRole, onLogout }) => {
  const [currentSection, setCurrentSection] = useState('inicio');  // Estado para la sección activa

  // Función para renderizar el contenido basado en la sección actual
  const renderMainContent = () => {
    switch (currentSection) {
      case 'configuracion':
        if (userRole === 'admin') {
          return <Configuration />;
        }
        break;
      case 'clientes':
        return <Clients />;
      case 'inicio':
      default:
        return <Inicio />;  // Mostrar el componente de Inicio
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar 
        userRole={userRole} 
        onLogout={onLogout} 
        onSectionChange={setCurrentSection}  // Cambiar la sección activa
        currentSection={currentSection}
      />
      <div className="dashboard-content">
        {renderMainContent()}  {/* Renderizar el contenido de la sección activa */}
      </div>
    </div>
  );
};

export default Dashboard;
