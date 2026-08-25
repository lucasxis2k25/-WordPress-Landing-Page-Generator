# -*- coding: utf-8 -*-
"""
Modelos de Dados do Sistema de Revisão Técnica por Blocos — Demo Store
"""
import uuid
import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

class BlockStatus(str, Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    EDITADO = "EDITADO"
    EXCLUIDO = "EXCLUÍDO"
    REVISAO = "REVISÃO"

class ProductStatus(str, Enum):
    IMPORTADO = "IMPORTADO"
    EM_REVISAO = "EM REVISÃO"
    APROVADO = "APROVADO"
    PUBLICADO = "PUBLICADO"

class Block:
    def __init__(
        self,
        id: str,
        tipo: str,
        titulo: str,
        conteudo: str,
        status: str = BlockStatus.PENDENTE.value,
        ordem: int = 1,
        original_conteudo: Optional[str] = None,
        edited_conteudo: Optional[str] = None,
        observacao_interna: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.tipo = tipo
        self.titulo = titulo
        self.conteudo = conteudo
        self.original_conteudo = original_conteudo if original_conteudo is not None else conteudo
        self.edited_conteudo = edited_conteudo
        self.status = status
        self.ordem = ordem
        self.observacao_interna = observacao_interna
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "original_conteudo": self.original_conteudo,
            "edited_conteudo": self.edited_conteudo,
            "status": self.status,
            "ordem": self.ordem,
            "observacao_interna": self.observacao_interna,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            tipo=data.get("tipo", "geral"),
            titulo=data.get("titulo", ""),
            conteudo=data.get("conteudo", ""),
            status=data.get("status", BlockStatus.PENDENTE.value),
            ordem=data.get("ordem", 1),
            original_conteudo=data.get("original_conteudo"),
            edited_conteudo=data.get("edited_conteudo"),
            observacao_interna=data.get("observacao_interna", ""),
            metadata=data.get("metadata", {})
        )

    def editar(self, novo_titulo: str, novo_conteudo: str, observacao: str = ""):
        self.titulo = novo_titulo
        self.edited_conteudo = novo_conteudo
        self.conteudo = novo_conteudo
        self.observacao_interna = observacao
        self.status = BlockStatus.EDITADO.value

    def aprovar(self):
        self.status = BlockStatus.APROVADO.value

    def marcar_revisao(self, observacao: str = ""):
        self.status = BlockStatus.REVISAO.value
        if observacao:
            self.observacao_interna = observacao

    def excluir(self):
        self.status = BlockStatus.EXCLUIDO.value

    def restaurar(self):
        self.status = BlockStatus.PENDENTE.value


class Section:
    def __init__(
        self,
        id: str,
        tipo: str,
        titulo: str,
        ordem: int = 1,
        blocks: Optional[List[Block]] = None
    ):
        self.id = id
        self.tipo = tipo
        self.titulo = titulo
        self.ordem = ordem
        self.blocks = blocks or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "ordem": self.ordem,
            "blocks": [b.to_dict() for b in self.blocks]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Section":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            tipo=data.get("tipo", "secao"),
            titulo=data.get("titulo", ""),
            ordem=data.get("ordem", 1),
            blocks=[Block.from_dict(b) for b in data.get("blocks", [])]
        )


