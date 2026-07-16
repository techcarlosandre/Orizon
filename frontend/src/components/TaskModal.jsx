import React, { useState, useEffect, useRef } from "react";

export default function TaskModal({
  isOpen,
  onClose,
  task,
  categories,
  onSave,
  getSuggestion,
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [status, setStatus] = useState("pending");

  const [suggestedCategoryName, setSuggestedCategoryName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const debounceTimeout = useRef(null);

  // Carrega dados da tarefa se estiver editando
  useEffect(() => {
    if (task) {
      setTitle(task.title || "");
      setDescription(task.description || "");
      setCategoryId(task.category?.id || "");
      setDueDate(task.due_date || "");
      setStatus(task.status || "pending");
    } else {
      // Limpa os campos se for criação
      setTitle("");
      setDescription("");
      setCategoryId("");
      setDueDate("");
      setStatus("pending");
    }
    setSuggestedCategoryName("");
    setError("");
  }, [task, isOpen]);

  // Efeito para buscar sugestão de categoria em tempo real (debounce de 600ms)
  useEffect(() => {
    if (task) return; // Não sugere categoria na edição de tarefa já existente
    if (!title.trim()) {
      setSuggestedCategoryName("");
      return;
    }

    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }

    debounceTimeout.current = setTimeout(async () => {
      try {
        const suggestion = await getSuggestion(title);
        if (suggestion && suggestion !== "Geral") {
          setSuggestedCategoryName(suggestion);
        } else {
          setSuggestedCategoryName("");
        }
      } catch (err) {
        console.error("Erro ao obter sugestão:", err);
      }
    }, 600);

    return () => {
      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }
    };
  }, [title, task, getSuggestion]);

  if (!isOpen) return null;

  const handleApplySuggestion = () => {
    // Procura se o usuário já possui uma categoria com o nome sugerido
    const matchedCategory = categories.find(
      (cat) => cat.name.toLowerCase() === suggestedCategoryName.toLowerCase()
    );

    if (matchedCategory) {
      setCategoryId(matchedCategory.id);
      setSuggestedCategoryName("");
    } else {
      alert(
        `Para usar a sugestão, crie a categoria "${suggestedCategoryName}" primeiro no menu de Categorias.`
      );
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!title.trim()) return;

    setLoading(true);
    try {
      const payload = {
        title: title.trim(),
        description: description.trim(),
        category_id: categoryId || null,
        due_date: dueDate || null,
        status,
      };
      await onSave(payload);
      onClose();
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || "Erro ao salvar tarefa. Verifique os campos."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>{task ? "Editar Tarefa" : "Nova Tarefa"}</h3>
          <button className="btn-close" onClick={onClose}>
            &times;
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="task-title">Título *</label>
            <input
              id="task-title"
              type="text"
              className="input-field"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="Digite o título da tarefa"
              maxLength={255}
            />
          </div>

          {/* Sugestão em tempo real */}
          {suggestedCategoryName && (
            <div className="suggestion-banner">
              <span>Sugestão de categoria: <strong>{suggestedCategoryName}</strong></span>
              <button type="button" onClick={handleApplySuggestion}>
                Aplicar
              </button>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="task-description">Descrição</label>
            <textarea
              id="task-description"
              className="input-field"
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descreva a tarefa..."
              style={{ resize: "vertical" }}
            />
          </div>

          <div className="form-group">
            <label htmlFor="task-category">Categoria</label>
            <select
              id="task-category"
              className="input-field"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
            >
              <option value="">Sem categoria</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="task-due-date">Data de Vencimento</label>
            <input
              id="task-due-date"
              type="date"
              className="input-field"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>

          {task && (
            <div className="form-group">
              <label htmlFor="task-status">Status</label>
              <select
                id="task-status"
                className="input-field"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="pending">Pendente</option>
                <option value="completed">Concluída</option>
              </select>
            </div>
          )}

          <div className="modal-footer" style={{ marginTop: "1.5rem" }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-primary"
              style={{ width: "auto", marginTop: 0 }}
              disabled={loading}
            >
              {loading ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
