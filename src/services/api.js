// src/services/api.js
import axios from 'axios';

// Configurar la URL base del backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Crear instancia de axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token a todas las peticiones
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de respuesta
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// ===== SERVICIOS DE AUTENTICACIÓN =====

export const authService = {
  // Login
  login: async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, user } = response.data;
      
      // Guardar token y usuario en localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Error en el login',
      };
    }
  },

  // Registro
  register: async (name, email, password) => {
    try {
      const response = await api.post('/auth/register', {
        name,
        email,
        password,
      });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Error en el registro',
      };
    }
  },

  // Logout
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  // Verificar si está logueado
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },

  // Obtener usuario actual
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};

// ===== SERVICIOS DE GESTIÓN DE ANALISTAS =====

export const analystService = {
  // Obtener todos los analistas
  getAll: async () => {
    try {
      const response = await api.get('/users/analysts');
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Error obteniendo analistas',
      };
    }
  },

  // Crear analista
  create: async (firstName, lastName, email) => {
    try {
      const response = await api.post('/users/analysts', {
        first_name: firstName,
        last_name: lastName,
        email,
      });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Error creando analista',
      };
    }
  },

  // Actualizar analista
  update: async (id, firstName, lastName, email) => {
    try {
      const response = await api.put(`/users/analysts/${id}`, {
        first_name: firstName,
        last_name: lastName,
        email,
      });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Error actualizando analista',
      };
    }
  },

  // Eliminar analista
  delete: async (id) => {
    try {
      const response = await api.delete(`/users/analysts/${id}`);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Error eliminando analista',
      };
    }
  },
};

export default api;