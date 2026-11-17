# Uso de inteligência artificial

O projeto foi desenvolvido com apoio do **Claude** (Anthropic), usado como assistente de programação.

## Como a IA ajudou

- **Dados fictícios:** sugeriu as 12 ocorrências, os três bairros e os eventos de histórico, além dos dois registros inconsistentes de propósito (sem categoria e com código repetido).
- **Código:** escreveu a primeira versão de `painel.py`, `indicadores.py` e `sistema.py` a partir dos requisitos do enunciado.
- **Testes e documentação:** escreveu os testes automáticos e o rascunho deste README.

## Como o resultado foi verificado

- Os 15 testes automáticos (`python -m unittest discover -s tests`) passam e conferem os números à mão: o tempo médio de conclusão (7 + 5 + 4 + 12) / 4 = 7,0 dias, a idade média das pendências 163 / 8 ≈ 20,4 dias e os totais da matriz.
- O roteiro `python src/sistema.py --demo` foi executado e cada saída foi comparada com o que as regras do README dizem que deveria acontecer.
- Cada regra de validação e de transição de status foi testada com uma entrada inválida, para ver a mensagem de erro.
- O código usa só os conteúdos das fases 1 a 3 (listas, dicionários, fila, pilha, matriz, condicionais, laços, funções e leitura de arquivo).

<!-- TODO: completar com o que você revisou, mudou ou aprendeu ao estudar o código. -->
