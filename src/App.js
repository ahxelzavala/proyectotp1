import { useState } from 'react';
import './App.css';
import LoginRegister from './Components/LoginRegister/LoginRegister';
import Dashboard from './Components/Dashboard/Dashboard';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const navigate = useNavigate();

  const handleLoginSuccess = (role) => {
    setIsLoggedIn(true);
    setUserRole(role);
    navigate('/dashboard');
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserRole(null);
    navigate('/');
  };

  return (
    <div className="App">
      <Routes>
        <Route path="/" element={
          isLoggedIn ? <Navigate to="/dashboard" /> : <LoginRegister onLoginSuccess={handleLoginSuccess} />
        } />
        <Route path="/dashboard" element={
          isLoggedIn ? <Dashboard userRole={userRole} onLogout={handleLogout} /> : <Navigate to="/" />
        } />
      </Routes>
    </div>
  );
}

export default App;
