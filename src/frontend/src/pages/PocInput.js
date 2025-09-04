// frontend/src/pages/PocInput.js
import React, {useState} from 'react';
import ProductDescriptionInput from '../components/ProductDescriptionInput';
import ProductPictureInput from '../components/ProductPictureInput';
import ProductTitleInput from '../components/ProductTitleInput';
import ProductCategoryButton from '../components/ProductCategoryButton';
import ProductCategoryModal from '../components/ProductCategoryModal';
import ValidateButton from '../components/ValidateButton';

const PocInput = () => {
  const [description, setDescription] = useState('');
  const [picture, setPicture] = useState(null);
  const [title, setTitle] = useState('');
  const [categoryModalShow, setCategoryModalShow] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);

  const handleCategoryButtonClick = () => {
    setCategoryModalShow(true);
  };

  const handleTitleChange = (e) => {
    setTitle(e.target.value);
  };

  const handleDescriptionChange = (e) => {
    setDescription(e.target.value);
  };

  const handlePictureChange = (e) => {
    setPicture(e.target.files[0]);
  };

  const handleCategorySelect = (cat) => {
    setSelectedCategory(cat);
    setCategoryModalShow(false);
  };

   // Example save handler
  const handleValidateAll = () => {
    // Save logic here (e.g., send to backend)
    const productData = {
      title,
      description,
      category: selectedCategory,
      picture
    };
    console.log('Saving product:', productData);
    // Add your save-to-database logic here
  };

  return (
    <div>
      <h1>PocInput Page</h1>
      <div style={{ width: '60%', margin: '0 auto' }}>
        <ProductTitleInput value={title} onChange={(e) => setTitle(e.target.value)} />
        <div style={{ height: '2rem' }}></div> 
        <ProductPictureInput onChange={handlePictureChange} />
        <div style={{ height: '2rem' }}></div> 
        <ProductDescriptionInput value={description} onChange={handleDescriptionChange} />
        <div style={{ height: '2rem' }}></div> 
        <ProductCategoryButton onClick={handleCategoryButtonClick} />
        <ValidateButton
          onClick={handleValidateAll}
          disabled={!title || !description || !selectedCategory || !picture}
        >
          Validate Product
        </ValidateButton>
      </div>
      <ProductCategoryModal
        show={categoryModalShow}
        onHide={() => setCategoryModalShow(false)}
        onSelect={handleCategorySelect}
      />
      {selectedCategory && <p>Selected Category: {selectedCategory}</p>}
    </div>
  );
};

export default PocInput;