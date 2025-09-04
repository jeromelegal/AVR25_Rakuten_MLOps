import React from 'react';
import { Form } from 'react-bootstrap';

const ProductTitleInput = ({ value, onChange }) => (
  <Form.Group controlId="productTitle">
    <Form.Label>Product Title</Form.Label>
    <Form.Control
      type="text"
      placeholder="Enter product title"
      value={value}
      onChange={onChange}
      maxLength={100}
    />
  </Form.Group>
);

export default ProductTitleInput;