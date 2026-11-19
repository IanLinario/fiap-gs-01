"""
UTILS: funções genéricas, que não dependem das regras do painel
================================================================
Servem para qualquer texto, arquivo ou lista de números. As regras da
comunidade (categorias, status, fila, pilha) ficam em painel.py.
"""
import csv
import unicodedata


# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------

def normalizar(texto):
    """'Em Análise ' -> 'em_analise'. Aceita o que a pessoa digitar, com ou sem acento."""
    if texto is None:
        return ""
    texto = texto.strip().lower()
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(caractere for caractere in sem_acento if not unicodedata.combining(caractere))
    return sem_acento.replace(" ", "_").replace("-", "_")


def esta_vazio(valor):
    return valor is None or str(valor).strip() == ""


def parece_dado_pessoal(texto):
    """True se o texto tem e-mail ou uma sequência longa de dígitos (telefone, CPF)."""
    digitos_seguidos = 0
    maior = 0
    for caractere in texto:
        if caractere.isdigit():
            digitos_seguidos += 1
            maior = max(maior, digitos_seguidos)
        elif caractere not in " .-()":
            digitos_seguidos = 0
    return "@" in texto or maior >= 8


# ---------------------------------------------------------------------------
# Arquivos
# ---------------------------------------------------------------------------

def ler_csv(caminho):
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


# ---------------------------------------------------------------------------
# Números
# ---------------------------------------------------------------------------

def transformar_em_porcentagem(parte, total):
    """Percentual de 0 a 100. Total zero dá 0, em vez de erro de divisão."""
    if total == 0:
        return 0.0
    return parte / total * 100


def calcular_media(valores):
    if not valores:
        return 0.0
    return sum(valores) / len(valores)
