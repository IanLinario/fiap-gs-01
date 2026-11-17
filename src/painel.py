"""
PAINEL: dados, estruturas e regras do Neighborhood Action Dashboard
===================================================================
Lê as ocorrências e o histórico dos arquivos CSV, valida cada registro e
organiza tudo nas estruturas pedidas no enunciado:

- lista      -> todas as ocorrências válidas, na ordem de registro
- dicionário -> índice {código: ocorrência}, para buscar pelo código
- fila       -> ocorrências "aberta" ainda não examinadas, por ordem de abertura
- pilha      -> eventos de acompanhamento; o topo é sempre o mais recente
- hierarquia -> bairro -> categoria -> códigos das ocorrências
- matriz     -> quantidade de ocorrências por categoria (linha) e status (coluna)

Só usa a biblioteca padrão do Python.
"""
import csv
import os
import unicodedata
from collections import deque

PASTA_DADOS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
)

# A simulação acontece em "dias": o dia 1 é o início do acompanhamento
# e hoje é o dia 30. Não usamos datas reais.
DIA_ATUAL = 30

# Valores padronizados (chave usada no código -> nome mostrado na tela)
CATEGORIAS = {
    "iluminacao": "Iluminação",
    "acessibilidade": "Acessibilidade",
    "limpeza": "Limpeza",
    "conservacao": "Conservação",
}

STATUS = {
    "aberta": "Aberta",
    "em_analise": "Em análise",
    "concluida": "Concluída",
}

SIGNIFICADO_STATUS = {
    "aberta": "registrada pela comunidade e ainda não examinada; espera na fila",
    "em_analise": "alguém já examinou a demanda e o encaminhamento está em andamento",
    "concluida": "o problema foi resolvido; o registro não muda mais",
}

# Mudanças de status permitidas. "em_analise -> aberta" devolve a demanda
# para a fila quando falta informação. "concluida" é final.
TRANSICOES = {
    "aberta": ["em_analise"],
    "em_analise": ["concluida", "aberta"],
    "concluida": [],
}

CAMPOS = ["id", "categoria", "descricao", "bairro", "local", "dia_abertura", "status"]
CAMPOS_OBRIGATORIOS = CAMPOS  # todos são obrigatórios


# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------

def normalizar(texto):
    """'Em Análise ' -> 'em_analise'. Aceita o que a pessoa digitar, com ou sem acento."""
    if texto is None:
        return ""
    texto = texto.strip().lower()
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.replace(" ", "_").replace("-", "_")


def normalizar_codigo(codigo):
    """'14' -> '014'. Códigos têm sempre três dígitos."""
    codigo = (codigo or "").strip()
    if codigo.isdigit():
        return codigo.zfill(3)
    return codigo


def vazio(valor):
    return valor is None or str(valor).strip() == ""


def parece_dado_pessoal(texto):
    """True se o texto tem e-mail ou uma sequência longa de dígitos (telefone, CPF)."""
    digitos_seguidos = 0
    maior = 0
    for c in texto:
        if c.isdigit():
            digitos_seguidos += 1
            maior = max(maior, digitos_seguidos)
        elif c not in " .-()":
            digitos_seguidos = 0
    return "@" in texto or maior >= 8


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def validar_ocorrencia(registro, codigos_usados):
    """
    Devolve a lista de problemas do registro (lista vazia = registro válido).
    `codigos_usados` são os códigos já aceitos, para impedir duplicados.
    """
    problemas = []
    for campo in CAMPOS_OBRIGATORIOS:
        if vazio(registro.get(campo)):
            problemas.append(f"campo obrigatório '{campo}' ausente")

    codigo = registro.get("id", "")
    categoria = normalizar(registro.get("categoria"))
    status = normalizar(registro.get("status"))
    descricao = registro.get("descricao") or ""
    dia = registro.get("dia_abertura")

    if not vazio(codigo) and codigo in codigos_usados:
        problemas.append(f"código {codigo} repetido (já existe outra ocorrência com ele)")
    if not vazio(categoria) and categoria not in CATEGORIAS:
        problemas.append(f"categoria desconhecida: '{registro.get('categoria')}'")
    if not vazio(status) and status not in STATUS:
        problemas.append(f"status desconhecido: '{registro.get('status')}'")
    if not vazio(dia):
        if not str(dia).strip().isdigit():
            problemas.append(f"dia de abertura não é um número: '{dia}'")
        elif int(dia) < 1 or int(dia) > DIA_ATUAL:
            problemas.append(f"dia de abertura fora da simulação (1 a {DIA_ATUAL}): {dia}")
    if parece_dado_pessoal(descricao) or parece_dado_pessoal(registro.get("local") or ""):
        problemas.append("o texto parece conter dado pessoal (e-mail ou telefone)")
    return problemas


