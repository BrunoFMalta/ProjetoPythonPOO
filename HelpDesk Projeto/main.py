"""Mini Help Desk - programa principal (interface em terminal)."""
from calendario import CalendarioComercial
from central import Central, Relatorio
from chamados import Chamado, Incidente, Requisicao
from enums import Impacto, Status, TipoInteracao, Urgencia, Nivel
from usuarios import Cliente, Tecnico


# ---------- entrada de dados ----------
def ler_texto(msg: str) -> str:
    while True:
        valor = input(msg).strip()
        if valor:
            return valor
        print("Valor obrigatório.")


def ler_opcao(msg: str, minimo: int, maximo: int) -> int:
    while True:
        try:
            valor = int(input(msg))
        except ValueError:
            print("Digite um número.")
            continue
        if minimo <= valor <= maximo:
            return valor
        print(f"Escolha entre {minimo} e {maximo}.")


def escolher(itens: list, rotulo, titulo: str):
    """Mostra uma lista numerada e devolve o item escolhido (ou None se vazia)."""
    if not itens:
        print("Nenhum item disponível para esta ação.")
        return None
    print(f"\n{titulo}")
    for i, item in enumerate(itens, start=1):
        print(f"  {i}. {rotulo(item)}")
    return itens[ler_opcao("Número: ", 1, len(itens)) - 1]


# ---------- saída de dados ----------
def linha_chamado(central: Central, c: Chamado) -> str:
    tecnico = c.tecnico.nome if c.tecnico else "-"
    prazo = c.calcular_prazo(central.calendario).strftime("%d/%m %H:%M")
    return (f"#{c.id:<3} {type(c).__name__:<10} {c.titulo[:26]:<26} "
            f"{c.prioridade.name:<8} {c.nivel_atual.name:<3} {c.status.value:<15} "
            f"{tecnico:<8} {prazo}")


def listar(central: Central, chamados: list[Chamado]) -> None:
    if not chamados:
        print("Nenhum chamado.")
        return
    print(f"\n{'ID':<4} {'Tipo':<10} {'Título':<26} {'Prior.':<8} {'Nív':<3} "
          f"{'Status':<15} {'Técnico':<8} Prazo")
    for c in chamados:
        print(linha_chamado(central, c))


# ---------- ações do menu ----------
def abrir_chamado(central: Central) -> None:
    cliente = escolher(central.clientes(), lambda c: c.descricao(), "Cliente solicitante:")
    if cliente is None:
        return
    tipo = ler_opcao("Tipo (1-Incidente, 2-Requisição): ", 1, 2)
    titulo = ler_texto("Título: ")
    descricao = ler_texto("Descrição: ")
    urgencia = Urgencia(ler_opcao("Urgência (1-Baixa, 2-Média, 3-Alta): ", 1, 3))
    impacto = Impacto(ler_opcao("Impacto (1-Baixo, 2-Médio, 3-Alto): ", 1, 3))
    if tipo == 1:
        extra = ler_texto("Serviço afetado: ")
        chamado = Incidente(titulo, descricao, cliente, urgencia, impacto, extra)
    else:
        extra = ler_texto("Item solicitado: ")
        chamado = Requisicao(titulo, descricao, cliente, urgencia, impacto, extra)
    central.abrir_chamado(chamado)
    print(f"-> Chamado #{chamado.id} aberto | Prioridade: {chamado.prioridade.name} "
          f"| Nível: {chamado.nivel_atual.name} | Status: {chamado.status.value}")


def atribuir_chamado(central: Central) -> None:
    chamado = escolher(central.buscar(status=Status.ABERTO),
                       lambda c: linha_chamado(central, c), "Chamado a atribuir:")
    if chamado is None:
        return
    tecnico = escolher(central.tecnicos(),
                       lambda t: f"{t.descricao()} - carga: {t.carga_atual()}", "Técnico:")
    central.atribuir(chamado, tecnico)
    print(f"-> Chamado #{chamado.id} atribuído a {tecnico.nome}.")


