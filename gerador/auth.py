# -*- coding: utf-8 -*-
"""
Módulo de Autenticação e Usuários
"""

import hashlib

USERS = {
    "fernando": {
        "id": 1,
        "nome": "Fernando",
        "login": "fernando",
        "senha_hash": hashlib.sha256("DemoStore123".encode()).hexdigest(),
        "role": "supervisor"
    },
    "leomar": {
        "id": 2,
        "nome": "Leomar",
        "login": "leomar",
        "senha_hash": hashlib.sha256("DemoStore123".encode()).hexdigest(),
        "role": "supervisor"
    },
    "andrea": {
        "id": 3,
        "nome": "Andrea",
        "login": "andrea",
        "senha_hash": hashlib.sha256("DemoStore123".encode()).hexdigest(),
        "role": "supervisor"
    },
    "daniel": {
        "id": 4,
        "nome": "Daniel",
        "login": "daniel",
        "senha_hash": hashlib.sha256("DemoStore123".encode()).hexdigest(),
        "role": "supervisor"
    },
    "lucas": {
        "id": 5,
        "nome": "Lucas",
        "login": "lucas",
        "senha_hash": hashlib.sha256("DemoStore123".encode()).hexdigest(),
        "role": "admin"
    },
    "valmir": {
        "id": 6,
        "nome": "Valmir",
        "login": "valmir",
        "senha_hash": hashlib.sha256("DemoStore123".encode()).hexdigest(),
        "role": "supervisor"
    }
}

def authenticate(login, senha):
    login = login.strip().lower()
    if login not in USERS:
        return None
    
    user = USERS[login]
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    if user["senha_hash"] == senha_hash:
        # Retorna uma cópia sem a senha
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
