"""Enumerações usadas pelo sistema."""
from enum import Enum


class Status(Enum):
    ABERTO = "Aberto"
    EM_ATENDIMENTO = "Em atendimento"
    PENDENTE = "Pendente"
    SOLUCIONADO = "Solucionado"
    FECHADO = "Fechado"


class Urgencia(Enum):
    BAIXA = 1
    MEDIA = 2
    ALTA = 3


class Impacto(Enum):
    BAIXO = 1
    MEDIO = 2
    ALTO = 3


class Prioridade(Enum):
    BAIXA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4


class Nivel(Enum):
    N1 = 1  # atendimento por telefone, problemas simples
    N2 = 2  # atendimento presencial, problemas complexos


class TipoInteracao(Enum):
    COMENTARIO = "Comentário"
    MUDANCA_STATUS = "Mudança de status"
    ATRIBUICAO = "Atribuição"
    ESCALONAMENTO = "Escalonamento"
    SOLUCAO = "Solução"
