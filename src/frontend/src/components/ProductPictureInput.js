import React from 'react';
import { Form } from 'react-bootstrap';

const ProductPictureInput = ({ onChange }) => (
  <Form.Group controlId="productPicture">
    <Form.Label>Product Picture</Form.Label>
    <Form.Control
      type="file"
      accept="image/*"
      onChange={onChange}
    />
  </Form.Group>
);

export default ProductPictureInput;