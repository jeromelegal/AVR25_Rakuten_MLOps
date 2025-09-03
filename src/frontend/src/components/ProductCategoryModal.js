import React from 'react';
import { Modal, Button } from 'react-bootstrap';

const ProductCategoryModal = ({ show, onHide, categories, onSelect }) => (
  <Modal show={show} onHide={onHide} centered>
    <Modal.Header>
      <Modal.Title>Category</Modal.Title>
      <Button variant="link" onClick={onHide} style={{ fontSize: '1.5rem', lineHeight: '1', color: '#000', textDecoration: 'none', position: 'absolute', top: '10px', right: '15px' }}>
        ×
      </Button>
    </Modal.Header>
    <Modal.Body>
      {categories.map((cat) => (
        <Button
          key={cat}
          variant="outline-secondary"
          className="m-2"
          onClick={() => onSelect(cat)}
        >
          {cat}
        </Button>
      ))}
    </Modal.Body>
  </Modal>
);

export default ProductCategoryModal;