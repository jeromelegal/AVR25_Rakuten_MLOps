import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Spinner } from 'react-bootstrap';
import ValidateButton from './ValidateButton';
import { rakutenCategories } from '../constants/rakutenCategories';

const ProductCategoryModal = ({ show, onHide, onSelect }) => {
  const [changingCategory, setChangingCategory] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');

  const [categoryProposal, setCategoryProposal] = useState(null);
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  // Example category proposal
  // const categoryProposal = "Electronics";
  const categoriesToShow = rakutenCategories;

  // Fonction pour appeler ton API
  const fetchCategory = async () => {
    setLoading(true);
    setElapsed(0);
    setCategoryProposal(null);

    const start = Date.now();
    try {
      // ⚠️ adapte l’URL à ton backend
      const res = await fetch('/api/predict-category');
      const data = await res.json();
      
      setCategoryProposal(data.category);
    } catch (err) {
      setCategoryProposal('⚠️ Erreur de prédiction');
    } finally {
      const end = Date.now();
      setElapsed(((end - start) / 1000).toFixed(1));
      setLoading(false);
    }
  };

  // Déclenche automatiquement au montage
  useEffect(() => {
    if (show) {
      fetchCategory();
    }
  }, [show]);

  const handleValidate = () => {
    let categoryObject;
    if (changingCategory && selectedCategory) {
      // Find the category object by id
      categoryObject = categoriesToShow.find(cat => String(cat.id) === String(selectedCategory));
    } else {
      // Use the proposal as a fallback (find by name)
      categoryObject = categoriesToShow.find(cat => cat.name === categoryProposal) || { name: categoryProposal };
    }

    if (categoryObject){
      const selected = {
        id: categoryObject.id,
        name: categoryObject.name
      };
      onSelect(selected);
    }
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
        <div 
         style={{
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
          <div
            style={{
              marginTop: '0.5rem',
              padding: '0.5rem 1rem',
              background: '#e3eafc',
              borderRadius: '6px',
              display: 'inline-block',
              fontSize: '1.1rem',
              minWidth: '150px',
            }}
          >
              {loading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Spinner animation="border" size="sm" />
                  <span>Predicting...</span>
                </div>
              ) : (
                categoryProposal
              )}
            </div>
          </div>

          {!loading && elapsed > 0 && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#555' }}>
              Response time: {elapsed}s
            </div>
          )}

          {changingCategory && (
            <div style={{ color: '#a94442', marginTop: '0.5rem', fontSize: '0.95rem' }}>
              This value is not taken into account, please select a new category below.
            </div>
          )}

          <div style={{ marginTop: '1rem' }}>
            <Button variant="outline-primary" size="sm" onClick={fetchCategory}>
              🔄 Force prediction
            </Button>
          </div>
       
        <div style={{ height: '1.5rem' }}></div>  
        {changingCategory && (
          <Form.Group controlId="selectCategory" style={{ marginBottom: '1.5rem' }}>
            <Form.Label>Select a category</Form.Label>
            <Form.Select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="">-- Choose a category --</option>
              {categoriesToShow.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
        )}

        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '1rem',
          }}
        >
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