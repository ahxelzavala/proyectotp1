// src/config.js
const config = {
  API_URL: process.env.REACT_APP_API_URL || 
           (window.location.hostname === 'localhost' 
             ? 'http://localhost:8000' 
             : 'https://proyectotp1.onrender.com')
};

export default config;