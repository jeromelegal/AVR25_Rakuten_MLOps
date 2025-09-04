import React from 'react';
import { Button } from 'react-bootstrap';

const ValidateButton = ({ onClick, disabled, children }) => (
  <Button
    style={{ backgroundColor: '#d4edda', color: '#155724', border: 'none' }}
    onClick={onClick}
    disabled={disabled}
  >
    {children || 'Validate'}
  </Button>
);

export default ValidateButton;