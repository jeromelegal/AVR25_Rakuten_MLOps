// ProductCategoryButton.js
import React from 'react';
import { Button } from 'react-bootstrap';

/**
 * Props:
 * - onClick: () => void
 * - selectedCategory?: { code: number|string, label: string } | null
 */
const ProductCategoryButton = ({ onClick, selectedCategory }) => (
  <Button variant="primary" onClick={onClick}>
    {selectedCategory?.label ? `Catégorie : ${selectedCategory.label}` : 'Choisir une catégorie'}
  </Button>
);

export default ProductCategoryButton;
