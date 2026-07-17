import React, { useEffect, useState, useCallback } from "react";
import { useAuth } from "../hooks/useAuth";
import { useTasks } from "../hooks/useTasks";
import { useCategories } from "../hooks/useCategories";
import TaskCard from "../components/TaskCard";
import TaskModal from "../components/TaskModal";
import CategoriesModal from "../components/CategoriesModal";
import ShareModal from "../components/ShareModal";

export default function Dashboard() {
  const { user } = useAuth();
  const { categories, fetchCategories, createCategory, deleteCategory } = useCategories();
  const {
    tasks,
    count,
    nextPage,
    prevPage,
    loading: tasksLoading,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    toggleTaskStatus,
    shareTask,
    fetchTaskShares,
    revokeTaskShare,
    getCategorySuggestion,
  } = useTasks();

  // ── States para Filtros ───────────────────────────────────────────────────
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [status, setStatus] = useState("");
  const [dueDateAfter, setDueDateAfter] = useState("");
  const [dueDateBefore, setDueDateBefore] = useState("");

  // ── States para Paginação ─────────────────────────────────────────────────
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // ── States para Modais ────────────────────────────────────────────────────
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [isCategoriesModalOpen, setIsCategoriesModalOpen] = useState(false);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [activeTask, setActiveTask] = useState(null);
  const [taskToDeleteId, setTaskToDeleteId] = useState(null);
  const [customAlert, setCustomAlert] = useState("");

  // ── Fetch de Dados ────────────────────────────────────────────────────────
  const loadData = useCallback(() => {
    const filters = {
      search,
      category: selectedCategory,
      status,
      due_date_after: dueDateAfter,
      due_date_before: dueDateBefore,
    };
    fetchTasks(filters, page, pageSize);
  }, [fetchTasks, search, selectedCategory, status, dueDateAfter, dueDateBefore, page, pageSize]);

  // Carrega as categorias na montagem
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  // Recarrega as tarefas quando filtros ou paginação mudam
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Reseta para a página 1 ao alterar filtros
  const handleFilterChange = (setter) => (e) => {
    setter(e.target.value);
    setPage(1);
  };

  const handleClearFilters = () => {
    setSearch("");
    setSelectedCategory("");
    setStatus("");
    setDueDateAfter("");
    setDueDateBefore("");
    setPage(1);
  };

  // ── Handlers de Ações ─────────────────────────────────────────────────────
  const handleToggleStatus = async (taskId) => {
    try {
      await toggleTaskStatus(taskId);
    } catch (err) {
      setCustomAlert("Erro ao alterar status da tarefa.");
    }
  };

  const handleCreateTaskClick = () => {
    setActiveTask(null);
    setIsTaskModalOpen(true);
  };

  const handleEditTaskClick = (task) => {
    setActiveTask(task);
    setIsTaskModalOpen(true);
  };

  const handleShareTaskClick = (task) => {
    setActiveTask(task);
    setIsShareModalOpen(true);
  };

  const handleSaveTask = async (taskData) => {
    if (activeTask) {
      await updateTask(activeTask.id, taskData);
    } else {
      await createTask(taskData);
    }
    loadData();
  };

  const handleDeleteTaskClick = (taskId) => {
    setTaskToDeleteId(taskId);
  };

  const handleConfirmDeleteTask = async () => {
    if (!taskToDeleteId) return;
    try {
      await deleteTask(taskToDeleteId);
      setTaskToDeleteId(null);
      loadData();
    } catch (err) {
      setCustomAlert("Erro ao excluir tarefa.");
    }
  };

  // ── Paginação Helpers ─────────────────────────────────────────────────────
  const totalPages = Math.ceil(count / pageSize);

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div className="dashboard-title">
          <h2>Bem-vindo, {user?.first_name || user?.username}!</h2>
          <p>Gerencie suas tarefas pessoais e compartilhadas.</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={() => setIsCategoriesModalOpen(true)}>
            🏷️ Categorias
          </button>
          <button className="btn-primary btn-icon" style={{ marginTop: 0 }} onClick={handleCreateTaskClick}>
            + Nova Tarefa
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="filters-card">
        <div className="filters-grid">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Busca</label>
            <input
              type="text"
              className="input-field"
              placeholder="Buscar por título..."
              value={search}
              onChange={handleFilterChange(setSearch)}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Categoria</label>
            <select
              className="input-field"
              value={selectedCategory}
              onChange={handleFilterChange(setSelectedCategory)}
            >
              <option value="">Todas</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Status</label>
            <select
              className="input-field"
              value={status}
              onChange={handleFilterChange(setStatus)}
            >
              <option value="">Todos</option>
              <option value="pending">Pendentes</option>
              <option value="completed">Concluídas</option>
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Vencimento De</label>
            <input
              type="date"
              className="input-field"
              value={dueDateAfter}
              onChange={handleFilterChange(setDueDateAfter)}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Vencimento Até</label>
            <input
              type="date"
              className="input-field"
              value={dueDateBefore}
              onChange={handleFilterChange(setDueDateBefore)}
            />
          </div>
        </div>

        {(search || selectedCategory || status || dueDateAfter || dueDateBefore) && (
          <button
            className="btn-secondary"
            onClick={handleClearFilters}
            style={{ marginTop: "1.25rem", width: "100%", padding: "0.6rem" }}
          >
            Limpar Filtros
          </button>
        )}
      </div>

      {/* Listagem de Tarefas */}
      {tasksLoading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
          <div className="spinner"></div>
        </div>
      ) : (
        <>
          <div className="tasks-grid">
            {tasks.length === 0 ? (
              <div className="empty-state">
                <h3>Nenhuma tarefa encontrada</h3>
                <p style={{ marginTop: "0.5rem" }}>Crie uma nova tarefa ou ajuste os filtros.</p>
              </div>
            ) : (
              tasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  currentUser={user}
                  onToggleStatus={handleToggleStatus}
                  onEdit={handleEditTaskClick}
                  onShare={handleShareTaskClick}
                  onDelete={handleDeleteTaskClick}
                />
              ))
            )}
          </div>

          {/* Paginação */}
          {count > 0 && (
            <div className="pagination-controls">
              <div className="page-size-selector">
                Exibir
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
                tarefas por página
              </div>

              <div className="pagination-info">
                Mostrando página {page} de {totalPages || 1} ({count} total)
              </div>

              <div className="pagination-buttons">
                <button
                  className="btn-secondary"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!prevPage}
                >
                  Anterior
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={!nextPage}
                >
                  Próximo
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Modais */}
      <TaskModal
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
        task={activeTask}
        categories={categories}
        onSave={handleSaveTask}
        getSuggestion={getCategorySuggestion}
        onCreateCategory={createCategory}
      />

      <CategoriesModal
        isOpen={isCategoriesModalOpen}
        onClose={() => setIsCategoriesModalOpen(false)}
        categories={categories}
        onCreate={createCategory}
        onDelete={deleteCategory}
      />

      <ShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        task={activeTask}
        onShare={shareTask}
        onListShares={fetchTaskShares}
        onRevokeShare={revokeTaskShare}
      />
      {/* Custom Alert Modal */}
      {customAlert && (
        <div className="modal-overlay" style={{ zIndex: 1100 }}>
          <div className="modal-content" style={{ maxWidth: "400px" }}>
            <div className="modal-header">
              <h3>Aviso</h3>
              <button className="btn-close" onClick={() => setCustomAlert("")}>
                &times;
              </button>
            </div>
            <div className="modal-body" style={{ margin: "1.5rem 0", color: "var(--text-primary)" }}>
              <p>{customAlert}</p>
            </div>
            <div className="modal-footer" style={{ display: "flex", justifyContent: "flex-end" }}>
              <button className="btn-primary" onClick={() => setCustomAlert("")}>
                Ok
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Custom Task Delete Confirm Modal */}
      {taskToDeleteId && (
        <div className="modal-overlay" style={{ zIndex: 1100 }}>
          <div className="modal-content" style={{ maxWidth: "420px" }}>
            <div className="modal-header">
              <h3>Excluir Tarefa</h3>
              <button className="btn-close" onClick={() => setTaskToDeleteId(null)}>
                &times;
              </button>
            </div>
            <div className="modal-body" style={{ margin: "1.5rem 0", color: "var(--text-primary)" }}>
              <p>Deseja realmente excluir esta tarefa permanentemente?</p>
            </div>
            <div className="modal-footer" style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
              <button className="btn-secondary" onClick={() => setTaskToDeleteId(null)}>
                Cancelar
              </button>
              <button className="btn-primary danger" onClick={handleConfirmDeleteTask}>
                Excluir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
