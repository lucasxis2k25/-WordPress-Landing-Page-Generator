# -*- coding: utf-8 -*-
"""
Módulo de Auditoria e Log de Histórico
"""

import json
import os
import datetime

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_DB_PATH = os.path.join(PROJ_DIR, "gerador", "audit_db.json")

def _load_audit_db():
    if os.path.exists(AUDIT_DB_PATH):
        try:
            with open(AUDIT_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_audit_db(db):
    with open(AUDIT_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def log_action(produto_slug, user_id, user_name, action, details=""):
    """
    Registra uma ação no histórico do produto.
    Exemplos de action: "Produto revisado", "Descrição editada", "Aprovou produto", "Enviou para revisão"
    """
    db = _load_audit_db()
    
    if produto_slug not in db:
        db[produto_slug] = []
        
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "details": details
    }
    
    db[produto_slug].append(log_entry)
    _save_audit_db(db)

def get_product_history(produto_slug):
    db = _load_audit_db()
    return db.get(produto_slug, [])
