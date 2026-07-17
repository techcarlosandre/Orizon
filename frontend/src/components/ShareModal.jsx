import React, { useState, useEffect, useCallback } from "react";

export default function ShareModal({
  isOpen,
  onClose,
  task,
  onShare,
  onListShares,
  onRevokeShare,
}) {
  const [usernameOrEmail, setUsernameOrEmail] = useState("");
  const [permission, setPermission] = useState("view");
  const [shares, setShares] = useState([]);
  
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [showRevokeConfirmId, setShowRevokeConfirmId] = useState(null);

  // Carrega a lista de compartilhamentos ativos ao abrir
  const loadShares = useCallback(async () => {
    if (!task) return;
    setFetchLoading(true);
    try {
      const data = await onListShares(task.id);
      setShares(data);
    } catch (err) {
      console.error(err);
    } finally {
      setFetchLoading(false);
    }
  }, [task, onListShares]);

  useEffect(() => {
    if (isOpen && task) {
      loadShares();
      setUsernameOrEmail("");
      setPermission("view");
      setError("");
    }
  }, [isOpen, task, loadShares]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!usernameOrEmail.trim()) return;

    setLoading(true);
    try {
      await onShare(task.id, usernameOrEmail.trim(), permission);
      setUsernameOrEmail("");
      loadShares(); // Recarrega lista
    } catch (err) {
      setError(err.message || "Erro ao compartilhar.");
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = (shareId) => {
    setError("");
    setShowRevokeConfirmId(shareId);
  };

  const handleConfirmRevoke = async () => {
    if (!showRevokeConfirmId) return;
    setLoading(true);
    try {
      await onRevokeShare(task.id, showRevokeConfirmId);
      setShowRevokeConfirmId(null);
      loadShares(); // Recarrega lista
    } catch (err) {
      setError("Erro ao revogar compartilhamento.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Compartilhar Tarefa</h3>
          <button className="btn-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: "1rem" }}>
          Tarefa: <strong>{task?.title}</strong>
        </p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="share-username">Usuário (Username ou E-mail)</label>
            <input
              id="share-username"
              type="text"
              className="input-field"
              value={usernameOrEmail}
              onChange={(e) => setUsernameOrEmail(e.target.value)}
              required
              placeholder="Digite o username ou e-mail"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="share-permission">Nível de Permissão</label>
            <select
              id="share-permission"
              className="input-field"
              value={permission}
              onChange={(e) => setPermission(e.target.value)}
              disabled={loading}
            >
              <option value="view">Visualizar (Leitura / Conclusão)</option>
              <option value="edit">Editar (Escrita completa)</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ marginTop: "0.5rem" }}
          >
            {loading ? "Compartilhando..." : "Compartilhar"}
          </button>
        </form>

        <h4 style={{ fontSize: "0.95rem", fontWeight: "600", marginTop: "2rem", marginBottom: "0.75rem" }}>
          Usuários com Acesso
        </h4>

        {fetchLoading ? (
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>Carregando...</p>
        ) : shares.length === 0 ? (
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            Esta tarefa ainda não foi compartilhada.
          </p>
        ) : (
          <div className="share-list">
            {shares.map((share) => (
              <div key={share.id} className="share-item">
                <div className="share-user-info">
                  <span style={{ fontSize: "0.95rem", fontWeight: "500" }}>
                    {share.shared_with.username}
                  </span>
                  <span className="share-user-email">{share.shared_with.email}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <span className="share-badge">{share.permission}</span>
                  <button
                    className="btn-action-icon danger"
                    onClick={() => handleRevoke(share.id)}
                    title="Revogar Acesso"
                  >
                    &times;
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Fechar
          </button>
        </div>
      </div>
      {showRevokeConfirmId && (
        <div className="modal-overlay" style={{ zIndex: 1100 }}>
          <div className="modal-content" style={{ maxWidth: "420px" }}>
            <div className="modal-header">
              <h3>Revogar Compartilhamento</h3>
              <button 
                type="button" 
                className="btn-close" 
                onClick={() => setShowRevokeConfirmId(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body" style={{ margin: "1.5rem 0", color: "var(--text-primary)" }}>
              <p>Deseja revogar o acesso deste usuário?</p>
            </div>
            <div className="modal-footer" style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowRevokeConfirmId(null)}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="btn-primary danger"
                onClick={handleConfirmRevoke}
              >
                Revogar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
