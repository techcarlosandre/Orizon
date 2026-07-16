import { useState, useCallback } from "react";
import client from "../api/client";

export function useCategories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      // Como a listagem é paginada globalmente pelo DRF, pegamos de data.results
      const { data } = await client.get("/categories/");
      setCategories(data.results || data);
    } catch (err) {
      console.error(err);
      setError("Falha ao carregar categorias.");
    } finally {
      setLoading(false);
    }
  }, []);

  const createCategory = async (name) => {
    setError("");
    try {
      const { data } = await client.post("/categories/", { name });
      setCategories((prev) => [...prev, data]);
      return data;
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.name?.[0] || "Erro ao criar categoria.";
      setError(msg);
      throw new Error(msg);
    }
  };

  const deleteCategory = async (id) => {
    setError("");
    try {
      await client.delete(`/categories/${id}/`);
      setCategories((prev) => prev.filter((cat) => cat.id !== id));
    } catch (err) {
      console.error(err);
      setError("Erro ao excluir categoria.");
      throw err;
    }
  };

  return {
    categories,
    loading,
    error,
    fetchCategories,
    createCategory,
    deleteCategory,
  };
}
