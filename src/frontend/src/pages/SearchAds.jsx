// src/pages/SearchAds.jsx
import React, { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import { Form, Table, Image, Button, Spinner, Alert, Pagination } from "react-bootstrap";
import axiosInstance from "../services/axiosInstance";

const PAGE_SIZE = 10;

export default function SearchAds() {
  const [q, setQ] = useState("");
  const [selectedCat, setSelectedCat] = useState(null);   // {code,label} ou null
  const [categories, setCategories] = useState([]);       // [{code,label}]
  const [page, setPage] = useState(1);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [pageSize, setPageSize] = useState(PAGE_SIZE);
  const [thumbs, setThumbs] = useState({});
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState("");
  const history = useHistory();

  // --- utils ---
  const normalizeCategories = (data) => {
    if (!data) return [];
    if (Array.isArray(data)) {
      if (data.length && typeof data[0] === "string") {
        return data.map((s) => ({ code: s, label: s }));
      }
      return data.map((c) => {
        const code = c.code ?? c.id ?? c.value ?? c.key ?? c.slug ?? c.label ?? c.name ?? "";
        const label = c.label ?? c.name ?? c.title ?? String(code ?? "").toUpperCase();
        return { code, label };
      });
    }
    if (Array.isArray(data.data)) return normalizeCategories(data.data);
    return [];
  };
  
  const normalizeSearch = (data, page, pageSize) => {
    if (!data || typeof data !== "object") {
      return { items: [], count: 0, page, page_size: pageSize, has_more: false };
    }
    const items = data.items ?? data.results ?? data.data ?? [];
    const count = data.count ?? data.total ?? (Array.isArray(items) ? items.length : 0);
    const currentPage = Number(data.page ?? (data.offset != null
      ? Math.floor((Number(data.offset) || 0) / (Number(data.limit) || pageSize)) + 1
      : page));
    const currentSize = Number(data.page_size ?? data.limit ?? pageSize) || pageSize;
    // 1) has_more: on privilégie la valeur de l'API si elle existe, sinon on dérive
    const apiHasMore = typeof data.has_more === "boolean" ? data.has_more : undefined;
    const derivedHasMore = (Number(count) > 0)
      ? (currentPage * currentSize) < Number(count)
      : (Array.isArray(items) && items.length === currentSize);
    const has_more = (apiHasMore ?? derivedHasMore);

    // 2) total "effectif" : si count est 0/absent mais qu'on pense qu'il y a une page suivante,
    //    on force un total minimal pour débloquer la pagination (au moins page+1).
    const effectiveCount =
      Number(count) > 0
        ? Number(count)
        : (has_more
            ? (currentPage * currentSize + 1)
            : ((currentPage - 1) * currentSize + (Array.isArray(items) ? items.length : 0)));
    return {
      items: Array.isArray(items) ? items : [],
      count: effectiveCount,
      page: Number(currentPage) || page,
      page_size: Number(currentSize) || pageSize,
      has_more,
    };
  };
  
  // --- catégories ---
  useEffect(() => {
    let mounted = true;
    axiosInstance.get(`/api/protected/get_categories`)
      .then(({ data }) => {
        const norm = normalizeCategories(data);
        if (mounted) setCategories(norm);
        // console.debug("[cats] raw:", data, "normalized:", norm);
      })
      .catch((e) => {
        // console.warn("[cats] error:", e?.response?.status, e?.response?.data || e.message);
      });
    return () => { mounted = false; };
  }, []);

  const debouncedQ = useDebounce(q, 300);

  // --- recherche ---
  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError("");

    const categoryParam = selectedCat?.label ?? selectedCat?.code ?? undefined;
    const params = {
      q: debouncedQ || undefined,
      category: categoryParam,
      category_code: selectedCat?.code ?? undefined,
      page,
      page_size: PAGE_SIZE,
    };

    axiosInstance.get(`/api/protected/search_ads`, { params })
      .then(({ data }) => {
        console.debug("[search_ads][raw]", JSON.stringify(data));
        const norm = normalizeSearch(data, page, PAGE_SIZE);
        if (!mounted) return;
        setItems(norm.items);
        setHasMore(norm.has_more);
        setTotal(norm.count);
        setPageSize(norm.page_size);
        setThumbs({});
        // console.debug("[search] params:", params, "raw:", data, "normalized:", norm);
      })
      .catch((err) => {
        if (!mounted) return;
        const detail = err.response?.data?.detail || err.message;
        setError(`Erreur lors de la recherche: ${detail}`);
        // console.error("[search] error:", err?.response?.status, err?.config?.url, err?.response?.data || err.message);
      })
      .finally(() => mounted && setLoading(false));

    return () => { mounted = false; };
  }, [debouncedQ, selectedCat, page]);

  // thumbnails (inchangé, déclenche après items)
  useEffect(() => {
    const fetchThumbs = async () => {
      for (const ad of items) {
        const first = ad.images?.[0]?.image_uuid;
        if (first && !thumbs[ad.id]) {
          try {
            const { data } = await axiosInstance.get(`/api/protected/image/${first}`);
            const dataUrl = `data:${data.content_type || "image/jpeg"};base64,${data.content}`;
            setThumbs((t) => ({ ...t, [ad.id]: dataUrl }));
          } catch {}
        }
      }
    };
    if (items.length) fetchThumbs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  const onRowClick = (id) => history.push(`/ads/${id}`);

  return (
    <div>
      <h1>Recherche d'annonces</h1>

      <Form className="d-flex gap-2 my-3" onSubmit={(e) => e.preventDefault()}>
        <Form.Control
          placeholder="Texte (designation, description)"
          value={q}
          onChange={(e) => { setPage(1); setQ(e.target.value); }}
        />
        <Form.Select
          value={selectedCat?.code ?? ""}
          onChange={(e) => {
            const code = e.target.value;
            const found = categories.find(c => String(c.code) === String(code));
            setPage(1);
            setSelectedCat(found || null);
          }}
          style={{ maxWidth: 280 }}
        >
          <option value="">Toutes catégories</option>
          {categories.map(c => (
            <option key={String(c.code)} value={String(c.code)}>{c.label}</option>
          ))}
        </Form.Select>
        <Button variant="secondary" onClick={() => { setQ(""); setSelectedCat(null); setPage(1); }}>
          Réinitialiser
        </Button>
      </Form>

      {error && <Alert variant="danger">{error}</Alert>}
      {loading && <Spinner animation="border" />}

      {!loading && !items.length && <div>Aucun résultat.</div>}

      {!!items.length && (
        <>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>Image</th>
                <th>Désignation</th>
                <th>Catégorie</th>
                <th>Description</th>
                <th>Créée le</th>
              </tr>
            </thead>
            <tbody>
              {items.map((ad) => (
                <tr key={ad.id} style={{ cursor: "pointer" }} onClick={() => onRowClick(ad.id)}>
                  <td style={{ width: 80 }}>
                    {thumbs[ad.id] ? (
                      <Image src={thumbs[ad.id]} thumbnail style={{ maxWidth: 70, maxHeight: 70 }} />
                    ) : (
                      <div style={{ width: 70, height: 70, background: "#eee" }} />
                    )}
                  </td>
                  <td>{ad.designation}</td>
                  <td>{ad.category}</td>
                  <td style={{ maxWidth: 320, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {ad.description}
                  </td>
                  <td>{new Date(ad.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </Table>

          {(() => {
            const totalPages = Math.max(1, Math.ceil((total || 0) / (pageSize || PAGE_SIZE)));
            const go = (p) => setPage(p);
            // on affiche: 1 ... (page-1) [page] (page+1) ... total
            const around = [page - 1, page, page + 1].filter(p => p >= 1 && p <= totalPages);
            const unique = (arr) => [...new Set(arr)];
            const pages = unique([1, ...(page > 3 ? ["..."] : []), ...around, ...(page < totalPages - 2 ? ["..."] : []), totalPages]);
            return (
              <Pagination className="mt-3">
                <Pagination.Prev disabled={page === 1} onClick={() => go(Math.max(1, page - 1))} />
                {pages.map((p, idx) =>
                  p === "..." ? (
                    // Ellipsis par défaut est "disabled". On le remplace par un Item cliquable qui avance d'1 page.
                    <Pagination.Item key={`e${idx}`} onClick={() => go(Math.min(totalPages, page + 1))}>
                      +
                    </Pagination.Item>
                  ) : (
                    <Pagination.Item key={p} active={p === page} onClick={() => go(p)}>
                      {p}
                    </Pagination.Item>
                  )
                )}
                {/* Next reste cliquable si l'API dit qu'il y a encore des résultats (hasMore=true) */}
                <Pagination.Next
                  disabled={page >= totalPages && !hasMore}
                  onClick={() => go(page + 1)}
                />
              </Pagination>
            );
          })()}
        </>
      )}
    </div>
  );
}

// Petit hook debounce local
function useDebounce(value, delay = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return v;
}
