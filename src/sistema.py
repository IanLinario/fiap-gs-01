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
    buscar_por_codigo, cadastrar, carregar_painel, eventos_da_ocorrencia,
    examinar_proxima, filtrar, hierarquia, matriz_categoria_status, normalizar,
    ultimas_atualizacoes,
)

LINHA = "=" * 72


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------

def tabela(cabecalho, linhas):
    """Tabela em texto puro, com colunas alinhadas (lê bem em leitor de tela)."""
    linhas = [[str(c) for c in linha] for linha in linhas]
    larguras = [len(c) for c in cabecalho]
    for linha in linhas:
        for i, celula in enumerate(linha):
            larguras[i] = max(larguras[i], len(celula))
    def formatar(celulas):
        return " | ".join(c.ljust(larguras[i]) for i, c in enumerate(celulas))
    saida = [formatar(cabecalho), "-+-".join("-" * l for l in larguras)]
    saida += [formatar(linha) for linha in linhas]
    return "\n".join(saida)


def titulo(texto):
    print()
    print(LINHA)
    print(texto.upper())
    print(LINHA)


def mostrar_ocorrencias(lista):
    if not lista:
        print("Nenhuma ocorrência encontrada com esses critérios.")
        return
    linhas = [
        [o["id"], CATEGORIAS[o["categoria"]], o["bairro"], o["local"],
         f"dia {o['dia_abertura']}", STATUS[o["status"]]]
        for o in lista
    ]
    print(tabela(["Código", "Categoria", "Bairro", "Local", "Abertura", "Status"], linhas))
    print(f"\n{len(lista)} ocorrência(s).")


def mostrar_detalhe(painel, o):
    print(f"Código:     {o['id']}")
    print(f"Categoria:  {CATEGORIAS[o['categoria']]}")
    print(f"Descrição:  {o['descricao']}")
    print(f"Local:      {o['local']} ({o['bairro']})")
    print(f"Abertura:   dia {o['dia_abertura']}")
    print(f"Status:     {STATUS[o['status']]} — {SIGNIFICADO_STATUS[o['status']]}")
    eventos = eventos_da_ocorrencia(painel, o["id"])
    if eventos:
        print("Histórico:")
        for e in eventos:
            de = STATUS.get(e["de"], "—")
            print(f"  dia {e['dia']:>2}: {de} -> {STATUS[e['para']]} ({e['nota']})")
    else:
        print("Histórico:  nenhuma atualização ainda.")


def mostrar_eventos(eventos):
    if not eventos:
        print("Nenhum evento registrado.")
        return
    linhas = [
        [e["id"], f"dia {e['dia']}", STATUS.get(e["de"], "—"), STATUS[e["para"]], e["nota"]]
        for e in eventos
    ]
    print(tabela(["Código", "Dia", "De", "Para", "Nota"], linhas))


# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------

def tela_validacao(painel):
    titulo("Registros com problema (regras de validação)")
    if not painel["rejeitados"] and not painel["avisos"]:
        print("Todos os registros passaram na validação.")
    for r in painel["rejeitados"]:
        reg = r["registro"]
        print(f"Linha {r['linha']} do CSV (código {reg.get('id') or '?'}): NÃO cadastrada")
        for problema in r["problemas"]:
            print(f"  - {problema}")
    for aviso in painel["avisos"]:
        print(f"Aviso: {aviso}")
    print("\nRegistros recusados ficam fora da lista e dos indicadores até serem corrigidos no CSV.")


def tela_hierarquia(painel):
    titulo("Hierarquia: bairro -> categoria -> ocorrências")
    for bairro, por_categoria in sorted(hierarquia(painel).items()):
        total = sum(len(codigos) for codigos in por_categoria.values())
        print(f"{bairro} ({total})")
        for categoria in CATEGORIAS:
            if categoria in por_categoria:
                codigos = por_categoria[categoria]
                print(f"    {CATEGORIAS[categoria]}: {', '.join(codigos)}")


