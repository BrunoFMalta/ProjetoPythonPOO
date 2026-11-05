"""Testes das regras principais (rodar com: pytest)."""
from datetime import datetime

import pytest

from calendario import CalendarioComercial
from central import Central, Relatorio
from chamados import Incidente, Requisicao
from enums import Impacto, Nivel, Prioridade, Status, TipoInteracao, Urgencia
from usuarios import Cliente, Tecnico


@pytest.fixture
def cenario():
    central = Central(CalendarioComercial())
    cliente = Cliente("Maria", "maria@x.com", "Financeiro")
    n1 = Tecnico("Carlos", "carlos@x.com", Nivel.N1)
    n2 = Tecnico("Ana", "ana@x.com", Nivel.N2)
    for usuario in (cliente, n1, n2):
        central.cadastrar_usuario(usuario)
    return central, cliente, n1, n2


def novo_incidente(cliente, urgencia=Urgencia.MEDIA, impacto=Impacto.MEDIO, abertura=None):
    return Incidente("Sem rede", "Cabo sem conexão", cliente, urgencia, impacto,
                     "Rede", abertura)


def test_prioridade_calculada_por_urgencia_e_impacto(cenario):
    _, cliente, _, _ = cenario
    assert novo_incidente(cliente, Urgencia.ALTA, Impacto.ALTO).prioridade == Prioridade.CRITICA
    assert novo_incidente(cliente, Urgencia.BAIXA, Impacto.BAIXO).prioridade == Prioridade.BAIXA


def test_transicao_invalida_e_barrada(cenario):
    _, cliente, _, _ = cenario
    chamado = novo_incidente(cliente)
    with pytest.raises(ValueError):
        chamado.mudar_status(Status.FECHADO, cliente)
    assert chamado.status == Status.ABERTO


def test_escalonamento_n1_para_n2(cenario):
    central, cliente, n1, n2 = cenario
    chamado = novo_incidente(cliente)
    central.abrir_chamado(chamado)
    chamado.atribuir(n1)
    assert chamado.status == Status.EM_ATENDIMENTO and n1.carga_atual() == 1

    chamado.escalar(n1, "precisa trocar a ponteira RJ45 no local")
    assert chamado.nivel_atual == Nivel.N2
    assert chamado.tecnico is None
    assert chamado.status == Status.ABERTO
    assert n1.carga_atual() == 0
    assert any(i.tipo == TipoInteracao.ESCALONAMENTO for i in chamado.historico)

    with pytest.raises(ValueError):  # N1 não pode mais pegar este chamado
        chamado.atribuir(n1)
    chamado.atribuir(n2)
    assert chamado.tecnico is n2


def test_fluxo_completo_ate_fechar(cenario):
    central, cliente, n1, _ = cenario
    chamado = novo_incidente(cliente)
    central.abrir_chamado(chamado)
    chamado.atribuir(n1)
    chamado.mudar_status(Status.SOLUCIONADO, n1)
    assert chamado.data_resolucao is not None
    chamado.mudar_status(Status.FECHADO, cliente)
    assert chamado.status == Status.FECHADO


def test_calendario_pula_fim_de_semana():
    cal = CalendarioComercial()
    sexta_17h = datetime(2026, 11, 6, 17, 0)
    assert cal.somar_horas_uteis(sexta_17h, 2) == datetime(2026, 11, 9, 9, 0)
    sabado_10h = datetime(2026, 11, 7, 10, 0)
    assert cal.somar_horas_uteis(sabado_10h, 1) == datetime(2026, 11, 9, 9, 0)


def test_horas_uteis_entre():
    cal = CalendarioComercial()
    assert cal.horas_uteis_entre(datetime(2026, 11, 6, 17, 0), datetime(2026, 11, 9, 9, 0)) == 2.0


def test_sla_estourado(cenario):
    _, cliente, _, _ = cenario
    segunda_8h = datetime(2026, 11, 2, 8, 0)
    chamado = novo_incidente(cliente, abertura=segunda_8h)  # prioridade MEDIA = 16h úteis
    cal = CalendarioComercial()
    assert chamado.calcular_prazo(cal) == datetime(2026, 11, 3, 14, 0)
    assert not chamado.sla_estourado(datetime(2026, 11, 3, 13, 0), cal)
    assert chamado.sla_estourado(datetime(2026, 11, 3, 15, 0), cal)


def test_polimorfismo_do_prazo(cenario):
    _, cliente, _, _ = cenario
    segunda_8h = datetime(2026, 11, 2, 8, 0)
    cal = CalendarioComercial()
    incidente = novo_incidente(cliente, abertura=segunda_8h)
    requisicao = Requisicao("Novo mouse", "Solicitação", cliente, Urgencia.MEDIA,
                            Impacto.MEDIO, "Mouse", segunda_8h)
    assert incidente.calcular_prazo(cal) != requisicao.calcular_prazo(cal)
    assert requisicao.calcular_prazo(cal) == datetime(2026, 11, 5, 18, 0)


def test_relatorio_carga_por_tecnico(cenario):
    central, cliente, n1, _ = cenario
    chamado = novo_incidente(cliente)
    central.abrir_chamado(chamado)
    chamado.atribuir(n1)
    assert Relatorio(central).carga_por_tecnico() == {"Carlos": 1, "Ana": 0}
