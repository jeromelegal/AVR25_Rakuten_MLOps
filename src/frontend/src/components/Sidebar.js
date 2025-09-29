// frontend/src/components/Sidebar.js
import React, { useState, useContext, useEffect } from 'react';
import { Navbar, Nav, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import styles from './Sidebar.module.css';

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { authenticated } = useContext(AuthContext);

  // Charger l'état de la barre latérale depuis localStorage
  useEffect(() => {
    const savedCollapsed = localStorage.getItem('sidebarCollapsed');
    if (savedCollapsed !== null) {
      setCollapsed(JSON.parse(savedCollapsed));
    }
  }, []);

  // Sauvegarder l'état de la barre latérale dans localStorage
  const toggleSidebar = () => {
    const newCollapsedState = !collapsed;
    setCollapsed(newCollapsedState);
    localStorage.setItem('sidebarCollapsed', JSON.stringify(newCollapsedState));
  };

  if (!authenticated) {
    return null; // Ne pas afficher la barre de navigation si l'utilisateur n'est pas connecté
  }

  return (
    <div className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
      <Navbar bg="light" expand="lg" className="flex-column align-items-start">
        <Button
          variant="outline-secondary"
          onClick={toggleSidebar}
          className="mb-3 d-flex align-items-center justify-content-center"
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            backgroundColor: '#e9ecef',
            borderColor: '#dee2e6',
            color: '#495057'
          }}
        >
          {collapsed ? (
            <i className="bi bi-arrow-right-square-fill"></i>
          ) : (
            <i className="bi bi-arrow-left-square-fill"></i>
          )}
        </Button>
        <Nav className={`flex-column w-100 ${collapsed ? 'd-none' : ''}`}>
          <Nav.Link as={Link} to="/home" className={styles.navLink}>Home</Nav.Link>
          <Nav.Link as={Link} to="/newproduct" className={styles.navLink}>New Product</Nav.Link>
          <Nav.Link as={Link} to="/findproduct" className={styles.navLink}>Find a Product</Nav.Link>
          <Nav.Link as={Link} to="/datalake" className={styles.navLink}>DataLake</Nav.Link>
          <Nav.Link as={Link} to="/datatransform" className={styles.navLink}>DataTransform</Nav.Link>
          <Nav.Link as={Link} to="/dataload" className={styles.navLink}>DataLoad</Nav.Link>
          <Nav.Link as={Link} to="/dataanalyse" className={styles.navLink}>DataAnalyse</Nav.Link>
          <Nav.Link as={Link} to="/datalearn" className={styles.navLink}>DataLearn</Nav.Link>
          <Nav.Link as={Link} to="/search" className={styles.navLink}>SearchAds</Nav.Link>
          <Nav.Link as={Link} to="//ads" className={styles.navLink}>AdDetails</Nav.Link>
        </Nav>
      </Navbar>
    </div>
  );
};

export default Sidebar;
