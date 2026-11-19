"""
NEIGHBORHOOD ACTION DASHBOARD — interface textual
=================================================
Execute:  python src/sistema.py          (menu interativo)
          python src/sistema.py --demo   (roteiro do exemplo do enunciado)
"""
import sys

import indicadores
from painel import (
    CATEGORIAS, DIA_ATUAL, SIGNIFICADO_STATUS, STATUS, atualizar_status,
    buscar_por_codigo, cadastrar, carregar_painel, listar_eventos_da_ocorrencia,
    examinar_proxima, filtrar, montar_hierarquia, montar_matriz_categoria_status,
    listar_ultimas_atualizacoes,
)
from utils import normalizar, transformar_em_porcentagem

LINHA = "=" * 72


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------

def formatar_tabela(cabecalho, linhas):
    """Tabela em texto puro, com colunas alinhadas (lê bem em leitor de tela)."""
    linhas = [[str(celula) for celula in linha] for linha in linhas]
    larguras = [len(nome_coluna) for nome_coluna in cabecalho]
    for linha in linhas:
        for i, celula in enumerate(linha):
            larguras[i] = max(larguras[i], len(celula))
    def formatar_linha(celulas):
        return " | ".join(celula.ljust(larguras[i]) for i, celula in enumerate(celulas))
    saida = [formatar_linha(cabecalho), "-+-".join("-" * largura for largura in larguras)]
    saida += [formatar_linha(linha) for linha in linhas]
    return "\n".join(saida)


def mostrar_titulo(texto):
    print()
    print(LINHA)
    print(texto.upper())
    print(LINHA)


def mostrar_ocorrencias(ocorrencias):
    if not ocorrencias:
        print("Nenhuma ocorrência encontrada com esses critérios.")
        return
    linhas = [
        [ocorrencia["id"], CATEGORIAS[ocorrencia["categoria"]], ocorrencia["bairro"], ocorrencia["local"],
         f"dia {ocorrencia['dia_abertura']}", STATUS[ocorrencia["status"]]]
        for ocorrencia in ocorrencias
    ]
    print(formatar_tabela(["Código", "Categoria", "Bairro", "Local", "Abertura", "Status"], linhas))
    print(f"\n{len(ocorrencias)} ocorrência(s).")


def mostrar_detalhe(painel, ocorrencia):
    print(f"Código:     {ocorrencia['id']}")
    print(f"Categoria:  {CATEGORIAS[ocorrencia['categoria']]}")
    print(f"Descrição:  {ocorrencia['descricao']}")
    print(f"Local:      {ocorrencia['local']} ({ocorrencia['bairro']})")
    print(f"Abertura:   dia {ocorrencia['dia_abertura']}")
    print(f"Status:     {STATUS[ocorrencia['status']]} — {SIGNIFICADO_STATUS[ocorrencia['status']]}")
    eventos = listar_eventos_da_ocorrencia(painel, ocorrencia["id"])
    if eventos:
        print("Histórico:")
        for evento in eventos:
            status_anterior = STATUS.get(evento["de"], "—")
            print(f"  dia {evento['dia']:>2}: {status_anterior} -> {STATUS[evento['para']]} ({evento['nota']})")
    else:
        print("Histórico:  nenhuma atualização ainda.")


def mostrar_eventos(eventos):
    if not eventos:
        print("Nenhum evento registrado.")
        return
    linhas = [
        [evento["id"], f"dia {evento['dia']}", STATUS.get(evento["de"], "—"), STATUS[evento["para"]], evento["nota"]]
        for evento in eventos
    ]
    print(formatar_tabela(["Código", "Dia", "De", "Para", "Nota"], linhas))


# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------

