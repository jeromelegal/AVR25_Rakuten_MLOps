// frontend/src/pages/HomePage.js
import React from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import { getUsername } from '../services/authService';
import HomeMessage from '../components/HomeMessage';

const HomePage = () => {
  const username = getUsername();

  return (
    <Container fluid className="mt-4">
      <Row>
        <Col>
            <HomeMessage username={username} />
        </Col>
      </Row>
    </Container>
  );
};

export default HomePage;
