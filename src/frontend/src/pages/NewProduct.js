import {useState} from 'react';
import ProductDescriptionInput from '../components/ProductDescriptionInput';
import ProductPictureInput from '../components/ProductPictureInput';
import ProductTitleInput from '../components/ProductTitleInput';
import ProductCategoryButton from '../components/ProductCategoryButton';
import ProductCategoryModal from '../components/ProductCategoryModal';
import ValidateButton from '../components/ValidateButton';
import { handleValidateAll } from './handlers/handleValidateAll';

const API_BASE = process.env.API_GATEWAY_BASE_URL

const NewProduct = () => {
  const accessToken = localStorage.getItem('access_token');
  const [description, setDescription] = useState('');
  const [picture, setPicture] = useState(null);
  const [title, setTitle] = useState('');
  const [categoryModalShow, setCategoryModalShow] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);

  const handleCategoryButtonClick = () => {
    setCategoryModalShow(true);
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
  const onValidateClick = async () => {
    try {
      const formData = new FormData();
      formData.append("designation", title);
      formData.append("description", description);
      formData.append("category_code", selectedCategory.code);
      formData.append("category_label", selectedCategory.name);
      formData.append("file", picture);

      const headers = {};
      if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
      const response = await fetch(`${API_BASE}/create_ad`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Erreur API: ${response.status}`);
      }

      const payload = await response.json();
      console.log("Annonce créée:", payload);
      alert(`Annonce créée avec ID: ${payload.ad.id}`);
    } catch (err) {
      console.error("Erreur lors de la création:", err);
      alert("Impossible de créer l'annonce");
    }
  };

  return (
    <div>
      <h1>Add a new product</h1>
      <div style={{ width: '60%', margin: '0 auto' }}>
        <ProductTitleInput value={title} onChange={(e) => setTitle(e.target.value)} />
        <div style={{ height: '2rem' }}></div> 
        <ProductPictureInput onChange={handlePictureChange} />
        <div style={{ height: '2rem' }}></div> 
        <ProductDescriptionInput value={description} onChange={handleDescriptionChange} />
        <div style={{ height: '2rem' }}></div> 
        <ProductCategoryButton onClick={handleCategoryButtonClick} />
        {selectedCategory && (
        <div
          style={{
            background: '#e3eafc',
            color: '#155a9e',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            margin: '1rem 0',
            fontWeight: '500',
            textAlign: 'center'
          }}
        >
          Selected Category: {selectedCategory.name}
        </div>
      )}
        <div style={{ height: '1rem' }}></div> 
        <ValidateButton
          onClick={onValidateClick}
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
    </div>
  );
};

export default NewProduct;