def mostrar_validacao(painel):
    mostrar_titulo("Registros com problema (regras de validação)")
    if not painel["rejeitados"] and not painel["avisos"]:
        print("Todos os registros passaram na validação.")
    for rejeitado in painel["rejeitados"]:
        registro = rejeitado["registro"]
        print(f"Linha {rejeitado['linha']} do CSV (código {registro.get('id') or '?'}): NÃO cadastrada")
        for problema in rejeitado["problemas"]:
            print(f"  - {problema}")
    for aviso in painel["avisos"]:
        print(f"Aviso: {aviso}")
    print("\nRegistros recusados ficam fora da lista e dos indicadores até serem corrigidos no CSV.")


def mostrar_hierarquia(painel):
    mostrar_titulo("Hierarquia: bairro -> categoria -> ocorrências")
    for bairro, por_categoria in sorted(montar_hierarquia(painel).items()):
        total = sum(len(codigos) for codigos in por_categoria.values())
        print(f"{bairro} ({total})")
        for categoria in CATEGORIAS:
            if categoria in por_categoria:
                codigos = por_categoria[categoria]
                print(f"    {CATEGORIAS[categoria]}: {', '.join(codigos)}")


def mostrar_matriz(painel):
    categorias, situacoes, matriz = montar_matriz_categoria_status(painel)
    linhas = []
    totais_coluna = [0 for _ in situacoes]
    for i, categoria in enumerate(categorias):
        linhas.append([CATEGORIAS[categoria]] + matriz[i] + [sum(matriz[i])])
        for j in range(len(situacoes)):
            totais_coluna[j] += matriz[i][j]
    linhas.append(["TOTAL"] + totais_coluna + [sum(totais_coluna)])
    print(formatar_tabela(["Categoria"] + [STATUS[status] for status in situacoes] + ["Total"], linhas))


def mostrar_indicadores(painel):
    resumo = indicadores.resumir_indicadores(painel)
    mostrar_titulo(f"Painel de indicadores (dia {DIA_ATUAL} da simulação)")

    print("Dados de origem: matriz categoria x status (lista de listas)\n")
    mostrar_matriz(painel)

    print("\n1) Proporção por categoria = ocorrências da categoria / total x 100")
    print(formatar_tabela(
        ["Categoria", "Qtd", "%"],
        [[CATEGORIAS[categoria], quantidade, f"{transformar_em_porcentagem(quantidade, resumo['total']):.1f}%"]
         for categoria, quantidade in resumo["por_categoria"].items()],
    ))

    print("\n2) Proporção por status = ocorrências no status / total x 100")
    print(formatar_tabela(
        ["Status", "Qtd", "%"],
        [[STATUS[status], quantidade, f"{transformar_em_porcentagem(quantidade, resumo['total']):.1f}%"]
         for status, quantidade in resumo["por_status"].items()],
    ))

    print("\n3) Tempo médio até a conclusão = soma(dia da conclusão - dia de abertura) / concluídas")
    if resumo["tempos"]:
        print(formatar_tabela(
            ["Código", "Abertura", "Conclusão", "Dias"],
            [[codigo, f"dia {abertura}", f"dia {conclusao}", dias]
             for codigo, abertura, conclusao, dias in resumo["tempos"]],
        ))
        print(f"Tempo médio: {resumo['tempo_medio_conclusao']:.1f} dias")
    else:
        print("Nenhuma ocorrência concluída ainda.")

    print(f"\n4) Pendências = ocorrências com status diferente de Concluída")
    print(f"   idade de cada uma = dia atual ({DIA_ATUAL}) - dia de abertura")
    print(formatar_tabela(
        ["Código", "Status", "Dias em aberto"],
        [[codigo, STATUS[status], dias] for codigo, status, dias in resumo["pendentes"]],
    ))
    print(f"Pendências: {len(resumo['pendentes'])} | idade média: {resumo['idade_media_pendentes']:.1f} dias "
          f"| na fila sem exame: {resumo['na_fila']} | taxa de resolução: {resumo['taxa_resolucao']:.1f}%")

    print("\nO que os números sugerem:")
    for frase in indicadores.interpretar(resumo):
        print(f"- {frase}")


def mostrar_status():
    print("Situações possíveis:")
    for chave, nome in STATUS.items():
        print(f"  {nome}: {SIGNIFICADO_STATUS[chave]}")


