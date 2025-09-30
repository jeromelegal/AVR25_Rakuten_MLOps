// ProductCategoryModal.js (fusion des comportements de (1) et (2))
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
 * - description?: string
 * - designation?: string
 * - files?: File[]   // images éventuelles
 */
const ProductCategoryModal = ({
  show,
  onHide,
  onSelect,
  initialCategory = null,
  enablePrediction = true,
  description,
  designation,
  files = [],
}) => {
  const [changingCategory, setChangingCategory] = useState(false);

  // Catégories depuis la gateway
  const [categories, setCategories] = useState([]); // [{code, label}]
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [errorCategories, setErrorCategories] = useState('');

  // Sélection (stocke le "code")
  const [selectedCode, setSelectedCode] = useState(initialCategory?.code ?? '');

  // Prédiction
  const [categoryProposal, setCategoryProposal] = useState(initialCategory?.label ?? null); // string label
  const [predictLoading, setPredictLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  // Charger la liste des catégories quand la modale s’ouvre
  useEffect(() => {
    if (!show) return;
    let mounted = true;

    setLoadingCategories(true);
    setErrorCategories('');
    axiosInstance
      .get('/api/protected/get_categories')
      .then(({ data }) => {
        if (!mounted) return;
        const arr = Array.isArray(data) ? data : [];
        setCategories(arr);
        // Si on avait une proposition texte, tenter de la “résoudre” vers {code,label}
        if (arr.length && categoryProposal && !changingCategory) {
          const found = findByLabel(arr, categoryProposal);
          if (found) setSelectedCode(found.code);
        }
      })
      .catch((e) => {
        if (!mounted) return;
        const detail = e?.response?.data?.detail || e.message || 'Erreur de chargement';
        setErrorCategories(detail);
      })
      .finally(() => {
        if (mounted) setLoadingCategories(false);
      });

    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show]);

  // Lancer la prédiction automatiquement quand la modale s’ouvre
  useEffect(() => {
    if (show && enablePrediction) {
      handlePredict();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show, enablePrediction]);

  // Helpers de matching label
  const norm = (s) => (s || '').toString().trim().toLowerCase();
  const findByLabel = (arr, label) => arr.find(c => norm(c.label) === norm(label));

  // Prédiction via le même endpoint que (2)
  const handlePredict = async () => {
    setPredictLoading(true);
    setElapsed(0);
    // ne pas écraser une sélection manuelle en cours
    const hadManualChange = changingCategory;

    const start = Date.now();
    try {
      const formData = new FormData();
      if (description) formData.append('description', description);
      if (designation) formData.append('designation', designation);
      if (files?.length) files.forEach((f) => formData.append('files', f));

      // axiosInstance gère déjà l’auth (interceptors). Ne PAS fixer Content-Type manuellement.
      const res = await axiosInstance.post('/api/protected/api-processing/predict', formData);
      if (res.status !== 200) throw new Error(`Erreur API: ${res.status}`);

      // attendu: { category: <string>, probability, overall_probabilities, ... }
      const predictedLabel = res?.data?.category || 'Indéterminée';
      setCategoryProposal(predictedLabel);

      // Tenter de résoudre vers une catégorie {code,label}
      if (categories.length && !hadManualChange) {
        const resolved = findByLabel(categories, predictedLabel);
        if (resolved) setSelectedCode(resolved.code);
      }
    } catch (err) {
      console.error(err);
      setCategoryProposal('⚠️ Erreur de prédiction');
    } finally {
      const end = Date.now();
      setElapsed(((end - start) / 1000).toFixed(1));
      setPredictLoading(false);
    }
  };

  // Validation : renvoie toujours {code,label} (ou null)
  const handleValidate = () => {
    let finalCat = null;

    if (changingCategory) {
      // Sélection manuelle obligatoire
      if (selectedCode) {
        const found = categories.find(c => String(c.code) === String(selectedCode));
        if (found) finalCat = { code: found.code, label: found.label };
      }
    } else {
      // Sinon, on priorise la résolution de la proposition de prédiction
      if (categoryProposal) {
        const found = findByLabel(categories, categoryProposal);
        // Si pas trouvé, on passe un “label libre” avec code vide pour que le backend réagisse proprement
        finalCat = found ? { code: found.code, label: found.label } : { code: '', label: categoryProposal };
      } else if (initialCategory) {
        finalCat = initialCategory;
      }
    }

    onSelect(finalCat);
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
