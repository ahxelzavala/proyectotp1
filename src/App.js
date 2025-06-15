import { useState } from 'react';
import './App.css';
import LoginRegister from './Components/LoginRegister/LoginRegister';
import Dashboard from './Components/Dashboard/Dashboard';
import Clients from './Components/Dashboard/Clients';
import Products from './Components/Dashboard/Products';
import Analysis from './Components/Dashboard/Analysis';
import Configuration from './Components/Dashboard/Configuration';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const navigate = useNavigate(); // Usamos el hook navigate para redirigir

  const handleLoginSuccess = (role) => {
    setIsLoggedIn(true);
    setUserRole(role);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);  // Primero actualizar el estado de la sesión
    setUserRole(null);
    navigate('/');  // Redirigir directamente a la página de login/register
  };

  return (
    <div className="App">
      <Routes>
        <Route
          path="/"
          element={isLoggedIn ? <Navigate to="/dashboard" /> : <LoginRegister onLoginSuccess={handleLoginSuccess} />}
        />
        
        {/* Rutas protegidas del dashboard */}
        <Route
          path="/dashboard"
          element={isLoggedIn ? <Dashboard userRole={userRole} onLogout={handleLogout} /> : <Navigate to="/" />}
        />
        <Route
          path="/dashboard/clients"
          element={isLoggedIn ? <Clients userRole={userRole} onLogout={handleLogout} /> : <Navigate to="/" />}
        />
        <Route
          path="/dashboard/products"
          element={isLoggedIn ? <Products userRole={userRole} onLogout={handleLogout} /> : <Navigate to="/" />}
        />
        <Route
          path="/dashboard/analysis"
          element={isLoggedIn ? <Analysis userRole={userRole} onLogout={handleLogout} /> : <Navigate to="/" />}
        />
        <Route
          path="/dashboard/configuration"
          element={isLoggedIn && userRole === 'admin' ? <Configuration userRole={userRole} onLogout={handleLogout} /> : <Navigate to="/dashboard" />}
        />
      </Routes>
    </div>
  );
}

export default App;
