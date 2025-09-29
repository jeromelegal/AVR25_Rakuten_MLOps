// ProductCategoryModal.js
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Spinner, Alert } from 'react-bootstrap';
import ValidateButton from './ValidateButton';
import axiosInstance from '../services/axiosInstance';

/**
 * Props:
 * - show: boolean
 * - onHide: () => void
 * - onSelect: (cat: { code: number|string, label: string } | null) => void
 * - initialCategory?: { code: number|string, label: string } | null
 * - enablePrediction?: boolean
 */
const ProductCategoryModal = ({ show, onHide, onSelect, initialCategory = null, enablePrediction = false }) => {
  const [changingCategory, setChangingCategory] = useState(false);

  // Catégories depuis la gateway
  const [categories, setCategories] = useState([]); // [{code, label}]
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [errorCategories, setErrorCategories] = useState('');

  // Sélection (on stocke le "code")
  const [selectedCode, setSelectedCode] = useState(initialCategory?.code ?? '');

  // Prédiction (optionnelle)
  const [categoryProposal, setCategoryProposal] = useState(initialCategory?.label ?? null);
  const [predictLoading, setPredictLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  // 1) Charger la liste des catégories quand la modale s’ouvre
  useEffect(() => {
    if (!show) return;
    let mounted = true;
    setLoadingCategories(true);
    setErrorCategories('');

    // Endpoint Gateway protégé
    axiosInstance.get('/api/protected/get_categories')
      .then(({ data }) => { if (mounted) setCategories(Array.isArray(data) ? data : []); })
      .catch((e) => {
        const detail = e?.response?.data?.detail || e.message;
        if (mounted) setErrorCategories(detail);
      })
      .finally(() => { if (mounted) setLoadingCategories(false); });

    return () => { mounted = false; };
  }, [show]);

  // 2) (Optionnel) Lancer la prédiction quand la modale s’ouvre si activé
  useEffect(() => {
    if (show && enablePrediction) {
      handlePredict();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show, enablePrediction]);

  // Appel API de prédiction (optionnel)
  const handlePredict = async () => {
    setPredictLoading(true);
    setElapsed(0);
    setCategoryProposal(null);

    const start = Date.now();
    try {
      // On tente d’abord l’endpoint protégé (aligné Gateway).
      const res = await axiosInstance.get('/api/protected/predict-category');
      const data = res.data;
      setCategoryProposal(data?.category || 'Indéterminée');
    } catch (err1) {
      try {
        // Fallback : ancienne route non protégée si tu ne l’as pas encore migrée.
        const res2 = await axiosInstance.get('/api/predict-category');
        const data2 = res2.data;
        setCategoryProposal(data2?.category || 'Indéterminée');
      } catch (err2) {
        setCategoryProposal('⚠️ Erreur de prédiction');
      }
    } finally {
      const end = Date.now();
      setElapsed(((end - start) / 1000).toFixed(1));
      setPredictLoading(false);
    }
  };

  // 3) Validation : renvoie l’objet {code,label}
  const handleValidate = () => {
    let finalCategory = null;

    if (changingCategory && selectedCode) {
      const found = categories.find(c => String(c.code) === String(selectedCode));
      if (found) finalCategory = { code: found.code, label: found.label };
    } else {
      if (categoryProposal) {
        const found = categories.find(c => c.label === categoryProposal);
        finalCategory = found ? { code: found.code, label: found.label } : { code: '', label: categoryProposal };
      } else if (initialCategory) {
        finalCategory = initialCategory;
      }
    }

    onSelect(finalCategory);
    setChangingCategory(false);
  };

  const handleChangeCategoryClick = () => setChangingCategory(true);

  const bodyBg = changingCategory ? '#f8d7da' : '#f8f9fa';

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header>
        <Modal.Title>Catégorie</Modal.Title>
        <Button
          variant="link"
          onClick={onHide}
          style={{
            fontSize: '1.5rem',
            lineHeight: '1',
            color: '#000',
            textDecoration: 'none',
            position: 'absolute',
            top: '10px',
            right: '15px'
          }}
        >
          ×
        </Button>
      </Modal.Header>

      <Modal.Body>
        {/* Bloc proposition / état courant */}
        <div 
          style={{
            padding: '1rem',
            background: bodyBg,
            borderRadius: '8px',
            marginBottom: '1.5rem',
            textAlign: 'center',
            fontSize: '1.1rem',
            fontWeight: 500,
            opacity: changingCategory ? 0.75 : 1
          }}
        >
          <div>Proposition de catégorie :</div>
          <div
            style={{
              marginTop: '0.5rem',
              padding: '0.5rem 1rem',
              background: '#e3eafc',
              borderRadius: '6px',
              display: 'inline-block',
              minWidth: '150px',
            }}
          >
            {enablePrediction ? (
              predictLoading ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Spinner animation="border" size="sm" />
                  <span>Prédiction…</span>
                </span>
              ) : (
                categoryProposal || '—'
              )
            ) : (
              initialCategory?.label || categoryProposal || '—'
            )}
          </div>

          {!predictLoading && enablePrediction && elapsed > 0 && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#555' }}>
              Temps de réponse : {elapsed}s
            </div>
          )}

          {changingCategory && (
            <div style={{ color: '#a94442', marginTop: '0.5rem', fontSize: '0.95rem' }}>
              Cette valeur ne sera pas prise en compte : sélectionne une nouvelle catégorie ci-dessous.
            </div>
          )}

          {enablePrediction && (
            <div style={{ marginTop: '1rem' }}>
              <Button variant="outline-primary" size="sm" onClick={handlePredict}>
                🔄 Relancer la prédiction
              </Button>
            </div>
          )}
        </div>

        {/* Zone de chargement/erreur des catégories */}
        {loadingCategories && (
          <div className="d-flex align-items-center gap-2 mb-2">
            <Spinner animation="border" size="sm" />
            <span>Chargement des catégories…</span>
          </div>
        )}
        {errorCategories && <Alert variant="danger">Erreur catégories : {errorCategories}</Alert>}

        {/* Sélecteur manuel */}
        {changingCategory && !loadingCategories && !errorCategories && (
          <Form.Group controlId="selectCategory" style={{ marginBottom: '1.5rem' }}>
            <Form.Label>Choisir une catégorie</Form.Label>
            <Form.Select
              value={selectedCode}
              onChange={(e) => setSelectedCode(e.target.value)}
            >
              <option value="">— Sélectionne une catégorie —</option>
              {categories.map((cat) => (
                <option key={cat.code} value={cat.code}>
                  {cat.label}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          {!changingCategory && (
            <Button
              style={{ backgroundColor: '#ffe5b4', color: '#333', border: 'none' }}
              onClick={handleChangeCategoryClick}
              disabled={loadingCategories || !!errorCategories}
            >
              Changer de catégorie
            </Button>
          )}
          <ValidateButton
            onClick={handleValidate}
            disabled={changingCategory && !selectedCode}
          >
            Valider
          </ValidateButton>
        </div>
      </Modal.Body>
    </Modal>
  );
};

export default ProductCategoryModal;
