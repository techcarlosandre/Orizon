"""
Category suggestion service.

Algorithm: keyword matching against a curated category→keywords map.
Scoring: each keyword match in the title adds 1 point to that category.
Winner: highest score. Tie-break: first in insertion order.
Fallback: "Geral" when score is 0.

Design: pure Python (no I/O), making this trivially unit-testable
and importable by both the HTTP view and any future caller.

To extend: add keywords to CATEGORY_KEYWORDS or new categories.
The algorithm is O(K) where K = total number of keywords across all categories.
"""
from __future__ import annotations

# ── Keyword map ────────────────────────────────────────────────────────────────
# Keys are the suggested category names (returned to the client).
# Values are lists of Portuguese/English keywords matched case-insensitively.
# ORDER MATTERS: in case of a tie, the first category wins.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Trabalho": [
        "reunião", "meeting", "relatório", "prazo", "deadline", "projeto",
        "apresentação", "cliente", "contrato", "proposta", "sprint", "backlog",
        "tarefa", "entrega", "release", "deploy", "revisão", "review",
        "email", "e-mail", "ligação", "call",
    ],
    "Saúde": [
        "academia", "médico", "consulta", "exercício", "remédio", "dieta",
        "nutricionista", "treino", "corrida", "caminhada", "fisioterapia",
        "exame", "laboratorio", "vacina", "dentista", "psicólogo",
    ],
    "Estudos": [
        "estudar", "prova", "faculdade", "curso", "aula", "leitura",
        "livro", "pesquisa", "tcc", "monografia", "certificação", "treinamento",
        "workshop", "webinar", "artigo",
    ],
    "Finanças": [
        "pagar", "conta", "banco", "investimento", "imposto", "boleto",
        "cartão", "fatura", "orçamento", "dívida", "empréstimo", "transferência",
        "poupança", "ações", "criptomoeda",
    ],
    "Casa": [
        "limpar", "organizar", "compras", "supermercado", "manutenção",
        "conserto", "faxina", "cozinhar", "aluguel", "condomínio", "reforma",
        "jardim", "quintal",
    ],
    "Lazer": [
        "viagem", "cinema", "restaurante", "festa", "show", "passeio",
        "amigos", "férias", "jogo", "série", "filme", "leitura recreativa",
        "trilha", "praia", "camping",
    ],
    "Família": [
        "filho", "filha", "pai", "mãe", "aniversário", "escola",
        "pediatra", "cônjuge", "casamento", "família", "criança",
    ],
}

FALLBACK_CATEGORY = "Geral"


def suggest_category(title: str) -> str:
    """
    Return the best-matching category name for the given task title.

    Args:
        title: The task title to analyze.

    Returns:
        A category name string (e.g., "Trabalho", "Saúde") or "Geral" if
        no keyword matches are found.
    """
    if not title or not title.strip():
        return FALLBACK_CATEGORY

    title_lower = title.lower()
    scores: dict[str, int] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in title_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return FALLBACK_CATEGORY

    return max(scores, key=lambda cat: scores[cat])
