"""
INDICADORES do painel
=====================
Contagens, proporções e tempos calculados só com laços e operações simples.
"""
from painel import CATEGORIAS, DIA_ATUAL, STATUS, eventos_da_ocorrencia


def contar_por(ocorrencias, campo, chaves):
    """{chave: quantidade}, na ordem de `chaves` (inclui as que têm zero)."""
    contagem = {chave: 0 for chave in chaves}
    for o in ocorrencias:
        contagem[o[campo]] += 1
    return contagem


def proporcao(parte, total):
    """Percentual de 0 a 100. Total zero dá 0, em vez de erro de divisão."""
    if total == 0:
        return 0.0
    return parte / total * 100


def dia_de_conclusao(painel, codigo):
    for evento in reversed(eventos_da_ocorrencia(painel, codigo)):
        if evento["para"] == "concluida":
            return evento["dia"]
    return None


def tempos_de_conclusao(painel):
    """[(código, dia de abertura, dia de conclusão, dias)] das ocorrências concluídas."""
    tempos = []
    for o in painel["ocorrencias"]:
        if o["status"] == "concluida":
            fim = dia_de_conclusao(painel, o["id"])
            if fim is not None:
                tempos.append((o["id"], o["dia_abertura"], fim, fim - o["dia_abertura"]))
    return tempos


def media(valores):
    if not valores:
        return 0.0
    return sum(valores) / len(valores)


def pendencias(painel):
    """[(código, status, dias em aberto)] de tudo que não foi concluído, do mais antigo ao mais novo."""
    lista = []
    for o in painel["ocorrencias"]:
        if not (o["status"] == "concluida"):
            lista.append((o["id"], o["status"], DIA_ATUAL - o["dia_abertura"]))
    lista.sort(key=lambda item: item[2], reverse=True)
    return lista


def resumo(painel):
    """Junta todos os indicadores num dicionário, usado pela tela e pelos testes."""
    ocorrencias = painel["ocorrencias"]
    total = len(ocorrencias)
    por_categoria = contar_por(ocorrencias, "categoria", CATEGORIAS)
    por_status = contar_por(ocorrencias, "status", STATUS)
    tempos = tempos_de_conclusao(painel)
    pendentes = pendencias(painel)
    return {
        "total": total,
        "por_categoria": por_categoria,
        "por_status": por_status,
        "tempos": tempos,
        "tempo_medio_conclusao": media([t[3] for t in tempos]),
        "pendentes": pendentes,
        "idade_media_pendentes": media([p[2] for p in pendentes]),
        "taxa_resolucao": proporcao(por_status["concluida"], total),
        "na_fila": len(painel["fila"]),
    }


def interpretar(r):
    """Conclusão em texto, montada a partir dos números."""
    if r["total"] == 0:
        return ["Não há ocorrências cadastradas."]
    frases = []

    maior = max(r["por_categoria"].values())
    lideres = [CATEGORIAS[c] for c, n in r["por_categoria"].items() if n == maior]
    if len(lideres) == 1:
        frases.append(f"{lideres[0]} é a categoria com mais registros ({maior}).")
    else:
        frases.append(
            f"Os registros estão espalhados: {', '.join(lideres)} empatam com {maior} cada."
        )

    pendentes = len(r["pendentes"])
    frases.append(
        f"{pendentes} de {r['total']} demandas ({proporcao(pendentes, r['total']):.0f}%) "
        f"ainda não foram resolvidas, e elas estão abertas há "
        f"{r['idade_media_pendentes']:.1f} dias em média."
    )
    if r["tempos"] and r["idade_media_pendentes"] > r["tempo_medio_conclusao"]:
        frases.append(
            f"As pendências já esperam mais que o tempo médio de solução "
            f"({r['tempo_medio_conclusao']:.1f} dias): o atendimento está atrasado "
            f"em relação ao que a comunidade já viu acontecer."
        )
    if r["pendentes"]:
        codigo, status, dias = r["pendentes"][0]
        frases.append(
            f"A demanda mais antiga sem solução é a {codigo} ({STATUS[status]}, {dias} dias)."
        )
    return frases
