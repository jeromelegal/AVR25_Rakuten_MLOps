// frontend/src/components/HomeMessage.js
import React, { useState, useEffect } from 'react';
import { Card, Button } from 'react-bootstrap';

const HomeMessage = ({ username }) => {
  const [showMessage, setShowMessage] = useState(true);

  useEffect(() => {
    // Vérifier si le message a été masqué précédemment
    const userSettings = JSON.parse(localStorage.getItem('userSettings')) || {};
    if (userSettings.homeMessageHidden) {
      setShowMessage(false);
    }
  }, []);

  const handleClose = () => {
    // Masquer le message et stocker cet état dans les préférences de l'utilisateur
    setShowMessage(false);
    const userSettings = JSON.parse(localStorage.getItem('userSettings')) || {};
    userSettings.homeMessageHidden = true;
    localStorage.setItem('userSettings', JSON.stringify(userSettings));
  };

  if (!showMessage) {
    return null;
  }

  return (
    <Card>
      <Card.Body>
        <Card.Title className="text-center mb-4">Welcome to the Home Page</Card.Title>
        <Card.Text>
          Hello, {username || 'Guest'}! You have successfully logged in.
        </Card.Text>
        <Button
          variant="link"
          onClick={handleClose}
          style={{ position: 'absolute', top: '10px', right: '10px' }}
        >
          ×
        </Button>
      </Card.Body>
    </Card>
  );
};

export default HomeMessage;