# ---------------------------------------------------------------------------
# Carga dos arquivos
# ---------------------------------------------------------------------------

def ler_csv(caminho):
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def painel_vazio():
    return {
        "ocorrencias": [],     # lista
        "indice": {},          # dicionário código -> ocorrência
        "fila": deque(),       # fila de códigos "aberta"
        "pilha": [],           # pilha de eventos (topo = último)
        "historico": [],       # todos os eventos em ordem cronológica
        "rejeitados": [],      # registros inválidos e o motivo
        "avisos": [],          # inconsistências que não impedem o uso
        "maior_codigo": 0,     # para gerar o próximo código sem repetir
    }


def carregar_painel(pasta=PASTA_DADOS):
    painel = painel_vazio()

    linhas = ler_csv(os.path.join(pasta, "ocorrencias.csv"))
    for numero, registro in enumerate(linhas, start=2):  # linha 1 é o cabeçalho
        codigo = normalizar_codigo(registro.get("id"))
        registro["id"] = codigo
        if codigo.isdigit():
            painel["maior_codigo"] = max(painel["maior_codigo"], int(codigo))

        problemas = validar_ocorrencia(registro, painel["indice"])
        if problemas:
            painel["rejeitados"].append(
                {"linha": numero, "registro": registro, "problemas": problemas}
            )
            continue
        _incluir(painel, _montar_ocorrencia(registro))

    eventos = ler_csv(os.path.join(pasta, "historico.csv"))
    eventos.sort(key=lambda e: int(e["dia"]))  # sort é estável: empates mantêm a ordem do arquivo
    for evento in eventos:
        codigo = normalizar_codigo(evento["id"])
        de, para = normalizar(evento["de"]), normalizar(evento["para"])
        if codigo not in painel["indice"]:
            painel["avisos"].append(f"evento ignorado: ocorrência {codigo} não existe")
        elif de not in STATUS or para not in STATUS:
            painel["avisos"].append(f"evento ignorado em {codigo}: status desconhecido")
        else:
            _registrar_evento(painel, codigo, int(evento["dia"]), de, para, evento["nota"])

    _conferir_historico(painel)

    abertas = [o for o in painel["ocorrencias"] if o["status"] == "aberta"]
    abertas.sort(key=lambda o: (o["dia_abertura"], o["id"]))
    for ocorrencia in abertas:
        painel["fila"].append(ocorrencia["id"])
    return painel


def _montar_ocorrencia(registro):
    return {
        "id": registro["id"],
        "categoria": normalizar(registro["categoria"]),
        "descricao": registro["descricao"].strip(),
        "bairro": registro["bairro"].strip(),
        "local": registro["local"].strip(),
        "dia_abertura": int(registro["dia_abertura"]),
        "status": normalizar(registro["status"]),
    }


def _incluir(painel, ocorrencia):
    painel["ocorrencias"].append(ocorrencia)
    painel["indice"][ocorrencia["id"]] = ocorrencia


def _registrar_evento(painel, codigo, dia, de, para, nota):
    evento = {"id": codigo, "dia": dia, "de": de, "para": para, "nota": nota}
    painel["historico"].append(evento)
    painel["pilha"].append(evento)  # empilha: o mais recente fica no topo
    return evento


def _conferir_historico(painel):
    """O último evento de cada ocorrência precisa levar ao status atual dela."""
    for ocorrencia in painel["ocorrencias"]:
        eventos = eventos_da_ocorrencia(painel, ocorrencia["id"])
        if eventos and eventos[-1]["para"] != ocorrencia["status"]:
            painel["avisos"].append(
                f"{ocorrencia['id']}: o histórico termina em '{eventos[-1]['para']}', "
                f"mas o status é '{ocorrencia['status']}'"
            )
        elif not eventos and ocorrencia["status"] != "aberta":
            painel["avisos"].append(
                f"{ocorrencia['id']}: status '{ocorrencia['status']}' sem nenhum evento no histórico"
            )


# ---------------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------------

def buscar_por_codigo(painel, codigo):
    """Acesso direto pelo dicionário. Devolve None se não existir."""
    return painel["indice"].get(normalizar_codigo(codigo))


def filtrar(painel, categoria=None, status=None, bairro=None):
    """
    Filtro combinado. Um critério None não restringe nada:
    (categoria is None or o.categoria == categoria) and (status is None or o.status == status)
    """
    resultado = []
    for o in painel["ocorrencias"]:
        if (
            (categoria is None or o["categoria"] == categoria)
            and (status is None or o["status"] == status)
            and (bairro is None or normalizar(o["bairro"]) == normalizar(bairro))
        ):
            resultado.append(o)
    return resultado


