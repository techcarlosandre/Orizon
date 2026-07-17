import React, { useState } from "react";

export default function CategoriesModal({ isOpen, onClose, categories, onCreate, onDelete }) {
  const [newCatName, setNewCatName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showDeleteConfirmId, setShowDeleteConfirmId] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!newCatName.trim()) return;

    setLoading(true);
    try {
      await onCreate(newCatName.trim());
      setNewCatName("");
    } catch (err) {
      setError(err.message || "Erro ao criar categoria.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (id) => {
    setError("");
    setShowDeleteConfirmId(id);
  };

  const handleConfirmDelete = async () => {
    if (!showDeleteConfirmId) return;
    setLoading(true);
    try {
      await onDelete(showDeleteConfirmId);
      setShowDeleteConfirmId(null);
    } catch (err) {
      setError("Erro ao excluir categoria.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Categorias</h3>
          <button className="btn-close" onClick={onClose}>
            &times;
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem" }}>
          <input
            type="text"
            className="input-field"
            placeholder="Nova categoria"
            value={newCatName}
            onChange={(e) => setNewCatName(e.target.value)}
            disabled={loading}
            maxLength={50}
          />
          <button type="submit" className="btn-primary" style={{ width: "auto", marginTop: 0 }} disabled={loading}>
            +
          </button>
        </form>

        <div className="category-list">
          {categories.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center", marginTop: "1rem" }}>
              Nenhuma categoria criada.
            </p>
          ) : (
            categories.map((cat) => (
              <div key={cat.id} className="category-item">
                <span>{cat.name}</span>
                <button
                  className="btn-action-icon danger"
                  onClick={() => handleDelete(cat.id)}
                  title="Excluir Categoria"
                >
                  &times;
                </button>
              </div>
            ))
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Fechar
          </button>
        </div>
      </div>
      {showDeleteConfirmId && (
        <div className="modal-overlay" style={{ zIndex: 1100 }}>
          <div className="modal-content" style={{ maxWidth: "420px" }}>
            <div className="modal-header">
              <h3>Excluir Categoria</h3>
              <button 
                type="button" 
                className="btn-close" 
                onClick={() => setShowDeleteConfirmId(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body" style={{ margin: "1.5rem 0", color: "var(--text-primary)" }}>
              <p>
                Deseja realmente excluir esta categoria? As tarefas vinculadas a ela não serão excluídas, mas ficarão sem categoria.
              </p>
            </div>
            <div className="modal-footer" style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowDeleteConfirmId(null)}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="btn-primary danger"
                onClick={handleConfirmDelete}
              >
                Excluir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
