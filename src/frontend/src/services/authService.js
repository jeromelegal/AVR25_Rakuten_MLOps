// frontend/src/services/authService.js
import axios from 'axios';

const TOKEN_KEY = 'access_token';

// Fonction pour récupérer le token du localStorage
export const getAuthToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

// Fonction pour stocker le token dans le localStorage
export const storeToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
};

// Fonction pour supprimer le token du localStorage et réinitialiser les préférences de l'utilisateur
export const logout = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem('username');
  localStorage.removeItem('userSettings'); // Réinitialiser les préférences de l'utilisateur
};

// Fonction pour vérifier si l'utilisateur est connecté
export const isAuthenticated = () => {
  const token = getAuthToken();
  return !!token;
};

// Fonction pour obtenir le nom d'utilisateur
export const getUsername = () => {
  return localStorage.getItem('username');
};

export const login = async (username, password) => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('grant_type', 'password');

    const response = await axios.post(
      `/api/protected/login`,
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    const { access_token, username: responseUsername } = response.data;
    if (access_token) {
      storeToken(access_token);
      // Ensure the username from the response is stored in localStorage
      if (responseUsername) {
        localStorage.setItem('username', responseUsername);
      }
    }
    return { success: true, data: response.data };
  } catch (error) {
    console.error('Login failed:', error);
    return { success: false, error: error.response ? error.response.data : error.message };
  }
};

export const signup = async (username, email, password) => {
  try {
    const response = await axios.post(`/api/protected/signup`, {
      username,
      email,
      password,
    });

    return { success: true, data: response.data };
  } catch (error) {
    console.error('Signup failed:', error);
    return { success: false, error: error.response ? error.response.data : error.message };
  }
};
