# -*- coding: utf-8 -*-
"""
Módulo de Autenticação — usuários de demonstração.
Em produção, substitua este arquivo por autenticação real (OAuth, JWT, etc.).
"""

import hashlib

# Usuários de demonstração — altere senhas e adicione/remova usuários conforme necessário
USERS = {
    "admin": {
        "id": 1,
        "nome": "Administrador",
        "login": "admin",
        "senha_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin"
    },
    "editor": {
        "id": 2,
        "nome": "Editor",
        "login": "editor",
        "senha_hash": hashlib.sha256("editor123".encode()).hexdigest(),
        "role": "supervisor"
    },
    "viewer": {
        "id": 3,
        "nome": "Visualizador",
        "login": "viewer",
        "senha_hash": hashlib.sha256("viewer123".encode()).hexdigest(),
        "role": "viewer"
    },
}


def authenticate(login, senha):
    """Autentica um usuário pelo login e senha. Retorna os dados do usuário ou None."""
    login = login.strip().lower()
    if login not in USERS:
        return None

    user = USERS[login]
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    if user["senha_hash"] == senha_hash:
        return {
            "id": user["id"],
            "nome": user["nome"],
            "login": user["login"],
            "role": user["role"]
        }
    return None


def get_user_by_id(user_id):
    for u in USERS.values():
        if u["id"] == user_id:
            return {
                "id": u["id"],
                "nome": u["nome"],
                "login": u["login"],
                "role": u["role"]
            }
    return None


def can_approve(role):
    return role in ["supervisor", "admin"]
