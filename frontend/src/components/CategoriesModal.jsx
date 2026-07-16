import React, { useState } from "react";

export default function CategoriesModal({ isOpen, onClose, categories, onCreate, onDelete }) {
  const [newCatName, setNewCatName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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

  const handleDelete = async (id) => {
    if (window.confirm("Deseja realmente excluir esta categoria? As tarefas vinculadas a ela não serão excluídas, mas ficarão sem categoria.")) {
      try {
        await onDelete(id);
      } catch (err) {
        alert("Erro ao excluir categoria.");
      }
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
    </div>
  );
}