def tela_matriz(painel):
    categorias, situacoes, matriz = matriz_categoria_status(painel)
    linhas = []
    totais_coluna = [0 for _ in situacoes]
    for i, categoria in enumerate(categorias):
        linhas.append([CATEGORIAS[categoria]] + matriz[i] + [sum(matriz[i])])
        for j in range(len(situacoes)):
            totais_coluna[j] += matriz[i][j]
    linhas.append(["TOTAL"] + totais_coluna + [sum(totais_coluna)])
    print(tabela(["Categoria"] + [STATUS[s] for s in situacoes] + ["Total"], linhas))


def tela_indicadores(painel):
    r = indicadores.resumo(painel)
    titulo(f"Painel de indicadores (dia {DIA_ATUAL} da simulação)")

    print("Dados de origem: matriz categoria x status (lista de listas)\n")
    tela_matriz(painel)

    print("\n1) Proporção por categoria = ocorrências da categoria / total x 100")
    print(tabela(
        ["Categoria", "Qtd", "%"],
        [[CATEGORIAS[c], n, f"{indicadores.proporcao(n, r['total']):.1f}%"]
         for c, n in r["por_categoria"].items()],
    ))

    print("\n2) Proporção por status = ocorrências no status / total x 100")
    print(tabela(
        ["Status", "Qtd", "%"],
        [[STATUS[s], n, f"{indicadores.proporcao(n, r['total']):.1f}%"]
         for s, n in r["por_status"].items()],
    ))

    print("\n3) Tempo médio até a conclusão = soma(dia da conclusão - dia de abertura) / concluídas")
    if r["tempos"]:
        print(tabela(
            ["Código", "Abertura", "Conclusão", "Dias"],
            [[c, f"dia {a}", f"dia {f}", d] for c, a, f, d in r["tempos"]],
        ))
        print(f"Tempo médio: {r['tempo_medio_conclusao']:.1f} dias")
    else:
        print("Nenhuma ocorrência concluída ainda.")

    print(f"\n4) Pendências = ocorrências com status diferente de Concluída")
    print(f"   idade de cada uma = dia atual ({DIA_ATUAL}) - dia de abertura")
    print(tabela(
        ["Código", "Status", "Dias em aberto"],
        [[c, STATUS[s], d] for c, s, d in r["pendentes"]],
    ))
    print(f"Pendências: {len(r['pendentes'])} | idade média: {r['idade_media_pendentes']:.1f} dias "
          f"| na fila sem exame: {r['na_fila']} | taxa de resolução: {r['taxa_resolucao']:.1f}%")

    print("\nO que os números sugerem:")
    for frase in indicadores.interpretar(r):
        print(f"- {frase}")


def tela_status():
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


def acao_buscar(painel):
    codigo = perguntar("Código da ocorrência (ex.: 7 ou 007): ")
    o = buscar_por_codigo(painel, codigo)
    if o is None:
        print(f"Ocorrência '{codigo}' não encontrada. Use a opção 1 para ver os códigos.")
    else:
        mostrar_detalhe(painel, o)


def acao_filtrar(painel):
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


def acao_cadastrar(painel):
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


def acao_atualizar(painel):
    codigo = perguntar("Código da ocorrência: ")
    if buscar_por_codigo(painel, codigo) is None:
        print(f"Ocorrência '{codigo}' não encontrada.")
        return
    tela_status()
    print("Novo status:")
    novo = escolher("> ", STATUS) or ""
    nota = perguntar("Nota sobre a mudança (opcional): ")
    ok, mensagem = atualizar_status(painel, codigo, novo, nota)
    print(mensagem)


def acao_examinar(painel):
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