class Product:
    def __init__(
        self,
        id: str,
        slug: str,
        nome: str,
        sku: str,
        modelo: str = "",
        categoria: str = "",
        familia: str = "",
        volume_elegivel: str = "",
        clientes_elegiveis: str = "",
        source_file: str = "",
        lote: str = "Lote 001",
        status: str = ProductStatus.IMPORTADO.value,
        version: int = 1,
        sections: Optional[List[Section]] = None,
        deleted_blocks: Optional[List[Block]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        versions: Optional[List[Dict[str, Any]]] = None
    ):
        self.id = id
        self.slug = slug
        self.nome = nome
        self.sku = sku
        self.modelo = modelo or sku
        self.categoria = categoria
        self.familia = familia
        self.volume_elegivel = volume_elegivel
        self.clientes_elegiveis = clientes_elegiveis
        self.source_file = source_file
        self.lote = lote
        self.status = status
        self.version = version
        self.sections = sections or []
        self.deleted_blocks = deleted_blocks or []
        self.history = history or []
        self.versions = versions or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "nome": self.nome,
            "sku": self.sku,
            "modelo": self.modelo,
            "categoria": self.categoria,
            "familia": self.familia,
            "volume_elegivel": self.volume_elegivel,
            "clientes_elegiveis": self.clientes_elegiveis,
            "source_file": self.source_file,
            "lote": self.lote,
            "status": self.status,
            "version": self.version,
            "sections": [s.to_dict() for s in self.sections],
            "deleted_blocks": [b.to_dict() for b in self.deleted_blocks],
            "history": self.history,
            "versions": self.versions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            slug=data.get("slug", ""),
            nome=data.get("nome", ""),
            sku=data.get("sku", ""),
            modelo=data.get("modelo", ""),
            categoria=data.get("categoria", ""),
            familia=data.get("familia", ""),
            volume_elegivel=data.get("volume_elegivel", ""),
            clientes_elegiveis=data.get("clientes_elegiveis", ""),
            source_file=data.get("source_file", ""),
            lote=data.get("lote", "Lote 001"),
            status=data.get("status", ProductStatus.IMPORTADO.value),
            version=data.get("version", 1),
            sections=[Section.from_dict(s) for s in data.get("sections", [])],
            deleted_blocks=[Block.from_dict(b) for b in data.get("deleted_blocks", [])],
            history=data.get("history", []),
            versions=data.get("versions", [])
        )

    def log_acao(self, acao: str, detalhes: str = "", bloco_id: str = ""):
        entry = {
            "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "acao": acao,
            "detalhes": detalhes,
            "bloco_id": bloco_id
        }
        self.history.insert(0, entry)

    def criar_versao(self, descricao: str):
        self.version += 1
        snapshot = {
            "version": self.version,
            "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "descricao": descricao,
            "status": self.status,
            "sections_count": len(self.sections),
            "blocks_count": len(self.obter_todos_blocos())
        }
        self.versions.append(snapshot)
        self.log_acao(f"Nova versão v{self.version}", descricao)

    def obter_todos_blocos(self, incluir_excluidos: bool = False) -> List[Block]:
        blocos = []
        for s in self.sections:
            for b in s.blocks:
                if incluir_excluidos or b.status != BlockStatus.EXCLUIDO.value:
                    blocos.append(b)
        return blocos

    def encontrar_bloco(self, bloco_id: str) -> Optional[Block]:
        for s in self.sections:
            for b in s.blocks:
                if b.id == bloco_id:
                    return b
        for b in self.deleted_blocks:
            if b.id == bloco_id:
                return b
        return None

    def excluir_bloco(self, bloco_id: str) -> bool:
        for s in self.sections:
            for i, b in enumerate(s.blocks):
                if b.id == bloco_id:
                    b.excluir()
                    bloco_removido = s.blocks.pop(i)
                    self.deleted_blocks.append(bloco_removido)
                    self.log_acao("Bloco Excluído", f"Título: {bloco_removido.titulo}", bloco_id)
                    self._atualizar_status_geral()
                    return True
        return False

    def restaurar_bloco(self, bloco_id: str) -> bool:
        for i, b in enumerate(self.deleted_blocks):
            if b.id == bloco_id:
                b.restaurar()
                bloco_restaurado = self.deleted_blocks.pop(i)
                # Tenta devolver para a seção original pelo tipo
                colocou = False
                for s in self.sections:
                    if s.tipo == bloco_restaurado.tipo or bloco_restaurado.id.startswith(s.id):
                        s.blocks.append(bloco_restaurado)
                        colocou = True
                        break
                if not colocou and self.sections:
                    self.sections[-1].blocks.append(bloco_restaurado)
                
                self.log_acao("Bloco Restaurado", f"Título: {bloco_restaurado.titulo}", bloco_id)
                self._atualizar_status_geral()
                return True
        return False

    def aprovar_todos_blocos(self):
        for s in self.sections:
            for b in s.blocks:
                if b.status != BlockStatus.EXCLUIDO.value:
                    b.aprovar()
        self.status = ProductStatus.APROVADO.value
        self.log_acao("Aprovação Total", "Todos os blocos ativos foram aprovados")

    def _atualizar_status_geral(self):
        blocos = self.obter_todos_blocos(incluir_excluidos=False)
        if not blocos:
            return
        if all(b.status == BlockStatus.APROVADO.value for b in blocos):
            self.status = ProductStatus.APROVADO.value
        elif any(b.status in (BlockStatus.EDITADO.value, BlockStatus.REVISAO.value) for b in blocos):
            self.status = ProductStatus.EM_REVISAO.value
        elif self.status == ProductStatus.APROVADO.value:
            self.status = ProductStatus.EM_REVISAO.value

    def metricas_blocos(self) -> Dict[str, int]:
        blocos = self.obter_todos_blocos(incluir_excluidos=False)
        return {
            "total": len(blocos),
            "aprovados": sum(1 for b in blocos if b.status == BlockStatus.APROVADO.value),
            "pendentes": sum(1 for b in blocos if b.status == BlockStatus.PENDENTE.value),
            "editados": sum(1 for b in blocos if b.status == BlockStatus.EDITADO.value),
            "revisao": sum(1 for b in blocos if b.status == BlockStatus.REVISAO.value),
            "excluidos": len(self.deleted_blocks)
        }
