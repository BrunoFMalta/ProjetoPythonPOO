"""Usuários do sistema: clientes (quem abre chamados) e técnicos (quem atende)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from enums import Nivel, Status

if TYPE_CHECKING:
    from chamados import Chamado


class Usuario(ABC):
    """Classe base abstrata de qualquer pessoa cadastrada no sistema."""

    def __init__(self, nome: str, email: str) -> None:
        self.id: int | None = None
        self.nome = nome
        self.email = email

    @abstractmethod
    def descricao(self) -> str:
        """Texto curto para exibir o usuário em listas (polimórfico)."""


class Cliente(Usuario):
    """Quem abre chamados."""

    def __init__(self, nome: str, email: str, setor: str) -> None:
        super().__init__(nome, email)
        self.setor = setor

    def descricao(self) -> str:
        return f"{self.nome} ({self.setor})"


class Tecnico(Usuario):
    """Quem atende chamados. O nível (N1/N2) limita o que ele pode atender."""

    def __init__(self, nome: str, email: str, nivel: Nivel) -> None:
        super().__init__(nome, email)
        self.nivel = nivel
        self._chamados: list[Chamado] = []

    def descricao(self) -> str:
        return f"{self.nome} (Técnico {self.nivel.name})"

    @property
    def chamados(self) -> list[Chamado]:
        return list(self._chamados)

    def pode_atender(self, chamado: Chamado) -> bool:
        """N2 atende qualquer chamado; N1 só os de nível N1."""
        return self.nivel.value >= chamado.nivel_atual.value

    def carga_atual(self) -> int:
        """Chamados que ainda estão em andamento com este técnico."""
        return sum(1 for c in self._chamados
                   if c.status not in (Status.SOLUCIONADO, Status.FECHADO))

    def _receber(self, chamado: Chamado) -> None:
        """Uso restrito: chamado.atribuir() é o único ponto de entrada."""
        if chamado not in self._chamados:
            self._chamados.append(chamado)

    def _liberar(self, chamado: Chamado) -> None:
        """Uso restrito: chamado.escalar() remove o chamado do técnico."""
        if chamado in self._chamados:
            self._chamados.remove(chamado)
