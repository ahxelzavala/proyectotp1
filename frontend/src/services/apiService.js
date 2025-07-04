// URL del backend desplegado en Cloud Run
const API_URL = process.env.REACT_APP_API_URL || 'https://proyectoreact-backend-741997725999.us-central1.run.app';

// Función helper para hacer peticiones
const apiRequest = async (endpoint, options = {}) => {
  try {
    const url = `${API_URL}${endpoint}`;
    console.log('Haciendo petición a:', url); // Para debug
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    } else {
      return await response.text();
    }
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

// Métodos HTTP
export const apiGet = (endpoint) => apiRequest(endpoint);

export const apiPost = (endpoint, data) => 
  apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const apiPut = (endpoint, data) => 
  apiRequest(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const apiDelete = (endpoint) => 
  apiRequest(endpoint, {
    method: 'DELETE',
  });

// Función para probar la conexión
export const testConnection = async () => {
  try {
    const response = await apiGet('/'); // O cualquier endpoint que tengas
    console.log('Conexión exitosa:', response);
    return response;
  } catch (error) {
    console.error('Error de conexión:', error);
    throw error;
  }
};

export default { apiGet, apiPost, apiPut, apiDelete, testConnection };