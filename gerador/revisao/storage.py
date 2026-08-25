# -*- coding: utf-8 -*-
"""
Camada de Persistência e Repositório de Revisão Técnica — Demo Store
Salva e recupera o estado de produtos, blocos, lotes e histórico.
"""
import os
import json
from typing import List, Dict, Any, Optional
from .models import Product, ProductStatus
from .parser import MarkdownProductParser

REVISAO_DB_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "produtos_revisao"))

class ReviewStorage:
    def __init__(self, storage_dir: str = REVISAO_DB_DIR):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_path(self, product_id: str) -> str:
        return os.path.join(self.storage_dir, f"{product_id}.json")

    def save_product(self, product: Product) -> str:
        path = self._get_path(product.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(product.to_dict(), f, ensure_ascii=False, indent=2)
        return path

    def get_product(self, product_id: str) -> Optional[Product]:
        path = self._get_path(product_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Product.from_dict(data)
        except Exception as e:
            print(f"[!] Erro ao carregar produto {product_id}: {e}")
            return None

    def list_products(self) -> List[Product]:
        products = []
        if not os.path.exists(self.storage_dir):
            return products
        for fname in os.listdir(self.storage_dir):
            if fname.endswith(".json"):
                pid = fname[:-5]
                prod = self.get_product(pid)
                if prod:
                    products.append(prod)
        return sorted(products, key=lambda p: p.nome)

    def delete_product(self, product_id: str) -> bool:
        path = self._get_path(product_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def import_markdown_file(self, filepath: str, lote: str = "Lote 001") -> Product:
        product = MarkdownProductParser.parse_file(filepath, lote=lote)
        self.save_product(product)
        return product

    def import_lote_directory(self, dir_path: str, lote_name: str = "Lote Importado") -> Dict[str, Any]:
        results = {
            "total": 0,
            "sucesso": 0,
            "erros": 0,
            "produtos": [],
            "erros_detalhes": []
        }
        if not os.path.exists(dir_path):
            results["erros_detalhes"].append(f"Diretório {dir_path} não encontrado.")
            return results

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".md"):
                    results["total"] += 1
                    full_path = os.path.join(root, file)
                    try:
                        p = self.import_markdown_file(full_path, lote=lote_name)
                        results["sucesso"] += 1
                        results["produtos"].append(p.nome)
                    except Exception as e:
                        results["erros"] += 1
                        results["erros_detalhes"].append(f"Erro em {file}: {str(e)}")
        return results

    def obter_estatisticas(self) -> Dict[str, Any]:
        prods = self.list_products()
        lotes = set(p.lote for p in prods if p.lote)
        return {
            "total_produtos": len(prods),
            "pendentes": sum(1 for p in prods if p.status in (ProductStatus.IMPORTADO.value, ProductStatus.EM_REVISAO.value)),
            "aprovados": sum(1 for p in prods if p.status == ProductStatus.APROVADO.value),
            "publicados": sum(1 for p in prods if p.status == ProductStatus.PUBLICADO.value),
            "lotes": list(lotes)
        }