def escalar_chamado(central: Central) -> None:
    chamado = escolher(central.buscar(status=Status.EM_ATENDIMENTO),
                       lambda c: linha_chamado(central, c), "Chamado a escalar:")
    if chamado is None:
        return
    motivo = ler_texto("Motivo (ex.: precisa de atendimento presencial): ")
    chamado.escalar(chamado.tecnico, motivo)
    print(f"-> Chamado #{chamado.id} escalado para {chamado.nivel_atual.name} "
          f"e devolvido à fila.")


def resolver_chamado(central: Central) -> None:
    chamado = escolher(central.buscar(status=Status.EM_ATENDIMENTO),
                       lambda c: linha_chamado(central, c), "Chamado a resolver:")
    if chamado is None:
        return
    solucao = ler_texto("Solução aplicada: ")
    tecnico = chamado.tecnico
    chamado.mudar_status(Status.SOLUCIONADO, tecnico)
    chamado.registrar_interacao(tecnico, solucao, TipoInteracao.SOLUCAO)
    print(f"-> Chamado #{chamado.id} solucionado.")


def fechar_chamado(central: Central) -> None:
    chamado = escolher(central.chamados, lambda c: linha_chamado(central, c),
                       "Chamado a fechar:")
    if chamado is None:
        return
    chamado.mudar_status(Status.FECHADO, chamado.solicitante)
    print(f"-> Chamado #{chamado.id} fechado.")


def ver_detalhe(central: Central) -> None:
    chamado = escolher(central.chamados, lambda c: linha_chamado(central, c),
                       "Chamado a detalhar:")
    if chamado is None:
        return
    print(f"\nChamado #{chamado.id} - {chamado.titulo}")
    print(f"Descrição : {chamado.descricao}")
    print(f"Solicitante: {chamado.solicitante.descricao()}")
    print(f"Prioridade: {chamado.prioridade.name} | Nível: {chamado.nivel_atual.name} "
          f"| Status: {chamado.status.value}")
    print("Histórico:")
    for interacao in chamado.historico:
        print(f"  {interacao}")


def mostrar_relatorios(central: Central) -> None:
    relatorio = Relatorio(central)
    print("\n--- Chamados com SLA estourado ---")
    estourados = relatorio.sla_estourados()
    if estourados:
        for c in estourados:
            print(linha_chamado(central, c))
    else:
        print("Nenhum.")
    print("\n--- Carga por técnico (chamados em andamento) ---")
    for nome, carga in relatorio.carga_por_tecnico().items():
        print(f"  {nome}: {carga}")
    print(f"\nTempo médio de resolução: {relatorio.tempo_medio_resolucao():.1f} h úteis")


# ---------- preparação e laço principal ----------
def criar_dados_exemplo(central: Central) -> None:
    central.cadastrar_usuario(Cliente("Maria", "maria@empresa.com", "Financeiro"))
    central.cadastrar_usuario(Cliente("João", "joao@empresa.com", "RH"))
    central.cadastrar_usuario(Tecnico("Carlos", "carlos@suporte.com", Nivel.N1))
    central.cadastrar_usuario(Tecnico("Ana", "ana@suporte.com", Nivel.N2))
    joao = central.clientes()[1]
    central.abrir_chamado(Incidente("Impressora do RH não imprime", "Fila travada",
                                    joao, Urgencia.MEDIA, Impacto.MEDIO, "Impressão"))


MENU = """
=== MINI HELP DESK ===
1. Abrir chamado
2. Listar chamados
3. Atribuir chamado a técnico
4. Escalar chamado (N1 -> N2)
5. Resolver chamado
6. Fechar chamado
7. Ver detalhes e histórico
8. Relatórios
0. Sair"""


def main() -> None:
    central = Central(CalendarioComercial())
    criar_dados_exemplo(central)
    acoes = {
        1: abrir_chamado,
        2: lambda c: listar(c, c.chamados),
        3: atribuir_chamado,
        4: escalar_chamado,
        5: resolver_chamado,
        6: fechar_chamado,
        7: ver_detalhe,
        8: mostrar_relatorios,
    }
    while True:
        print(MENU)
        opcao = ler_opcao("Escolha: ", 0, 8)
        if opcao == 0:
            print("Até logo!")
            break
        try:
            acoes[opcao](central)
        except ValueError as erro:
            print(f"!! Não permitido: {erro}")


if __name__ == "__main__":
    main()
