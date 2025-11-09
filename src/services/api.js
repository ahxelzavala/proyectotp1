// frontend/src/services/api.js

const API_URL = 'https://proyectotp1.onrender.com';

console.log('🔗 API URL:', API_URL);

export const authService = {
  login: async (email, password) => {
    try {
      console.log('🔐 Intentando login con:', email);
      
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
      console.log('✅ Login response:', data);
      
      // Guardar token y usuario
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      console.log('✅ Login exitoso, datos guardados');
      
      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('❌ Login error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  },

  register: async (email, password, name) => {
    try {
      console.log('📝 Intentando registro:', email);
      
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

      const data = await response.json();
      console.log('✅ Registro exitoso:', data);
      
      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('❌ Register error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    console.log('👋 Sesión cerrada');
  },

  getToken: () => {
    return localStorage.getItem('token');
  },

  getUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated: () => {
    const token = localStorage.getItem('token');
    return !!token;
  }
};

export const analystService = {
  getAll: async () => {
    try {
      const token = authService.getToken();
      
      console.log('📋 Obteniendo analistas...');
      
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
      console.log('✅ Analistas obtenidos:', data);
      
      // El backend devuelve { success, analysts }
      return data.analysts || [];
    } catch (error) {
      console.error('❌ Get analysts error:', error);
      throw error;
    }
  },

  create: async (firstName, lastName, email) => {
    try {
      const token = authService.getToken();
      
      console.log('📝 Creando analista:', { firstName, lastName, email });
      
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

      const data = await response.json();
      console.log('✅ Analista creado:', data);
      
      return data;
    } catch (error) {
      console.error('❌ Create analyst error:', error);
      throw error;
    }
  },

  update: async (analystId, firstName, lastName, email) => {
    try {
      const token = authService.getToken();
      
      console.log('✏️ Actualizando analista:', analystId);
      
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

      const data = await response.json();
      console.log('✅ Analista actualizado:', data);
      
      return data;
    } catch (error) {
      console.error('❌ Update analyst error:', error);
      throw error;
    }
  },

  delete: async (analystId) => {
    try {
      const token = authService.getToken();
      
      console.log('🗑️ Eliminando analista:', analystId);
      
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

      const data = await response.json();
      console.log('✅ Analista eliminado');
      
      return data;
    } catch (error) {
      console.error('❌ Delete analyst error:', error);
      throw error;
    }
  }
};

export default API_URL;