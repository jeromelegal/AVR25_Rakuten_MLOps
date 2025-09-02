// frontend/src/components/Text.js
import React from 'react';
import { Card } from 'react-bootstrap';

const Text = ({ username }) => {
  return (
    <Card.Text>
      Hello, {username || 'Guest'}! You have successfully logged in.
    </Card.Text>
  );
};

export default Text;
