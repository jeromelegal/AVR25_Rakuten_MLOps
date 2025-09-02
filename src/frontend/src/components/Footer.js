// frontend/src/components/Footer.js
import React from 'react';
import { Container } from 'react-bootstrap';

const Footer = () => {
  return (
    <footer className="bg-light py-3 mt-auto w-100">
      <Container fluid>
        <div className="text-center">
          <span className="text-muted">© 2023 MyApp. All rights reserved.</span>
        </div>
      </Container>
    </footer>
  );
};

export default Footer;