def menu(painel):
    titulo("Neighborhood Action Dashboard")
    print("Painel comunitário de ocorrências com dados fictícios. Digite o número da opção.")
    if painel["rejeitados"]:
        print(f"Atenção: {len(painel['rejeitados'])} registro(s) do arquivo foram recusados (opção 10).")
    while True:
        print()
        for numero, texto in MENU:
            print(f"{numero:>2}. {texto}")
        opcao = perguntar("Opção: ")
        if opcao == "1":
            titulo("Ocorrências")
            mostrar_ocorrencias(painel["ocorrencias"])
        elif opcao == "2":
            acao_buscar(painel)
        elif opcao == "3":
            acao_filtrar(painel)
        elif opcao == "4":
            acao_cadastrar(painel)
        elif opcao == "5":
            acao_atualizar(painel)
        elif opcao == "6":
            acao_examinar(painel)
        elif opcao == "7":
            titulo("Últimas atualizações (topo da pilha primeiro)")
            mostrar_eventos(ultimas_atualizacoes(painel, 5))
        elif opcao == "8":
            tela_hierarquia(painel)
        elif opcao == "9":
            tela_indicadores(painel)
        elif opcao == "10":
            tela_validacao(painel)
        elif opcao == "0":
            print("Até logo! As alterações desta sessão não são gravadas no CSV.")
            break
        else:
            print(f"Opção '{opcao}' não existe. Digite um número de 0 a 10.")


# ---------------------------------------------------------------------------
# Demonstração (o roteiro do exemplo do enunciado)
# ---------------------------------------------------------------------------

def demo(painel):
    titulo("Demonstração: carga e validação")
    print(f"{len(painel['ocorrencias'])} ocorrências válidas carregadas de data/ocorrencias.csv, "
          f"{len(painel['historico'])} eventos de data/historico.csv.")
    tela_validacao(painel)

    titulo("Listagem")
    mostrar_ocorrencias(painel["ocorrencias"])

    titulo("Ação 1: cadastrar uma nova demanda")
    print("Tentativa sem categoria:")
    ok, problemas = cadastrar(painel, "", "Poste apagado ao lado do chafariz", "Centro", "Praça Central")
    for p in problemas:
        print(f"  - recusada: {p}")
    print("Tentativa com telefone na descrição:")
    ok, problemas = cadastrar(painel, "iluminacao", "Ligar para 11 98765-4321", "Centro", "Praça Central")
    for p in problemas:
        print(f"  - recusada: {p}")
    print("Tentativa correta:")
    ok, nova = cadastrar(painel, "Iluminação", "Poste apagado ao lado do chafariz", "Centro", "Praça Central")
    print(f"  Cadastrada como {nova['id']} (status Aberta, entrou no fim da fila).")

    titulo("Consulta: ocorrências abertas de iluminação")
    mostrar_ocorrencias(filtrar(painel, categoria="iluminacao", status="aberta"))

    titulo(f"Ação 2: alterar a {nova['id']} para 'em análise'")
    print("Tentativa inválida (pular direto para concluída):")
    print("  " + atualizar_status(painel, nova["id"], "concluída")[1])
    print("Tentativa válida:")
    print("  " + atualizar_status(painel, nova["id"], "em análise", "Equipe de iluminação acionada")[1])
    print("Código que não existe:")
    print("  " + atualizar_status(painel, "99", "concluida")[1])
    print()
    mostrar_detalhe(painel, nova)

    titulo("Fila: examinar a demanda aberta mais antiga")
    print("Fila antes: " + ", ".join(painel["fila"]))
    print(examinar_proxima(painel)[1])
    print("Fila depois: " + ", ".join(painel["fila"]))

    titulo("Pilha: últimas atualizações")
    mostrar_eventos(ultimas_atualizacoes(painel, 4))

    tela_hierarquia(painel)

    print("\nAção 3: indicadores atualizados")
    tela_indicadores(painel)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        if not sys.stdin.isatty():  # entrada por pipe ou arquivo; o console já lê Unicode
            sys.stdin.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    painel = carregar_painel()
    if "--demo" in sys.argv:
        demo(painel)
    else:
        menu(painel)


if __name__ == "__main__":
    main()
