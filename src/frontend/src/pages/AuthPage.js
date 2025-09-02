// frontend/src/pages/AuthPage.js
import React, { useContext } from 'react';
import { Redirect, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import LoginForm from '../components/LoginForm';
import SignupForm from '../components/SignupForm';
import { Container, Row, Col, Card } from 'react-bootstrap';

const AuthPage = () => {
  const { authenticated } = useContext(AuthContext);
  const location = useLocation();

  // Rediriger vers la page d'accueil si l'utilisateur est déjà authentifié
  if (authenticated) {
    return <Redirect to={location.state?.from || '/home'} />;
  }

  return (
    <Container className="mt-4">
      <Row className="justify-content-center">
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title className="text-center mb-4">Login</Card.Title>
              <LoginForm />
            </Card.Body>
          </Card>
          <Card className="mt-4">
            <Card.Body>
              <Card.Title className="text-center mb-4">Signup</Card.Title>
              <SignupForm />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default AuthPage;