# ---------------------------------------------------------------------------
# Entrada de dados
# ---------------------------------------------------------------------------

def perguntar(texto):
    try:
        return input(texto).strip()
    except EOFError:
        return "0"


def escolher(texto, opcoes):
    """Aceita o número da opção ou o nome, com ou sem acento. Vazio = sem filtro."""
    chaves = list(opcoes)
    for i, chave in enumerate(chaves, start=1):
        print(f"  {i}. {opcoes[chave]}")
    resposta = perguntar(texto)
    if resposta == "":
        return None
    if resposta.isdigit() and 1 <= int(resposta) <= len(chaves):
        return chaves[int(resposta) - 1]
    return normalizar(resposta)  # o painel valida e explica se for inválido


def executar_busca(painel):
    codigo = perguntar("Código da ocorrência (ex.: 7 ou 007): ")
    ocorrencia = buscar_por_codigo(painel, codigo)
    if ocorrencia is None:
        print(f"Ocorrência '{codigo}' não encontrada. Use a opção 1 para ver os códigos.")
    else:
        mostrar_detalhe(painel, ocorrencia)


def executar_filtro(painel):
    print("Categoria (Enter para todas):")
    categoria = escolher("> ", CATEGORIAS)
    print("Status (Enter para todos):")
    status = escolher("> ", STATUS)
    if (categoria is not None and categoria not in CATEGORIAS) or (
        status is not None and status not in STATUS
    ):
        print("Categoria ou status inválido. Escolha pelo número da lista.")
        return
    mostrar_ocorrencias(filtrar(painel, categoria, status))


def executar_cadastro(painel):
    print("Nova ocorrência. Não informe nomes, telefones ou e-mails: só o problema e um local genérico.")
    print("Categoria:")
    categoria = escolher("> ", CATEGORIAS) or ""
    descricao = perguntar("Descrição breve: ")
    bairro = perguntar("Bairro: ")
    local = perguntar("Local genérico (ex.: Praça Central): ")
    ok, resultado = cadastrar(painel, categoria, descricao, bairro, local)
    if ok:
        print(f"Cadastrada como {resultado['id']}, status Aberta, no fim da fila.")
    else:
        print("Não foi possível cadastrar:")
        for problema in resultado:
            print(f"  - {problema}")


def executar_atualizacao(painel):
    codigo = perguntar("Código da ocorrência: ")
    if buscar_por_codigo(painel, codigo) is None:
        print(f"Ocorrência '{codigo}' não encontrada.")
        return
    mostrar_status()
    print("Novo status:")
    novo = escolher("> ", STATUS) or ""
    nota = perguntar("Nota sobre a mudança (opcional): ")
    ok, mensagem = atualizar_status(painel, codigo, novo, nota)
    print(mensagem)


def executar_exame(painel):
    if painel["fila"]:
        print("Fila de demandas não examinadas (frente -> fim): " + ", ".join(painel["fila"]))
    ok, mensagem = examinar_proxima(painel)
    print(mensagem)


MENU = [
    ("1", "Listar todas as ocorrências"),
    ("2", "Buscar por código"),
    ("3", "Filtrar por categoria e status"),
    ("4", "Cadastrar nova ocorrência"),
    ("5", "Atualizar status"),
    ("6", "Examinar a próxima demanda da fila"),
    ("7", "Ver as últimas atualizações (pilha)"),
    ("8", "Ver a hierarquia bairro -> categoria"),
    ("9", "Painel de indicadores"),
    ("10", "Registros com problema (validação)"),
    ("0", "Sair"),
]


