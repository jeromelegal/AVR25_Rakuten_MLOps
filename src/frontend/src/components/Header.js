// frontend/src/components/Header.js
import React, { useContext } from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import LogoutButton from './LogoutButton';

const Header = () => {
  const { authenticated } = useContext(AuthContext);

  return (
    <Navbar bg="light" expand="lg" className="w-100">
      <Container fluid>
        <Navbar.Brand as={Link} to="/" className="mx-auto">MyApp</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            {authenticated ? (
              <LogoutButton />
            ) : (
              <Nav.Link as={Link} to="/auth">Login</Nav.Link>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Header;
