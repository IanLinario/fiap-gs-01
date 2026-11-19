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

## Revisão e refatoração feitas por mim

Depois da primeira versão, estudei o código função por função, com a IA explicando cada trecho, e mudei o que achei difícil de ler:

- **Nomes de variáveis.** Comecei pelo `indicadores.py`, trocando variáveis de uma letra por nomes que dizem o que guardam (`o` → `ocorrencia`, `r` → `resumo_painel`) e a função `proporcao` por `transformar_em_porcentagem`. Pedi à IA para conferir: ela apontou três problemas que a troca deixou (uma chave `{` apagada numa f-string, um `r` que sobrou e as chamadas a `proporcao` no `sistema.py` e nos testes), que foram corrigidos.
- **Toda função começa com um verbo.** Defini essa regra para o projeto inteiro: `hierarquia` virou `montar_hierarquia`, `media` virou `calcular_media`, `tela_indicadores` virou `mostrar_indicadores`, `acao_cadastrar` virou `executar_cadastro`, e assim por diante. Ficaram de fora só `main` (convenção do Python) e `setUp` (nome exigido pelo `unittest`).
- **Variáveis com nome vago.** Pedi à IA uma lista de candidatas no projeto todo, revisei a proposta e aprovei as trocas: `e` → `evento`, `c` → `caractere`, `l` → `largura`, `de`/`para` → `status_anterior`/`status_novo`, `lista` → `pendentes`, entre outras. Mantive `i` e `j` como índices da matriz.
- **Funções genéricas em `src/utils.py`.** Pedi à IA para mapear as funções usadas em mais de um arquivo. A maioria era a própria regra de negócio do painel (cadastrar, buscar, filtrar), que continua no `painel.py`. Para o `utils.py` foram só as seis que não dependem das ocorrências: `normalizar`, `esta_vazio`, `parece_dado_pessoal`, `ler_csv`, `transformar_em_porcentagem` e `calcular_media`.

Depois de cada mudança, rodei os 15 testes, o `--demo` e todas as opções do menu, e conferi que os números continuavam os mesmos.
