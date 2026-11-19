"""Testes automáticos. Rode com:  python -m unittest discover -s tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import indicadores  # noqa: E402
from painel import (  # noqa: E402
    atualizar_status, buscar_por_codigo, cadastrar, carregar_painel,
    examinar_proxima, filtrar, montar_hierarquia, montar_matriz_categoria_status,
    listar_ultimas_atualizacoes, validar_ocorrencia,
)
from utils import transformar_em_porcentagem  # noqa: E402


class TestCarga(unittest.TestCase):
    def setUp(self):
        self.painel = carregar_painel()

    def test_carrega_12_validas_e_recusa_2(self):
        self.assertEqual(len(self.painel["ocorrencias"]), 12)
        self.assertEqual(len(self.painel["rejeitados"]), 2)
        self.assertEqual(len(self.painel["historico"]), 12)
        self.assertEqual(self.painel["avisos"], [])

    def test_recusa_sem_categoria_e_codigo_repetido(self):
        motivos = [problema for rejeitado in self.painel["rejeitados"] for problema in rejeitado["problemas"]]
        self.assertIn("campo obrigatório 'categoria' ausente", motivos)
        self.assertTrue(any("repetido" in m for m in motivos))
        # o 007 que ficou é o primeiro do arquivo
        self.assertEqual(buscar_por_codigo(self.painel, "7")["categoria"], "acessibilidade")

    def test_fila_por_ordem_de_abertura(self):
        self.assertEqual(list(self.painel["fila"]), ["004", "007", "009", "012"])

    def test_topo_da_pilha_e_o_evento_mais_recente(self):
        topo = listar_ultimas_atualizacoes(self.painel, 1)[0]
        self.assertEqual((topo["id"], topo["dia"]), ("011", 27))


class TestValidacao(unittest.TestCase):
    def test_status_e_categoria_desconhecidos(self):
        problemas = validar_ocorrencia(
            {"id": "050", "categoria": "transito", "descricao": "x", "bairro": "b",
             "local": "l", "dia_abertura": "3", "status": "resolvida"}, {})
        self.assertEqual(len(problemas), 2)

    def test_dia_fora_da_simulacao(self):
        problemas = validar_ocorrencia(
            {"id": "050", "categoria": "limpeza", "descricao": "x", "bairro": "b",
             "local": "l", "dia_abertura": "45", "status": "aberta"}, {})
        self.assertTrue(any("fora da simulação" in problema for problema in problemas))

    def test_recusa_dado_pessoal(self):
        painel = carregar_painel()
        ok, problemas = cadastrar(painel, "limpeza", "Falar com joao@exemplo.com", "Centro", "Praça")
        self.assertFalse(ok)
        ok, problemas = cadastrar(painel, "limpeza", "Tel 11 98765-4321", "Centro", "Praça")
        self.assertFalse(ok)


class TestOperacoes(unittest.TestCase):
    def setUp(self):
        self.painel = carregar_painel()

    def test_cadastro_gera_014_e_entra_na_fila(self):
        ok, nova = cadastrar(self.painel, "Iluminação", "Poste apagado", "Centro", "Praça Central")
        self.assertTrue(ok)
        self.assertEqual(nova["id"], "014")  # 013 já foi usado por um registro recusado
        self.assertEqual(self.painel["fila"][-1], "014")

    def test_busca_e_filtro(self):
        self.assertIsNone(buscar_por_codigo(self.painel, "999"))
        abertas_iluminacao = filtrar(self.painel, categoria="iluminacao", status="aberta")
        self.assertEqual([ocorrencia["id"] for ocorrencia in abertas_iluminacao], ["009"])
        self.assertEqual(len(filtrar(self.painel)), 12)

    def test_transicoes(self):
        self.assertFalse(atualizar_status(self.painel, "004", "concluida")[0])  # pula etapa
        self.assertFalse(atualizar_status(self.painel, "001", "aberta")[0])     # concluída é final
        self.assertFalse(atualizar_status(self.painel, "004", "resolvida")[0])  # status desconhecido
        self.assertFalse(atualizar_status(self.painel, "404", "em_analise")[0])  # não existe
        ok, _ = atualizar_status(self.painel, "004", "Em análise")
        self.assertTrue(ok)
        self.assertNotIn("004", self.painel["fila"])
        self.assertEqual(listar_ultimas_atualizacoes(self.painel, 1)[0]["id"], "004")

    def test_devolver_para_fila(self):
        atualizar_status(self.painel, "003", "aberta", "Faltam fotos do local")
        self.assertEqual(self.painel["fila"][-1], "003")

    def test_examinar_proxima_tira_da_frente(self):
        ok, _ = examinar_proxima(self.painel)
        self.assertTrue(ok)
        self.assertEqual(buscar_por_codigo(self.painel, "004")["status"], "em_analise")
        self.assertEqual(self.painel["fila"][0], "007")


class TestEstruturasEIndicadores(unittest.TestCase):
    def setUp(self):
        self.painel = carregar_painel()

    def test_matriz(self):
        categorias, situacoes, matriz = montar_matriz_categoria_status(self.painel)
        self.assertEqual(sum(sum(linha) for linha in matriz), 12)
        # cada categoria tem 3 ocorrências; cada status também tem 4
        self.assertEqual([sum(linha) for linha in matriz], [3, 3, 3, 3])
        self.assertEqual([sum(linha[j] for linha in matriz) for j in range(3)], [4, 4, 4])

    def test_hierarquia(self):
        arvore = montar_hierarquia(self.painel)
        self.assertEqual(sorted(arvore), ["Centro", "Jardim das Flores", "Vila Nova"])
        self.assertEqual(arvore["Centro"]["acessibilidade"], ["003", "011"])

    def test_indicadores(self):
        resumo = indicadores.resumir_indicadores(self.painel)
        self.assertEqual(resumo["total"], 12)
        self.assertAlmostEqual(resumo["tempo_medio_conclusao"], 7.0)  # (7 + 5 + 4 + 12) / 4
        self.assertEqual(len(resumo["pendentes"]), 8)
        self.assertAlmostEqual(resumo["idade_media_pendentes"], 163 / 8)
        self.assertAlmostEqual(resumo["taxa_resolucao"], 4 / 12 * 100)
        self.assertEqual(transformar_em_porcentagem(1, 0), 0.0)


if __name__ == "__main__":
    unittest.main()
