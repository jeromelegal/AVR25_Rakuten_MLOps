// frontend/src/components/LogoutButton.js
import React, { useContext } from 'react';
import { Button } from 'react-bootstrap';
import { logout } from '../services/authService';
import { useHistory } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const LogoutButton = () => {
  const history = useHistory();
  const { setAuthenticated } = useContext(AuthContext);

  const handleLogout = () => {
    logout();
    setAuthenticated(false);
    history.push('/auth');
  };

  return (
    <Button
      variant="outline-secondary"
      onClick={handleLogout}
      style={{ marginLeft: 'auto' }}
    >
      Logout
    </Button>
  );
};

export default LogoutButton;
