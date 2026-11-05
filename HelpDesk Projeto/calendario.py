"""Regra de tempo: cálculo de prazos em horas comerciais."""
from datetime import datetime, time, timedelta


class CalendarioComercial:
    """Conta apenas horas úteis (por padrão seg-sex, 8h às 18h, sem feriados)."""

    def __init__(self, hora_inicio: time = time(8, 0), hora_fim: time = time(18, 0),
                 dias_uteis: set[int] | None = None) -> None:
        self.__hora_inicio = hora_inicio
        self.__hora_fim = hora_fim
        # 0 = segunda ... 6 = domingo
        self.__dias_uteis = dias_uteis if dias_uteis is not None else {0, 1, 2, 3, 4}

    def __eh_dia_util(self, momento: datetime) -> bool:
        return momento.weekday() in self.__dias_uteis

    def __eh_expediente(self, momento: datetime) -> bool:
        return (self.__eh_dia_util(momento)
                and self.__hora_inicio <= momento.time() < self.__hora_fim)

    def __proximo_expediente(self, momento: datetime) -> datetime:
        """Devolve o próprio momento se for expediente; senão, o início do próximo."""
        if self.__eh_expediente(momento):
            return momento
        if self.__eh_dia_util(momento) and momento.time() < self.__hora_inicio:
            return datetime.combine(momento.date(), self.__hora_inicio)
        dia = momento.date() + timedelta(days=1)
        while dia.weekday() not in self.__dias_uteis:
            dia += timedelta(days=1)
        return datetime.combine(dia, self.__hora_inicio)

    def somar_horas_uteis(self, inicio: datetime, horas: float) -> datetime:
        """Devolve o momento em que 'horas' úteis terão passado a partir de 'inicio'."""
        restante = timedelta(hours=horas)
        atual = self.__proximo_expediente(inicio)
        while True:
            fim_do_dia = datetime.combine(atual.date(), self.__hora_fim)
            disponivel = fim_do_dia - atual
            if restante <= disponivel:
                return atual + restante
            restante -= disponivel
            atual = self.__proximo_expediente(fim_do_dia)

    def horas_uteis_entre(self, inicio: datetime, fim: datetime) -> float:
        """Quantidade de horas úteis entre dois momentos."""
        if fim <= inicio:
            return 0.0
        total = timedelta()
        atual = self.__proximo_expediente(inicio)
        while atual < fim:
            fim_do_dia = datetime.combine(atual.date(), self.__hora_fim)
            total += min(fim, fim_do_dia) - atual
            atual = self.__proximo_expediente(fim_do_dia)
        return total.total_seconds() / 3600
