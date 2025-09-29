import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Badge, Image, Spinner, Alert, Button } from "react-bootstrap";
import axiosInstance from "../services/axiosInstance";

export default function AdDetails() {
  const { id } = useParams();
  const [ad, setAd] = useState(null);
  const [imgs, setImgs] = useState([]); // dataURLs
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        // Endpoint Gateway: GET /api/protected/mongodb/ad/{id}
        const { data } = await axiosInstance.get(`/api/protected/ad/${id}`);
        if (!mounted) return;
        setAd(data);

        // Récupération des images (si présentes)
        const imageUUIDs = (data.images || []).map((im) => im.image_uuid);
        const results = await Promise.allSettled(
          imageUUIDs.map((uuid) => axiosInstance.get(`/api/protected/image/${uuid}`))
        );
        const urls = results
          .filter((r) => r.status === "fulfilled")
          .map((r) => {
            const payload = r.value.data;
            return `data:${payload.content_type || "image/jpeg"};base64,${payload.content}`;
          });
        if (mounted) setImgs(urls);
      } catch (e) {
        const detail = e.response?.data?.detail || e.message;
        if (mounted) setError(`Erreur: ${detail}`);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => { mounted = false; };
  }, [id]);

  if (loading) return <Spinner animation="border" />;
  if (error) return <Alert variant="danger">{error}</Alert>;
  if (!ad) return <div>Annonce introuvable.</div>;

  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-2">
        <Link to="/search">← Retour à la recherche</Link>
        <Button as={Link} to={`/search`} variant="outline-secondary" size="sm">
          Revenir à la liste
        </Button>
      </div>

      <h2 className="mt-2">
        {ad.designation}{" "}
        <Badge bg="secondary">{ad.category}</Badge>
      </h2>
      <div style={{ color: "#666" }}>
        Publiée le {new Date(ad.created_at).toLocaleString()} — par {ad.user?.username}
      </div>

      <p className="mt-3" style={{ whiteSpace: "pre-wrap" }}>{ad.description}</p>

      <div className="d-flex flex-wrap gap-3">
        {imgs.map((src, i) => (
          <Image key={i} src={src} thumbnail style={{ maxWidth: 300, maxHeight: 300 }} />
        ))}
      </div>
    </div>
  );
}
