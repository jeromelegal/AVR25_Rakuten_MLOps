import React from 'react';
import { Modal, Button } from 'react-bootstrap';

const ProductCategoryModal = ({ show, onHide, categories, onSelect }) => {
  // Example category proposal
  const categoryProposal = "Electronics";

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header>
        <Modal.Title>Category</Modal.Title>
        <Button
          variant="link"
          onClick={onHide}
          style={{
            fontSize: '1.5rem',
            lineHeight: '1',
            color: '#000',
            textDecoration: 'none',
            position: 'absolute',
            top: '10px',
            right: '15px'
          }}
        >
          ×
        </Button>
      </Modal.Header>
      <Modal.Body>
        <div style={{
          padding: '1rem',
          background: '#f8f9fa',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          textAlign: 'center',
          fontSize: '1.2rem',
          fontWeight: '500'
        }}>
          <span>Category proposal:</span>
          <div style={{
            marginTop: '0.5rem',
            padding: '0.5rem 1rem',
            background: '#e3eafc',
            borderRadius: '6px',
            display: 'inline-block',
            fontSize: '1.1rem'
          }}>
            {categoryProposal}
          </div>
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '1rem'
        }}>
          <Button
            style={{ backgroundColor: '#ffe5b4', color: '#333', border: 'none' }}
            onClick={() => {}}
          >
            Change category
          </Button>
          <Button
            style={{ backgroundColor: '#d4edda', color: '#155724', border: 'none' }}
            onClick={() => onSelect(categoryProposal)}
          >
            Validate
          </Button>
        </div>
      </Modal.Body>
    </Modal>
  );
};

export default ProductCategoryModal;