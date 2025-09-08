const API_URL = 'http://localhost:4000/api/internal/mongodb/entity/ad'

export const handleValidateAll = async ({ title, description, picture }) => {
  // Convert image file to base64
  const toBase64 = file =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });

  let imageBase64 = '';
  if (picture) {
    imageBase64 = await toBase64(picture);
  }

  const productData = {
    designation: title,
    description: description,
    image: imageBase64
    // Add other fields if needed
  };

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
        // Add authentication headers if your gateway requires them
      },
      body: JSON.stringify(productData)
    });

    if (!response.ok) {
      throw new Error('Failed to save product');
    }

    const data = await response.json();
    console.log('Product saved via gateway:', data);
    return data;
  } catch (error) {
    console.error(error);
    throw error;
  }
};