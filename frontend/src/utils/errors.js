/**
 * Utility to extract clean, localized error messages from Axios / Django REST Framework responses.
 * Resolves JavaScript issues like index-based string truncation (e.g., getting "U" from "Usuário não encontrado").
 */
export function extractErrorMessage(err, fallback = "Ocorreu um erro inesperado.") {
  if (!err) return fallback;

  console.error("API Error context:", err);

  // If it's not a response error (e.g., network timeout)
  if (!err.response) {
    if (err.message && err.message.toLowerCase().includes("timeout")) {
      return "O tempo limite de conexão foi excedido. Tente novamente.";
    }
    if (err.message && err.message.toLowerCase().includes("network")) {
      return "Erro de rede. Verifique sua conexão com a internet.";
    }
    return err.message || fallback;
  }

  const { data, status } = err.response;

  // Handle standard HTTP status codes before checking body
  if (status === 401) {
    return "Sessão expirada ou credenciais inválidas. Por favor, faça login novamente.";
  }
  if (status === 403) {
    return "Você não tem permissão para realizar esta ação.";
  }
  if (status === 404) {
    return "O recurso solicitado não foi encontrado.";
  }
  if (status >= 500) {
    return "Erro interno no servidor da AWS. Tente novamente mais tarde.";
  }

  if (data) {
    // 1. Detail field (common in DRF)
    if (data.detail) {
      return translateMessage(Array.isArray(data.detail) ? data.detail[0] : data.detail);
    }

    // 2. Field-specific validation errors (e.g., {"email": ["message"]} or {"email": "message"})
    if (typeof data === "object") {
      const keys = Object.keys(data);
      if (keys.length > 0) {
        // Find the first field containing errors
        const firstKey = keys[0];
        const val = data[firstKey];

        if (Array.isArray(val) && val.length > 0) {
          return translateMessage(val[0]);
        }
        if (typeof val === "string") {
          return translateMessage(val);
        }
        if (val && typeof val === "object") {
          // Nested object errors
          const nestedKeys = Object.keys(val);
          if (nestedKeys.length > 0) {
            const nestedVal = val[nestedKeys[0]];
            if (Array.isArray(nestedVal) && nestedVal.length > 0) {
              return translateMessage(nestedVal[0]);
            }
            if (typeof nestedVal === "string") {
              return translateMessage(nestedVal);
            }
          }
        }
      }
    }

    // 3. String response body fallback
    if (typeof data === "string" && data.length < 150) {
      return translateMessage(data);
    }
  }

  return fallback;
}

/**
 * Translates common English backend validation errors to friendly Portuguese.
 */
function translateMessage(msg) {
  if (typeof msg !== "string") return String(msg);

  const trimmed = msg.trim();
  const lower = trimmed.toLowerCase();

  // Common authentication / user translations
  if (lower.includes("no active account found with the given credentials")) {
    return "Usuário ou senha incorretos.";
  }
  if (lower.includes("user with this username already exists")) {
    return "Este nome de usuário já está cadastrado.";
  }
  if (lower.includes("user with this email already exists")) {
    return "Este e-mail já está cadastrado.";
  }
  if (lower.includes("this field may not be blank") || lower.includes("this field is required")) {
    return "Este campo é obrigatório.";
  }
  if (lower.includes("password is too short")) {
    return "A senha deve ter pelo menos 8 caracteres.";
  }
  if (lower.includes("password is too common")) {
    return "Esta senha é muito comum. Tente outra mais forte.";
  }
  if (lower.includes("invalid password")) {
    return "A senha fornecida é inválida.";
  }
  if (lower.includes("token is invalid or expired")) {
    return "Sessão inválida ou expirada. Faça login novamente.";
  }

  return trimmed;
}
