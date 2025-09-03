import React from 'react';
import { Button } from 'react-bootstrap';

const ProductCategoryButton = ({ onClick }) => (
  <Button variant="primary" onClick={onClick}>
    Choose Category
  </Button>
);

export default ProductCategoryButton;