// frontend/src/components/Layout.js
import React, { useContext } from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import Sidebar from './Sidebar';
import Header from './Header';
import Footer from './Footer';
import { AuthContext } from '../context/AuthContext';
import styles from './Layout.module.css';

const Layout = ({ children }) => {
  const { authenticated } = useContext(AuthContext);

  return (
    <>
      <Header />
      <Container fluid className={styles.mainContent}>
        <Row>
          {authenticated && (
            <Col md={2} style={{ padding: 0 }}>
              <Sidebar />
            </Col>
          )}
          <Col md={authenticated ? 10 : 12}>
            {children}
          </Col>
        </Row>
      </Container>
      <Footer />
    </>
  );
};

export default Layout;
