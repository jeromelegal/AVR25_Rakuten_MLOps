import React, { useState } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';
import ValidateButton from './ValidateButton';
import { rakutenCategories } from '../constants/rakutenCategories';

const ProductCategoryModal = ({ show, onHide, categories = [], onSelect }) => {
  const [changingCategory, setChangingCategory] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');

  // Example category proposal
  const categoryProposal = "Electronics";
  const categoriesToShow = rakutenCategories;


  const handleValidate = () => {
    onSelect(changingCategory && selectedCategory ? selectedCategory : categoryProposal);
    setChangingCategory(false);
    setSelectedCategory('');
  };

  const handleChangeCategoryClick = () => {
    setChangingCategory(true);
  };

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
          background: changingCategory ? '#f8d7da' : '#f8f9fa',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          textAlign: 'center',
          fontSize: '1.2rem',
          fontWeight: '500',
          opacity: changingCategory ? 0.6 : 1
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
          {changingCategory && (
            <div style={{ color: '#a94442', marginTop: '0.5rem', fontSize: '0.95rem' }}>
              This value is not taken into account, please select a new category below.
            </div>
          )}
        </div>
        {changingCategory && (
          <Form.Group controlId="selectCategory" style={{ marginBottom: '1.5rem' }}>
            <Form.Label>Select a category</Form.Label>
            <Form.Select
              value={selectedCategory}
              onChange={e => setSelectedCategory(e.target.value)}
            >
              <option value="">-- Choose a category --</option>
              {categoriesToShow.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </Form.Select>
          </Form.Group>
        )}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '1rem'
        }}>
          {!changingCategory && (
            <Button
              style={{ backgroundColor: '#ffe5b4', color: '#333', border: 'none' }}
              onClick={handleChangeCategoryClick}
            >
              Change category
            </Button>
          )}
          <ValidateButton
            onClick={handleValidate}
            disabled={changingCategory && !selectedCategory}
          >
            Validate
          </ValidateButton>
        </div>
      </Modal.Body>
    </Modal>
  );
};

export default ProductCategoryModal;