def eventos_da_ocorrencia(painel, codigo):
    return [e for e in painel["historico"] if e["id"] == codigo]


def ultimas_atualizacoes(painel, quantidade=5):
    """Lê a pilha do topo para baixo sem desempilhar."""
    recentes = []
    posicao = len(painel["pilha"]) - 1
    while posicao >= 0 and len(recentes) < quantidade:
        recentes.append(painel["pilha"][posicao])
        posicao -= 1
    return recentes


def hierarquia(painel):
    """{bairro: {categoria: [códigos]}}"""
    arvore = {}
    for o in painel["ocorrencias"]:
        por_categoria = arvore.setdefault(o["bairro"], {})
        por_categoria.setdefault(o["categoria"], []).append(o["id"])
    return arvore


def matriz_categoria_status(painel):
    """Lista de listas: uma linha por categoria, uma coluna por status."""
    categorias = list(CATEGORIAS)
    situacoes = list(STATUS)
    matriz = [[0 for _ in situacoes] for _ in categorias]
    for o in painel["ocorrencias"]:
        linha = categorias.index(o["categoria"])
        coluna = situacoes.index(o["status"])
        matriz[linha][coluna] += 1
    return categorias, situacoes, matriz


# ---------------------------------------------------------------------------
# Alterações
# ---------------------------------------------------------------------------

def cadastrar(painel, categoria, descricao, bairro, local, dia=None):
    """
    Cadastra uma nova ocorrência com o próximo código livre e status "aberta".
    Devolve (True, ocorrência) ou (False, lista de problemas).
    """
    codigo = str(painel["maior_codigo"] + 1).zfill(3)
    registro = {
        "id": codigo,
        "categoria": categoria,
        "descricao": descricao,
        "bairro": bairro,
        "local": local,
        "dia_abertura": str(DIA_ATUAL if dia is None else dia),
        "status": "aberta",
    }
    problemas = validar_ocorrencia(registro, painel["indice"])
    if problemas:
        return False, problemas

    ocorrencia = _montar_ocorrencia(registro)
    _incluir(painel, ocorrencia)
    painel["maior_codigo"] += 1
    painel["fila"].append(codigo)  # entra no fim da fila
    _registrar_evento(painel, codigo, ocorrencia["dia_abertura"], "-", "aberta", "Cadastro")
    return True, ocorrencia


def atualizar_status(painel, codigo, novo_status, nota="", dia=None):
    """
    Muda o status se a transição for permitida e registra no histórico.
    Devolve (True, mensagem) ou (False, motivo).
    """
    ocorrencia = buscar_por_codigo(painel, codigo)
    novo = normalizar(novo_status)
    dia = DIA_ATUAL if dia is None else dia

    if ocorrencia is None:
        return False, f"Ocorrência {normalizar_codigo(codigo)} não encontrada."
    atual = ocorrencia["status"]
    if novo not in STATUS:
        return False, (
            f"Status '{novo_status}' desconhecido. Use: " + ", ".join(STATUS.values()) + "."
        )
    elif novo == atual:
        return False, f"A ocorrência {ocorrencia['id']} já está '{STATUS[atual]}'."
    elif not (novo in TRANSICOES[atual]):
        if atual == "concluida":
            return False, "Ocorrência concluída não muda mais. Cadastre uma nova se o problema voltar."
        return False, (
            f"Não é possível ir de '{STATUS[atual]}' para '{STATUS[novo]}'. "
            f"Permitido: " + ", ".join(STATUS[s] for s in TRANSICOES[atual]) + "."
        )
    else:
        if atual == "aberta" and ocorrencia["id"] in painel["fila"]:
            painel["fila"].remove(ocorrencia["id"])
        if novo == "aberta":
            painel["fila"].append(ocorrencia["id"])  # volta para o fim da fila
        ocorrencia["status"] = novo
        _registrar_evento(painel, ocorrencia["id"], dia, atual, novo, nota or "Atualização manual")
        return True, (
            f"Ocorrência {ocorrencia['id']}: '{STATUS[atual]}' -> '{STATUS[novo]}' (dia {dia})."
        )


def examinar_proxima(painel, nota="Examinada a partir da fila"):
    """Tira da frente da fila a demanda mais antiga e a passa para 'em análise'."""
    if not painel["fila"]:
        return False, "A fila está vazia: nenhuma demanda aberta esperando exame."
    codigo = painel["fila"][0]
    return atualizar_status(painel, codigo, "em_analise", nota)
