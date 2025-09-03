import React, { useState } from 'react';
import { Form, Image } from 'react-bootstrap';

const ProductPictureInput = ({ onChange }) => {
  const [preview, setPreview] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPreview(URL.createObjectURL(file));
    } else {
      setPreview(null);
    }
    onChange(e);
  };

  return (
    <Form.Group controlId="productPicture">
      <Form.Label>Product Picture</Form.Label>
      <Form.Control
        type="file"
        accept="image/*"
        onChange={handleFileChange}
      />
      {preview && (
        <div style={{ marginTop: '1rem' }}>
          <Image src={preview} alt="Preview" thumbnail style={{ maxWidth: '200px' }} />
        </div>
      )}
    </Form.Group>
  );
};

export default ProductPictureInput;