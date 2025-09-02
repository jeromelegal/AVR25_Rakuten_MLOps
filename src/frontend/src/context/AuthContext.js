// frontend/src/context/AuthContext.js
import React, { createContext, useState, useEffect } from 'react';
import { isAuthenticated } from '../services/authService';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    // Vérifier l'état d'authentification au montage du composant
    const isAuth = isAuthenticated();
    setAuthenticated(isAuth);
  }, []);

  return (
    <AuthContext.Provider value={{ authenticated, setAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
};
