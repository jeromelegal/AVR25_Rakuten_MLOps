import React from 'react';
import { Form, ButtonGroup, Button } from 'react-bootstrap';

const formatText = (command) => {
  document.execCommand(command, false, null);
};

const ProductDescriptionInput = ({ value, onChange }) => (
  <Form.Group controlId="productDescription">
    <Form.Label>Product Description</Form.Label>
    <div style={{ marginBottom: '0.5rem' }}></div> 
    <ButtonGroup className="mb-2">
      <Button variant="outline-secondary" size="sm" onClick={() => formatText('bold')}>
        <b>B</b>
      </Button>
      <Button variant="outline-secondary" size="sm" onClick={() => formatText('italic')}>
        <i>I</i>
      </Button>
      <Button variant="outline-secondary" size="sm" onClick={() => formatText('underline')}>
        <u>U</u>
      </Button>
    </ButtonGroup>
    <Form.Control
      as="textarea"
      rows={5}
      placeholder="Enter product description"
      value={value}
      onChange={onChange}
      style={{ resize: 'vertical' }}
    />
  </Form.Group>
);

export default ProductDescriptionInput;