import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== passwordConfirm) {
      setError("As senhas não conferem.");
      return;
    }

    setLoading(true);

    try {
      await register(username, email, password, passwordConfirm, firstName, lastName);
      navigate("/");
    } catch (err) {
      console.error(err);
      const data = err.response?.data;
      if (data) {
        // Tenta extrair mensagens granulares de erro retornadas pelo Django/DRF
        if (typeof data === "object") {
          const firstKey = Object.keys(data)[0];
          const firstError = data[firstKey];
          setError(
            Array.isArray(firstError) ? firstError[0] : JSON.stringify(firstError)
          );
        } else {
          setError(data.detail || "Erro ao realizar cadastro.");
        }
      } else {
        setError("Erro ao realizar cadastro. Tente novamente mais tarde.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-header">
          <h1>🚀 Criar Conta</h1>
          <p>Cadastre-se na plataforma Orizon</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username *</label>
            <input
              id="username"
              type="text"
              className="input-field"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="Username único"
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">E-mail *</label>
            <input
              id="email"
              type="email"
              className="input-field"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="seu-email@exemplo.com"
              autoComplete="email"
            />
          </div>

          <div style={{ display: "flex", gap: "1rem" }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="firstName">Nome</label>
              <input
                id="firstName"
                type="text"
                className="input-field"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Nome"
                autoComplete="given-name"
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="lastName">Sobrenome</label>
              <input
                id="lastName"
                type="text"
                className="input-field"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Sobrenome"
                autoComplete="family-name"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Senha *</label>
            <input
              id="password"
              type="password"
              className="input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Mínimo 8 caracteres"
              autoComplete="new-password"
            />
          </div>

          <div className="form-group">
            <label htmlFor="passwordConfirm">Confirmar Senha *</label>
            <input
              id="passwordConfirm"
              type="password"
              className="input-field"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              required
              placeholder="Repita sua senha"
              autoComplete="new-password"
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Cadastrando..." : "Cadastrar"}
          </button>
        </form>

        <div className="auth-footer">
          Já tem uma conta? <Link to="/login">Entre aqui</Link>
        </div>
      </div>
    </div>
  );
}
