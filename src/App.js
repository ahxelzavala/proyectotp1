import { useState, useEffect } from 'react';
import './App.css';
import LoginRegister from './Components/LoginRegister/LoginRegister';
import Dashboard from './Components/Dashboard/Dashboard';
import Clients from './Components/Dashboard/Clients';
import Products from './Components/Dashboard/Products';
import Analysis from './Components/Dashboard/Analysis';
import Configuration from './Components/Dashboard/Configuration';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { authService } from './services/api';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Verificar sesión al cargar la app
  useEffect(() => {
    const checkAuth = () => {
      try {
        const token = localStorage.getItem('access_token');
        const user = authService.getCurrentUser();
        
        if (token && user) {
          console.log('✅ Sesión encontrada:', user);
          setIsLoggedIn(true);
          setUserRole(user.role);
        } else {
          console.log('ℹ️ No hay sesión activa');
          setIsLoggedIn(false);
          setUserRole(null);
        }
      } catch (error) {
        console.error('Error verificando autenticación:', error);
        setIsLoggedIn(false);
        setUserRole(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLoginSuccess = (role) => {
    console.log('🎉 Login exitoso en App.js, rol:', role);
    setIsLoggedIn(true);
    setUserRole(role);
    navigate('/dashboard');
  };

  const handleLogout = () => {
    console.log('👋 Cerrando sesión...');
    authService.logout();
    setIsLoggedIn(false);
    setUserRole(null);
    navigate('/');
  };

  // Mostrar loading mientras verifica la sesión
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: '#062463',
        color: 'white',
        fontSize: '1.5rem'
      }}>
        Cargando...
      </div>
    );
  }

  return (
    <div className="App">
      <Routes>
        <Route
          path="/"
          element={
            isLoggedIn ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <LoginRegister onLoginSuccess={handleLoginSuccess} />
            )
          }
        />
        
        {/* Rutas protegidas del dashboard */}
        <Route
          path="/dashboard"
          element={
            isLoggedIn ? (
              <Dashboard userRole={userRole} onLogout={handleLogout} />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        
        <Route
          path="/dashboard/clients"
          element={
            isLoggedIn ? (
              <Clients userRole={userRole} onLogout={handleLogout} />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        
        <Route
          path="/dashboard/products"
          element={
            isLoggedIn ? (
              <Products userRole={userRole} onLogout={handleLogout} />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        
        <Route
          path="/dashboard/analysis"
          element={
            isLoggedIn ? (
              <Analysis userRole={userRole} onLogout={handleLogout} />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        
        <Route
          path="/dashboard/configuration"
          element={
            isLoggedIn && userRole === 'admin' ? (
              <Configuration userRole={userRole} onLogout={handleLogout} />
            ) : (
              <Navigate to="/dashboard" replace />
            )
          }
        />
        
        {/* Ruta catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;