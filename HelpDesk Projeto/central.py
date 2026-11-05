"""Coordenação do sistema: guarda chamados e usuários e gera relatórios."""
from __future__ import annotations

from datetime import datetime

from calendario import CalendarioComercial
from chamados import Chamado
from enums import Nivel, Status, TipoInteracao
from usuarios import Cliente, Tecnico, Usuario


class Central:
    """Ponto único de acesso aos dados (em memória)."""

    def __init__(self, calendario: CalendarioComercial) -> None:
        self.calendario = calendario
        self._chamados: list[Chamado] = []
        self._usuarios: list[Usuario] = []

    def __proximo_id(self, colecao: list) -> int:
        return len(colecao) + 1

    @property
    def chamados(self) -> list[Chamado]:
        return list(self._chamados)

    def clientes(self) -> list[Cliente]:
        return [u for u in self._usuarios if isinstance(u, Cliente)]

    def tecnicos(self) -> list[Tecnico]:
        return [u for u in self._usuarios if isinstance(u, Tecnico)]

    def cadastrar_usuario(self, usuario: Usuario) -> None:
        usuario.id = self.__proximo_id(self._usuarios)
        self._usuarios.append(usuario)

    def abrir_chamado(self, chamado: Chamado) -> None:
        chamado.id = self.__proximo_id(self._chamados)
        self._chamados.append(chamado)
        chamado.registrar_interacao(chamado.solicitante, "Chamado aberto.",
                                    TipoInteracao.COMENTARIO)

    def atribuir(self, chamado: Chamado, tecnico: Tecnico) -> None:
        chamado.atribuir(tecnico)

    def buscar(self, status: Status | None = None, tecnico: Tecnico | None = None,
               nivel: Nivel | None = None) -> list[Chamado]:
        resultado = self._chamados
        if status is not None:
            resultado = [c for c in resultado if c.status == status]
        if tecnico is not None:
            resultado = [c for c in resultado if c.tecnico is tecnico]
        if nivel is not None:
            resultado = [c for c in resultado if c.nivel_atual == nivel]
        return list(resultado)

    def chamados_do_tecnico(self, tecnico: Tecnico) -> list[Chamado]:
        return tecnico.chamados


class Relatorio:
    """Relatórios gerenciais sobre os chamados da Central."""

    def __init__(self, central: Central) -> None:
        self.central = central

    def sla_estourados(self, agora: datetime | None = None) -> list[Chamado]:
        agora = agora or datetime.now()
        return [c for c in self.central.chamados
                if c.sla_estourado(agora, self.central.calendario)]

    def carga_por_tecnico(self) -> dict[str, int]:
        return {t.nome: t.carga_atual() for t in self.central.tecnicos()}

    def tempo_medio_resolucao(self) -> float:
        """Média, em horas úteis, entre abertura e resolução dos chamados resolvidos."""
        resolvidos = [c for c in self.central.chamados if c.data_resolucao]
        if not resolvidos:
            return 0.0
        horas = [self.central.calendario.horas_uteis_entre(c.data_abertura, c.data_resolucao)
                 for c in resolvidos]
        return sum(horas) / len(horas)
