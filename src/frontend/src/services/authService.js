// frontend/src/services/authService.js
import axios from 'axios';
import qs from 'qs';

// Fonction pour récupérer le token du localStorage
export const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

// Fonction pour stocker le token dans le localStorage
export const storeToken = (token) => {
  localStorage.setItem('authToken', JSON.stringify(token));
};

// Fonction pour supprimer le token du localStorage et réinitialiser les préférences de l'utilisateur
export const logout = () => {
  localStorage.removeItem('authToken');
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
  let username = localStorage.getItem('username');
  if (username) {
    return username;
  }

  const token = getAuthToken();
  if (!token) return null;

  try {
    const tokenData = JSON.parse(token);
    username = tokenData.username;
    if (username) {
      localStorage.setItem('username', username);
    }
    return username;
  } catch (error) {
    console.error('Invalid token:', error);
    return null;
  }
};

// Autres fonctions existantes...
export const login = async (username, password) => {
  try {
    const response = await axios.post(`/api/protected/login`, qs.stringify({
      username,
      password,
      grant_type: 'password',
    }), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const token = response.data.access_token;
    storeToken(token);

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
