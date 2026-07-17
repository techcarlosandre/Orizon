import { useState, useCallback } from "react";
import client from "../api/client";
import { extractErrorMessage } from "../utils/errors";

export function useTasks() {
  const [tasks, setTasks] = useState([]);
  const [count, setCount] = useState(0);
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchTasks = useCallback(async (filters = {}, page = 1, pageSize = 20) => {
    setLoading(true);
    setError("");
    try {
      const params = {
        page,
        page_size: pageSize,
        ...filters,
      };
      
      // Remove parâmetros vazios para manter a URL limpa
      Object.keys(params).forEach((key) => {
        if (params[key] === "" || params[key] === null || params[key] === undefined) {
          delete params[key];
        }
      });

      const { data } = await client.get("/tasks/", { params });
      setTasks(data.results);
      setCount(data.count);
      setNextPage(data.next);
      setPrevPage(data.previous);
    } catch (err) {
      console.error(err);
      setError("Falha ao carregar tarefas.");
    } finally {
      setLoading(false);
    }
  }, []);

  const createTask = async (taskData) => {
    setError("");
    try {
      const { data } = await client.post("/tasks/", taskData);
      setTasks((prev) => [data, ...prev]);
      return data;
    } catch (err) {
      console.error(err);
      throw err;
    }
  };

  const updateTask = async (id, taskData) => {
    setError("");
    try {
      const { data } = await client.put(`/tasks/${id}/`, taskData);
      setTasks((prev) => prev.map((t) => (t.id === id ? data : t)));
      return data;
    } catch (err) {
      console.error(err);
      throw err;
    }
  };

  const deleteTask = async (id) => {
    setError("");
    try {
      await client.delete(`/tasks/${id}/`);
      setTasks((prev) => prev.filter((t) => t.id !== id));
      setCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error(err);
      throw err;
    }
  };

  const toggleTaskStatus = async (id) => {
    setError("");
    try {
      const { data } = await client.patch(`/tasks/${id}/toggle_status/`);
      setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, status: data.status } : t)));
      return data;
    } catch (err) {
      console.error(err);
      throw err;
    }
  };

  // ── Sharing actions ────────────────────────────────────────────────────────

  const shareTask = async (id, usernameOrEmail, permission = "view") => {
    setError("");
    try {
      const payload = {};
      if (usernameOrEmail.includes("@")) {
        payload.email = usernameOrEmail;
      } else {
        payload.username = usernameOrEmail;
      }
      payload.permission = permission;

      const { data } = await client.post(`/tasks/${id}/share/`, payload);
      return data;
    } catch (err) {
      console.error(err);
      const msg = extractErrorMessage(err, "Erro ao compartilhar tarefa.");
      throw new Error(msg);
    }
  };

  const fetchTaskShares = async (id) => {
    try {
      const { data } = await client.get(`/tasks/${id}/shares/`);
      return data;
    } catch (err) {
      console.error(err);
      throw err;
    }
  };

  const revokeTaskShare = async (taskId, shareId) => {
    try {
      await client.delete(`/tasks/${taskId}/shares/${shareId}/`);
    } catch (err) {
      console.error(err);
      throw err;
    }
  };

  // ── Suggestions client-side integration ────────────────────────────────────

  const getCategorySuggestion = async (title) => {
    try {
      const { data } = await client.post("/suggestions/category/", { title });
      return data.suggested_category;
    } catch (err) {
      console.error("Falha ao buscar sugestão de categoria:", err);
      return "Geral";
    }
  };

  return {
    tasks,
    count,
    nextPage,
    prevPage,
    loading,
    error,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    toggleTaskStatus,
    shareTask,
    fetchTaskShares,
    revokeTaskShare,
    getCategorySuggestion,
  };
}
