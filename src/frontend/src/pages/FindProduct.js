import React, { useState, useEffect } from 'react';
import { Form, Table, Image, Alert } from 'react-bootstrap';
import Papa from 'papaparse';

const CSV_PATH = '/products.csv'; 
const IMAGE_TEMP_PATH = '/tmp/';  

const columns = [
  { key: 'product_name', label: 'Name' },
  { key: 'product_category', label: 'Category' },
  { key: 'product_description', label: 'Description' },
];

const FindProduct = () => {
  const [products, setProducts] = useState([]);
  const [searchCol, setSearchCol] = useState('product_name');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [csvFound, setCsvFound] = useState(true);
  const [imageFolderTested, setImageFolderTested] = useState(false);
  const [imageFound, setImageFound] = useState(false);

  useEffect(() => {
    // Test if CSV exists
    fetch(CSV_PATH)
      .then(res => {
        if (!res.ok) {
          setCsvFound(false);
          return '';
        }
        setCsvFound(true);
        return res.text();
      })
      .then(text => {
        if (text) {
          Papa.parse(text, {
            header: true,
            complete: (result) => {
              setProducts(result.data.slice(0, 10));
              // Test if at least one image exists
              if (result.data.length > 0 && result.data[0].image_id) {
                fetch(`${IMAGE_TEMP_PATH}${result.data[0].image_id}`)
                  .then(imgRes => {
                    setImageFolderTested(true);
                    setImageFound(imgRes.ok);
                  })
                  .catch(() => {
                    setImageFolderTested(true);
                    setImageFound(false);
                  });
              } else {
                setImageFolderTested(true);
                setImageFound(false);
              }
            }
          });
        }
      });
  }, []);

  const filteredProducts = products.filter(prod =>
    prod[searchCol]?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', gap: '2rem' }}>
      <div style={{ flex: 1 }}>
        <h1>Find a Product</h1>
        {!csvFound && (
          <Alert variant="danger">
            CSV file not found at {CSV_PATH}
          </Alert>
        )}
        {imageFolderTested && !imageFound && (
          <Alert variant="warning">
            No image found in {IMAGE_TEMP_PATH} for the first product.
          </Alert>
        )}
        <Form style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
          <Form.Select
            value={searchCol}
            onChange={e => setSearchCol(e.target.value)}
            style={{ maxWidth: '180px' }}
          >
            {columns.map(col => (
              <option key={col.key} value={col.key}>{col.label}</option>
            ))}
          </Form.Select>
          <Form.Control
            type="text"
            placeholder={`Search by ${columns.find(c => c.key === searchCol).label}`}
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </Form>
        <Table striped bordered hover>
          <thead>
            <tr>
              {columns.map(col => <th key={col.key}>{col.label}</th>)}
              <th>Image</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map((prod, idx) => (
              <tr key={idx} style={{ cursor: 'pointer' }} onClick={() => setSelectedProduct(prod)}>
                {columns.map(col => <td key={col.key}>{prod[col.key]}</td>)}
                <td>
                  {prod.image_id ? (
                    <Image
                      src={`${IMAGE_TEMP_PATH}${prod.image_id}`}
                      alt="preview"
                      thumbnail
                      style={{ maxWidth: '60px', maxHeight: '60px' }}
                      onError={e => { e.target.style.display = 'none'; }}
                    />
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
      <div style={{ flex: 1, minWidth: '300px' }}>
        {selectedProduct && (
          <div style={{
            border: '1px solid #e3eafc',
            borderRadius: '8px',
            padding: '1rem',
            background: '#f8f9fa'
          }}>
            <h4>{selectedProduct.product_name}</h4>
            {selectedProduct.image_id && (
              <Image
                src={`${IMAGE_TEMP_PATH}${selectedProduct.image_id}`}
                alt="preview"
                thumbnail
                style={{ maxWidth: '200px', marginBottom: '1rem' }}
                onError={e => { e.target.style.display = 'none'; }}
              />
            )}
            <div><strong>Category:</strong> {selectedProduct.product_category}</div>
            <div><strong>Description:</strong> {selectedProduct.product_description}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FindProduct;