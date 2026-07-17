import React from "react";

export default function TaskCard({
  task,
  currentUser,
  onToggleStatus,
  onEdit,
  onShare,
  onDelete,
}) {
  const isOwner = task.owner_username === currentUser?.username;
  const isShared = task.is_shared_with_me;

  // Encontra a permissão deste usuário se for compartilhado
  const userShare = task.shares?.find(
    (s) => s.shared_with?.username === currentUser?.username
  );
  
  // Usuário pode editar se for dono OR se for compartilhado com permissão EDIT
  const canEdit = isOwner || userShare?.permission === "edit";

  // Formata data amigável
  const formatDueDate = (dateStr) => {
    if (!dateStr) return "";
    const [year, month, day] = dateStr.split("-");
    return `${day}/${month}/${year}`;
  };

  const handleToggle = (e) => {
    e.stopPropagation();
    onToggleStatus(task.id);
  };

  const handleEdit = (e) => {
    e.stopPropagation();
    onEdit(task);
  };

  const handleShare = (e) => {
    e.stopPropagation();
    onShare(task);
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    onDelete(task.id);
  };

  return (
    <div className="task-card">
      <div>
        <div className="task-card-header">
          <span className={`task-title ${task.status === "completed" ? "completed" : ""}`}>
            {task.title}
          </span>
          <span
            className={`status-indicator ${
              task.status === "completed" ? "completed" : "pending"
            }`}
            title={task.status === "completed" ? "Concluída" : "Pendente"}
          />
        </div>

        <p className="task-description">{task.description || "Sem descrição."}</p>

        <div className="task-meta">
          {task.category && (
            <span className="badge badge-category">{task.category.name}</span>
          )}
          {task.due_date && (
            <span className="badge badge-date">📅 {formatDueDate(task.due_date)}</span>
          )}
          {isShared && (
            <span className="badge badge-shared" title={`Dono: ${task.owner_username}`}>
              👥 Compartilhada ({userShare?.permission === "edit" ? "edita" : "vê"})
            </span>
          )}
        </div>
      </div>

      <div className="task-actions">
        <div className="action-left">
          {/* Toggle de Status - Disponível para owner e qualquer shared */}
          <button
            onClick={handleToggle}
            className="btn-action-icon"
            title={task.status === "completed" ? "Marcar como pendente" : "Marcar como concluída"}
          >
            {task.status === "completed" ? "↩" : "✓"}
          </button>
          
          {/* Editar - Apenas owner ou shared-edit */}
          {canEdit && (
            <button
              onClick={handleEdit}
              className="btn-action-icon"
              title="Editar Tarefa"
            >
              ✏️
            </button>
          )}
        </div>

        <div className="action-right">
          {/* Compartilhar - Apenas Owner */}
          {isOwner && (
            <button
              onClick={handleShare}
              className="btn-action-icon"
              title="Compartilhar"
            >
              👥
            </button>
          )}

          {/* Excluir - Apenas Owner */}
          {isOwner && (
            <button
              onClick={handleDelete}
              className="btn-action-icon danger"
              title="Excluir permanentemente"
            >
              🗑️
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
