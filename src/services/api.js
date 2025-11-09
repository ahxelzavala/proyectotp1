// frontend/src/services/api.js

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

console.log('🔗 API URL:', API_URL); // Para debug

export const authService = {
  login: async (email, password) => {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error en login');
      }

      const data = await response.json();
      
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  register: async (email, password, name) => {
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error en registro');
      }

      return await response.json();
    } catch (error) {
      console.error('Register error:', error);
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getToken: () => {
    return localStorage.getItem('token');
  },

  getUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  }
};

export const analystService = {
  getAll: async () => {
    try {
      const token = authService.getToken();
      
      const response = await fetch(`${API_URL}/users/analysts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Error obteniendo analistas');
      }

      const data = await response.json();
      
      // El backend puede devolver { success, analysts } o solo array
      return data.analysts || data;
    } catch (error) {
      console.error('Get analysts error:', error);
      throw error;
    }
  },

  create: async (firstName, lastName, email) => {
    try {
      const token = authService.getToken();
      
      const response = await fetch(`${API_URL}/users/analysts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email: email
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error creando analista');
      }

      return await response.json();
    } catch (error) {
      console.error('Create analyst error:', error);
      throw error;
    }
  },

  update: async (analystId, firstName, lastName, email) => {
    try {
      const token = authService.getToken();
      
      const response = await fetch(`${API_URL}/users/analysts/${analystId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email: email
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error actualizando analista');
      }

      return await response.json();
    } catch (error) {
      console.error('Update analyst error:', error);
      throw error;
    }
  },

  delete: async (analystId) => {
    try {
      const token = authService.getToken();
      
      const response = await fetch(`${API_URL}/users/analysts/${analystId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error eliminando analista');
      }

      return await response.json();
    } catch (error) {
      console.error('Delete analyst error:', error);
      throw error;
    }
  }
};

export default API_URL;