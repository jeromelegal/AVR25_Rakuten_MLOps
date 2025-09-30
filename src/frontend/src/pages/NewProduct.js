import {useState} from 'react';
import ProductDescriptionInput from '../components/ProductDescriptionInput';
import ProductPictureInput from '../components/ProductPictureInput';
import ProductTitleInput from '../components/ProductTitleInput';
import ProductCategoryButton from '../components/ProductCategoryButton';
import ProductCategoryModal from '../components/ProductCategoryModal';
import ValidateButton from '../components/ValidateButton';
import axios from 'axios';
import { getAuthToken } from '../services/authService'; // Import the token getter
// import qs from 'qs';
// import { handleValidateAll } from './handlers/handleValidateAll';

const API_BASE = `/api/protected`

const NewProduct = () => {
  //const accessToken = getAuthToken();
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
     const accessToken = getAuthToken();
      if (!accessToken) {
        alert("You must be logged in to create a product.");
        return;
      }

    try {
      const formData = new FormData();
      formData.append("designation", title);
      formData.append("description", description);
      formData.append("category_code", selectedCategory.code);
      formData.append("category_label", selectedCategory.label);
      formData.append("file", picture);


      for (const [k, v] of formData.entries()) {
        console.debug("[create_ad][form]", k, v instanceof File ? `${v.name} (${v.size}B)` : v);
      }

      const headers = {
        'Accept': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      };
      
      const res = await axios.post(`${API_BASE}/create_ad`, formData, {
        headers,
      });
       // axios puts payload in res.data and status in res.status
      console.log("Annonce créée:", res.data);
      const adId = res?.data?.ad?.id ?? res?.data?.id ?? 'unknown';
      alert(`Annonce créée avec ID: ${adId}`);

    } catch (err) {
      const res = err?.response;
      console.error("[create_ad][err]", res?.status, res?.headers, res?.data);
      console.error("Erreur lors de la création:", err);
       // Provide more specific feedback for auth errors
      const msg = typeof res?.data === "string" ? res.data : JSON.stringify(res?.data);
      alert(`Failed to create ad: ${res?.status}\n${msg}`);
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
        <ProductCategoryButton
          onClick={handleCategoryButtonClick}
          selectedCategory={selectedCategory}
        />
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
          Selected Category: {selectedCategory.label}
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
        description={description}
        designation={title}
        files={picture ? [picture] : []}
      />
    </div>
  );
};

export default NewProduct;