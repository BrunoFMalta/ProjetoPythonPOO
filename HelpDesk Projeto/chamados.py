"""Chamados de suporte e o histórico de interações."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from calendario import CalendarioComercial
from enums import Impacto, Nivel, Prioridade, Status, TipoInteracao, Urgencia
from usuarios import Cliente, Tecnico, Usuario


class Interacao:
    """Um registro no histórico do chamado (comentário, mudança de status, etc.)."""

    def __init__(self, autor: Usuario, texto: str, tipo: TipoInteracao,
                 data: datetime | None = None) -> None:
        self.autor = autor
        self.texto = texto
        self.tipo = tipo
        self.data = data or datetime.now()

    def __str__(self) -> str:
        return f"[{self.data:%d/%m %H:%M}] {self.tipo.value} - {self.autor.nome}: {self.texto}"


class Chamado(ABC):
    """Chamado de suporte (classe abstrata). Guarda as regras de negócio principais."""

    # Transições de status permitidas (atributo privado da classe)
    __TRANSICOES = {
        Status.ABERTO: {Status.EM_ATENDIMENTO},
        Status.EM_ATENDIMENTO: {Status.PENDENTE, Status.SOLUCIONADO},
        Status.PENDENTE: {Status.EM_ATENDIMENTO},
        Status.SOLUCIONADO: {Status.FECHADO, Status.EM_ATENDIMENTO},
        Status.FECHADO: set(),
    }

    def __init__(self, titulo: str, descricao: str, solicitante: Cliente,
                 urgencia: Urgencia, impacto: Impacto,
                 data_abertura: datetime | None = None) -> None:
        self.id: int | None = None
        self.titulo = titulo
        self.descricao = descricao
        self.solicitante = solicitante
        self.urgencia = urgencia
        self.impacto = impacto
        self.data_abertura = data_abertura or datetime.now()
        self.data_resolucao: datetime | None = None
        self.tecnico: Tecnico | None = None
        self._historico: list[Interacao] = []
        self.__status = Status.ABERTO          # privado: só muda via métodos
        self.__nivel_atual = Nivel.N1          # privado: só muda via escalar()
        self.__prioridade = self.__calcular_prioridade()

    # ----- leitura dos atributos privados -----
    @property
    def status(self) -> Status:
        return self.__status

    @property
    def nivel_atual(self) -> Nivel:
        return self.__nivel_atual

    @property
    def prioridade(self) -> Prioridade:
        return self.__prioridade

    @property
    def historico(self) -> list[Interacao]:
        return list(self._historico)

    # ----- regras privadas -----
    def __calcular_prioridade(self) -> Prioridade:
        """Prioridade = urgência x impacto (soma dos pesos 1 a 3)."""
        pontos = self.urgencia.value + self.impacto.value
        if pontos >= 6:
            return Prioridade.CRITICA
        if pontos == 5:
            return Prioridade.ALTA
        if pontos == 4:
            return Prioridade.MEDIA
        return Prioridade.BAIXA

    def __transicao_valida(self, novo: Status) -> bool:
        return novo in self.__TRANSICOES[self.__status]

    # ----- operações públicas -----
    def registrar_interacao(self, autor: Usuario, texto: str, tipo: TipoInteracao) -> None:
        self._historico.append(Interacao(autor, texto, tipo))

    def mudar_status(self, novo: Status, autor: Usuario) -> None:
        """Muda o status se a transição for permitida; senão levanta ValueError."""
        if not self.__transicao_valida(novo):
            raise ValueError(f"Transição inválida: {self.__status.value} -> {novo.value}.")
        anterior = self.__status
        self.__status = novo
        if novo == Status.SOLUCIONADO:
            self.data_resolucao = datetime.now()
        elif anterior == Status.SOLUCIONADO:
            self.data_resolucao = None  # chamado reaberto
        self.registrar_interacao(autor, f"{anterior.value} -> {novo.value}",
                                 TipoInteracao.MUDANCA_STATUS)

    def atribuir(self, tecnico: Tecnico) -> None:
        """Atribui o chamado a um técnico que tenha nível suficiente."""
        if self.__status != Status.ABERTO:
            raise ValueError("Só é possível atribuir chamados com status Aberto.")
        if not tecnico.pode_atender(self):
            raise ValueError(f"{tecnico.nome} ({tecnico.nivel.name}) não pode atender "
                             f"chamado de nível {self.__nivel_atual.name}.")
        self.tecnico = tecnico
        tecnico._receber(self)
        self.registrar_interacao(tecnico, f"Chamado atribuído a {tecnico.nome}.",
                                 TipoInteracao.ATRIBUICAO)
        self.mudar_status(Status.EM_ATENDIMENTO, tecnico)

    def escalar(self, autor: Tecnico, motivo: str) -> None:
        """N1 não resolveu: o chamado sobe para N2 e volta para a fila sem técnico."""
        if self.__status != Status.EM_ATENDIMENTO:
            raise ValueError("Só é possível escalar um chamado em atendimento.")
        if autor is not self.tecnico:
            raise ValueError("Só o técnico responsável pode escalar o chamado.")
        if autor.nivel != Nivel.N1 or self.__nivel_atual == Nivel.N2:
            raise ValueError("Só técnicos N1 escalam, e apenas chamados de nível N1.")
        autor._liberar(self)
        self.tecnico = None
        self.__nivel_atual = Nivel.N2
        self.__status = Status.ABERTO  # volta para a fila (do N2); não passa pela tabela de transições
        self.registrar_interacao(autor, f"Escalado para N2. Motivo: {motivo}",
                                 TipoInteracao.ESCALONAMENTO)

    @abstractmethod
    def calcular_prazo(self, cal: CalendarioComercial) -> datetime:
        """Prazo de atendimento do chamado (cada tipo calcula do seu jeito)."""

    def sla_estourado(self, agora: datetime, cal: CalendarioComercial) -> bool:
        """True se o prazo já passou (ou se foi resolvido depois dele)."""
        fim = self.data_resolucao or agora
        return fim > self.calcular_prazo(cal)


class Incidente(Chamado):
    """Algo que quebrou. O prazo depende da prioridade."""

    HORAS_SLA = {
        Prioridade.CRITICA: 4,
        Prioridade.ALTA: 8,
        Prioridade.MEDIA: 16,
        Prioridade.BAIXA: 24,
    }

    def __init__(self, titulo: str, descricao: str, solicitante: Cliente,
                 urgencia: Urgencia, impacto: Impacto, servico_afetado: str,
                 data_abertura: datetime | None = None) -> None:
        super().__init__(titulo, descricao, solicitante, urgencia, impacto, data_abertura)
        self.servico_afetado = servico_afetado

    def calcular_prazo(self, cal: CalendarioComercial) -> datetime:
        return cal.somar_horas_uteis(self.data_abertura, self.HORAS_SLA[self.prioridade])


class Requisicao(Chamado):
    """Pedido de algo novo. O prazo é fixo (5 dias úteis), independe da prioridade."""

    HORAS_PRAZO = 40

    def __init__(self, titulo: str, descricao: str, solicitante: Cliente,
                 urgencia: Urgencia, impacto: Impacto, item_solicitado: str,
                 data_abertura: datetime | None = None) -> None:
        super().__init__(titulo, descricao, solicitante, urgencia, impacto, data_abertura)
        self.item_solicitado = item_solicitado

    def calcular_prazo(self, cal: CalendarioComercial) -> datetime:
        return cal.somar_horas_uteis(self.data_abertura, self.HORAS_PRAZO)