def executar_menu(painel):
    mostrar_titulo("Neighborhood Action Dashboard")
    print("Painel comunitário de ocorrências com dados fictícios. Digite o número da opção.")
    if painel["rejeitados"]:
        print(f"Atenção: {len(painel['rejeitados'])} registro(s) do arquivo foram recusados (opção 10).")
    while True:
        print()
        for numero, texto in MENU:
            print(f"{numero:>2}. {texto}")
        opcao = perguntar("Opção: ")
        if opcao == "1":
            mostrar_titulo("Ocorrências")
            mostrar_ocorrencias(painel["ocorrencias"])
        elif opcao == "2":
            executar_busca(painel)
        elif opcao == "3":
            executar_filtro(painel)
        elif opcao == "4":
            executar_cadastro(painel)
        elif opcao == "5":
            executar_atualizacao(painel)
        elif opcao == "6":
            executar_exame(painel)
        elif opcao == "7":
            mostrar_titulo("Últimas atualizações (topo da pilha primeiro)")
            mostrar_eventos(listar_ultimas_atualizacoes(painel, 5))
        elif opcao == "8":
            mostrar_hierarquia(painel)
        elif opcao == "9":
            mostrar_indicadores(painel)
        elif opcao == "10":
            mostrar_validacao(painel)
        elif opcao == "0":
            print("Até logo! As alterações desta sessão não são gravadas no CSV.")
            break
        else:
            print(f"Opção '{opcao}' não existe. Digite um número de 0 a 10.")


# ---------------------------------------------------------------------------
# Demonstração (o roteiro do exemplo do enunciado)
# ---------------------------------------------------------------------------

def executar_demo(painel):
    mostrar_titulo("Demonstração: carga e validação")
    print(f"{len(painel['ocorrencias'])} ocorrências válidas carregadas de data/ocorrencias.csv, "
          f"{len(painel['historico'])} eventos de data/historico.csv.")
    mostrar_validacao(painel)

    mostrar_titulo("Listagem")
    mostrar_ocorrencias(painel["ocorrencias"])

    mostrar_titulo("Ação 1: cadastrar uma nova demanda")
    print("Tentativa sem categoria:")
    ok, problemas = cadastrar(painel, "", "Poste apagado ao lado do chafariz", "Centro", "Praça Central")
    for problema in problemas:
        print(f"  - recusada: {problema}")
    print("Tentativa com telefone na descrição:")
    ok, problemas = cadastrar(painel, "iluminacao", "Ligar para 11 98765-4321", "Centro", "Praça Central")
    for problema in problemas:
        print(f"  - recusada: {problema}")
    print("Tentativa correta:")
    ok, nova = cadastrar(painel, "Iluminação", "Poste apagado ao lado do chafariz", "Centro", "Praça Central")
    print(f"  Cadastrada como {nova['id']} (status Aberta, entrou no fim da fila).")

    mostrar_titulo("Consulta: ocorrências abertas de iluminação")
    mostrar_ocorrencias(filtrar(painel, categoria="iluminacao", status="aberta"))

    mostrar_titulo(f"Ação 2: alterar a {nova['id']} para 'em análise'")
    print("Tentativa inválida (pular direto para concluída):")
    print("  " + atualizar_status(painel, nova["id"], "concluída")[1])
    print("Tentativa válida:")
    print("  " + atualizar_status(painel, nova["id"], "em análise", "Equipe de iluminação acionada")[1])
    print("Código que não existe:")
    print("  " + atualizar_status(painel, "99", "concluida")[1])
    print()
    mostrar_detalhe(painel, nova)

    mostrar_titulo("Fila: examinar a demanda aberta mais antiga")
    print("Fila antes: " + ", ".join(painel["fila"]))
    print(examinar_proxima(painel)[1])
    print("Fila depois: " + ", ".join(painel["fila"]))

    mostrar_titulo("Pilha: últimas atualizações")
    mostrar_eventos(listar_ultimas_atualizacoes(painel, 4))

    mostrar_hierarquia(painel)

    print("\nAção 3: indicadores atualizados")
    mostrar_indicadores(painel)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        if not sys.stdin.isatty():  # entrada por pipe ou arquivo; o console já lê Unicode
            sys.stdin.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    painel = carregar_painel()
    if "--demo" in sys.argv:
        executar_demo(painel)
    else:
        executar_menu(painel)


if __name__ == "__main__":
    main()
