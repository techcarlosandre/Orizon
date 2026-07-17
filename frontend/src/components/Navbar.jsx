import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (err) {
      console.error("Erro ao deslogar:", err);
    }
  };

  // Pega a inicial do usuário para o avatar
  const getInitial = () => {
    if (user?.first_name) return user.first_name[0].toUpperCase();
    if (user?.username) return user.username[0].toUpperCase();
    return "U";
  };

  const getDisplayName = () => {
    if (user?.first_name) {
      return `${user.first_name} ${user.last_name || ""}`.trim();
    }
    return user?.username;
  };

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        📋 Projeto Orizon
      </Link>
      <div className="navbar-menu">
        <div className="user-badge">
          <div className="user-avatar">{getInitial()}</div>
          <span>{getDisplayName()}</span>
        </div>
        <button onClick={handleLogout} className="btn-secondary">
          Sair
        </button>
      </div>
    </nav>
  );
}
