"""
INDICADORES do painel
=====================
Contagens, proporções e tempos calculados só com laços e operações simples.
"""
from painel import CATEGORIAS, DIA_ATUAL, STATUS, listar_eventos_da_ocorrencia
from utils import calcular_media, transformar_em_porcentagem


def contar_por(ocorrencias, campo, chaves):
    """{chave: quantidade}, na ordem de `chaves` (inclui as que têm zero)."""
    contagem = {chave: 0 for chave in chaves}
    for ocorrencia in ocorrencias:
        contagem[ocorrencia[campo]] += 1
    return contagem


def encontrar_dia_de_conclusao(painel, codigo):
    for evento in reversed(listar_eventos_da_ocorrencia(painel, codigo)):
        if evento["para"] == "concluida":
            return evento["dia"]
    return None


def calcular_tempos_de_conclusao(painel):
    """[(código, dia de abertura, dia de conclusão, dias)] das ocorrências concluídas."""
    tempos = []
    for ocorrencia in painel["ocorrencias"]:
        if ocorrencia["status"] == "concluida":
            fim = encontrar_dia_de_conclusao(painel, ocorrencia["id"])
            if fim is not None:
                tempos.append((ocorrencia["id"], ocorrencia["dia_abertura"], fim, fim - ocorrencia["dia_abertura"]))
    return tempos


def listar_pendencias(painel):
    """[(código, status, dias em aberto)] de tudo que não foi concluído, do mais antigo ao mais novo."""
    pendentes = []
    for ocorrencia in painel["ocorrencias"]:
        if not (ocorrencia["status"] == "concluida"):
            pendentes.append((ocorrencia["id"], ocorrencia["status"], DIA_ATUAL - ocorrencia["dia_abertura"]))
    pendentes.sort(key=lambda pendencia: pendencia[2], reverse=True)
    return pendentes


def resumir_indicadores(painel):
    """Junta todos os indicadores num dicionário, usado pela tela e pelos testes."""
    ocorrencias = painel["ocorrencias"]
    total = len(ocorrencias)
    por_categoria = contar_por(ocorrencias, "categoria", CATEGORIAS)
    por_status = contar_por(ocorrencias, "status", STATUS)
    tempos = calcular_tempos_de_conclusao(painel)
    pendentes = listar_pendencias(painel)
    return {
        "total": total,
        "por_categoria": por_categoria,
        "por_status": por_status,
        "tempos": tempos,
        "tempo_medio_conclusao": calcular_media([tempo[3] for tempo in tempos]),
        "pendentes": pendentes,
        "idade_media_pendentes": calcular_media([pendencia[2] for pendencia in pendentes]),
        "taxa_resolucao": transformar_em_porcentagem(por_status["concluida"], total),
        "na_fila": len(painel["fila"]),
    }


def interpretar(resumo_painel):
    """Conclusão em texto, montada a partir dos números."""
    if resumo_painel["total"] == 0:
        return ["Não há ocorrências cadastradas."]
    frases = []

    tamanho_maior_categoria = max(resumo_painel["por_categoria"].values())
    categorias_lideres = [CATEGORIAS[categoria] for categoria, tamanho_categoria in resumo_painel["por_categoria"].items() if tamanho_categoria == tamanho_maior_categoria]

    if len(categorias_lideres) == 1:
        frases.append(f"{categorias_lideres[0]} é a categoria com mais registros ({tamanho_maior_categoria}).")
    else:
        frases.append(
            f"Os registros estão espalhados: {', '.join(categorias_lideres)} empatam com {tamanho_maior_categoria} cada."
        )

    pendentes = len(resumo_painel["pendentes"])
    frases.append(
        f"{pendentes} de {resumo_painel['total']} demandas ({transformar_em_porcentagem(pendentes, resumo_painel['total']):.0f}%) "
        f"ainda não foram resolvidas, e elas estão abertas há "
        f"{resumo_painel['idade_media_pendentes']:.1f} dias em média."
    )
    if resumo_painel["tempos"] and resumo_painel["idade_media_pendentes"] > resumo_painel["tempo_medio_conclusao"]:
        frases.append(
            f"As pendências já esperam mais que o tempo médio de solução "
            f"({resumo_painel['tempo_medio_conclusao']:.1f} dias): o atendimento está atrasado "
            f"em relação ao que a comunidade já viu acontecer."
        )
    if resumo_painel["pendentes"]:
        codigo, status, dias = resumo_painel["pendentes"][0]
        frases.append(
            f"A demanda mais antiga sem solução é a {codigo} ({STATUS[status]}, {dias} dias)."
        )
    return frases
