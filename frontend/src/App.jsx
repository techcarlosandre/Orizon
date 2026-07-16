import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth";
import PrivateRoute from "./routes/PrivateRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";

// Placeholder Dashboard para compilação na Fase 7.
// A implementação final do Dashboard será feita na Fase 8.
function DashboardPlaceholder() {
  return (
    <div style={{ textAlign: "center", marginTop: "4rem" }}>
      <h2>🚀 Dashboard Orizon</h2>
      <p style={{ color: "var(--text-secondary)", marginTop: "1rem" }}>
        Auth Setup concluído. Dashboard completo será implementado na Fase 8.
      </p>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Rotas Públicas */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Rotas Privadas (Protegidas) */}
          <Route element={<PrivateRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<DashboardPlaceholder />} />
              <Route path="/tasks" element={<Navigate to="/" replace />} />
            </Route>
          </Route>

          {/* Fallback - Redireciona tudo desconhecido para o Dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
