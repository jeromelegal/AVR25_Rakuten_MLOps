import React from 'react';
import { Form } from 'react-bootstrap';

const ProductDescriptionInput = ({ value, onChange }) => (
  <Form.Group controlId="productDescription">
    <Form.Label>Product Description</Form.Label>
    <Form.Control
      type="text"
      placeholder="Enter product description"
      value={value}
      onChange={onChange}
    />
  </Form.Group>
);

export default ProductDescriptionInput;