// frontend/src/pages/PocInput.js
import React, {useState} from 'react';
import ProductDescriptionInput from '../components/ProductDescriptionInput';
import ProductPictureInput from '../components/ProductPictureInput';

const PocInput = () => {
  const [description, setDescription] = useState('');
  const [picture, setPicture] = useState(null);

  const handleDescriptionChange = (e) => {
    setDescription(e.target.value);
  };

  const handlePictureChange = (e) => {
    setPicture(e.target.files[0]);
  };

  return (
    <div>
      <h1>PocInput Page</h1>
      <ProductDescriptionInput value={description} onChange={handleDescriptionChange} />
      <ProductPictureInput onChange={handlePictureChange} />
    </div>
  );
};

export default PocInput;