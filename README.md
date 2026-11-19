# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href="https://www.fiap.com.br/">
  <img src="https://raw.githubusercontent.com/equipe1ccon/FIAP-PORTFOLIO-1CCON/master/assets/logo-fiap.png" 
       alt="FIAP - Faculdade de Informática e Administração Paulista" 
       width="40%">
</a>
</p>

<br>

# Neighborhood Action Dashboard

## Grupo 20

## 👨‍🎓 Integrantes: 
- <a href="https://github.com/IanLinario">Ian Marrafon Linário Leal</a> – RM576816

## 👩‍🏫 Professores:

### Tutor(a)
- <a href="https://www.linkedin.com/in/andretritiack/">André Tritiack de Farias</a>
  
### Coordenador(a)
- <a href="https://www.linkedin.com/in/andregodoichiovato/">André Godoi Chiovato</a>

## 📜 Descrição

Global Solution da Fase 4 (desafio **CitizenTech**). O **Neighborhood Action Dashboard** é um painel comunitário em terminal para registrar, organizar e acompanhar demandas de melhoria de bairro: iluminação, acessibilidade, limpeza e conservação de espaços coletivos.

### A comunidade simulada

Uma região fictícia com três bairros: **Centro** (praça, biblioteca, avenida e escola), **Vila Nova** (posto de saúde, quadra poliesportiva e mercado) e **Jardim das Flores** (parque, coreto e horta comunitária).

- **Problema:** os relatos de moradores ficam espalhados, ninguém sabe o que já foi visto, o que está parado e o que é mais urgente.
- **Público beneficiado:** moradores, que acompanham suas solicitações, e a associação de bairro, que enxerga onde estão os problemas e quanto tempo eles levam para ser resolvidos.
- **Limite:** é um protótipo com dados inventados. Não se conecta a prefeitura nem promete atendimento.

### Os dados

Ficam em CSV com `;` como separador (assim as descrições podem ter vírgula) e são lidos com o módulo `csv` da biblioteca padrão.

**`data/ocorrencias.csv`**: 14 linhas, das quais 12 são válidas e 2 têm problema de propósito.

| Campo | Significado | Exemplo |
|---|---|---|
| `id` | Código único de três dígitos | `014` |
| `categoria` | `iluminacao`, `acessibilidade`, `limpeza` ou `conservacao` | `iluminacao` |
| `descricao` | Descrição breve, sem dado pessoal | `Poste apagado na esquina` |
| `bairro` | Bairro da comunidade simulada | `Centro` |
| `local` | Local genérico, nunca um endereço com número | `Praça Central` |
| `dia_abertura` | Dia simulado de abertura, de 1 a 30 (hoje é o dia 30) | `2` |
| `status` | `aberta`, `em_analise` ou `concluida` | `aberta` |

Todos os campos são obrigatórios. Usamos **dias simulados** em vez de datas reais: a conta de tempo fica uma subtração simples e ninguém confunde o protótipo com um registro real.

**`data/historico.csv`**: 12 eventos de acompanhamento (`id;dia;de;para;nota`), cada um uma mudança de status.

### Situações (status)

| Status | Significado | Pode ir para |
|---|---|---|
| **Aberta** | Registrada pela comunidade e ainda não examinada; espera na fila | Em análise |
| **Em análise** | Alguém examinou a demanda e o encaminhamento está em andamento | Concluída, ou Aberta (devolvida por falta de informação) |
| **Concluída** | O problema foi resolvido; o registro não muda mais | — |

Não dá para pular de Aberta para Concluída: toda demanda passa por análise.

## 🧱 Estruturas de dados e por que cada uma

| Estrutura | Onde | Para quê | Por que ela |
|---|---|---|---|
| **Lista** | `painel["ocorrencias"]` | Guarda todas as ocorrências válidas na ordem de registro; é o que a listagem, os filtros e os indicadores percorrem | Percorrer tudo em ordem é exatamente o que essas operações fazem |
| **Dicionário** | `painel["indice"]` (`{código: ocorrência}`) | Buscar, validar duplicados e atualizar pelo código | Acesso direto pela chave, sem varrer a lista inteira |
| **Fila** | `painel["fila"]` (`collections.deque`) | Demandas **Aberta** ainda não examinadas, da mais antiga para a mais nova; a opção 6 tira sempre a da frente | Primeiro a entrar, primeiro a sair: é justo atender quem espera há mais tempo. O `deque` tira da frente sem deslocar os outros itens, como faria `list.pop(0)` |
| **Pilha** | `painel["pilha"]` | Cada mudança de status é empilhada; a opção 7 lê do topo para baixo | Último a entrar, primeiro a sair: o topo é sempre o evento mais recente |
| **Hierarquia** | `montar_hierarquia()`: `{bairro: {categoria: [códigos]}}` | Mostra a comunidade como bairro → categoria → ocorrências | Responde "o que está acontecendo no meu bairro?" e mostra onde cada tipo de problema se concentra |
| **Matriz** | `montar_matriz_categoria_status()`: lista de listas 4 × 3 | Linha = categoria, coluna = status, célula = quantidade | Os totais por categoria são as somas das linhas e os totais por status, as somas das colunas; é a origem dos indicadores |

## 🔀 Regras lógicas

### Validação do cadastro (`validar_ocorrencia`)

Um registro só entra na lista se passar por todas as regras. Se falhar, ele é **recusado com o motivo** e fica fora da listagem e dos indicadores (opção 10 do menu):

| Regra | Condição | Mensagem |
|---|---|---|
| Campo obrigatório | `esta_vazio(campo)` para qualquer campo | `campo obrigatório 'categoria' ausente` |
| Código único | `not esta_vazio(codigo) and codigo in codigos_usados` | `código 007 repetido` |
| Categoria padronizada | `not esta_vazio(categoria) and categoria not in CATEGORIAS` | `categoria desconhecida` |
| Status padronizado | `not esta_vazio(status) and status not in STATUS` | `status desconhecido` |
| Dia válido | `int(dia) < 1 or int(dia) > DIA_ATUAL` | `dia de abertura fora da simulação` |
| Privacidade | `"@" in texto or maior_sequencia_de_digitos >= 8` | `o texto parece conter dado pessoal` |

No arquivo de exemplo, a linha do código **013** não tem categoria e a segunda linha com código **007** repete um código. Os dois casos são detectados ao carregar. O código 013 continua "gasto", então o próximo cadastro recebe **014** e nenhum código se repete.

### Expressão booleana documentada: o filtro

```python
(categoria is None or ocorrencia["categoria"] == categoria) and (status is None or ocorrencia["status"] == status)
```

- Cada parêntese diz "não há filtro **OU** o valor bate". Quando a pessoa deixa a categoria em branco (`None`), o primeiro lado do `or` já é verdadeiro e todas as categorias passam.
- O `and` exige que os dois critérios valham ao mesmo tempo. Com categoria = iluminação e status = aberta, só passa quem é das duas coisas.

### Atualização de status (`atualizar_status`)

```python
if novo not in STATUS:              -> "Status 'resolvida' desconhecido. Use: ..."
elif novo == atual:                 -> "A ocorrência já está 'Aberta'."
elif not (novo in TRANSICOES[atual]):
    if atual == "concluida":        -> "Ocorrência concluída não muda mais."
    else:                           -> "Não é possível ir de 'Aberta' para 'Concluída'. Permitido: Em análise."
else:                               -> muda, tira/põe na fila, empilha o evento no histórico
```

Antes disso, se o código não existe, a resposta é `Ocorrência 099 não encontrada.`. A ordem importa: primeiro se verifica se o pedido faz sentido (o status existe?), depois se ele muda alguma coisa, e só então se a transição é permitida. Assim cada erro recebe a mensagem que explica o problema real.

### Onde aparecem AND, OR e NOT

1. **Filtro** (acima): `or` dentro de cada critério e `and` entre eles.
2. **Validação de código único e de categoria/status**: `not esta_vazio(x) and x not in ...`. Um campo vazio já gera a mensagem "ausente", e o `not esta_vazio` evita repetir o erro como "desconhecido".
3. **Privacidade**: `"@" in texto or maior >= 8`. Basta um sinal de e-mail ou de telefone/CPF para recusar.
4. **Transição**: `not (novo in TRANSICOES[atual])`.
5. **Pendências**: `not (ocorrencia["status"] == "concluida")`.

## 📊 Indicadores

O painel (opção 9) mostra a matriz de origem, a fórmula de cada indicador e o resultado. Com os 12 registros do arquivo:

| Indicador | Fórmula | Resultado |
|---|---|---|
| Total por categoria | soma da linha da matriz | 3 em cada uma das 4 categorias |
| Proporção por categoria | categoria / total × 100 | 25% cada |
| Total por status | soma da coluna da matriz | 4 abertas, 4 em análise, 4 concluídas |
| Taxa de resolução | concluídas / total × 100 | 33,3% |
| Tempo médio até a conclusão | Σ(dia da conclusão − dia de abertura) / concluídas | (7 + 5 + 4 + 12) / 4 = **7,0 dias** |
| Pendências e idade média | não concluídas; Σ(30 − dia de abertura) / pendências | 8 pendências, **20,4 dias** em média |

O dia da conclusão sai do histórico: é o dia do último evento que leva a ocorrência para Concluída.

**Interpretação.** As demandas estão bem distribuídas entre as categorias, então nenhum tipo de problema domina. O alerta está no tempo: o que foi resolvido levou 7 dias em média, mas o que continua pendente já espera 20 dias, quase o triplo. Ou seja, a comunidade não registra mais do que antes; o encaminhamento é que parou. Quatro demandas estão "em análise" há mais de 15 dias (a 003, rampa da biblioteca, há 26), e é por elas que a associação deveria começar a cobrar. Acessibilidade merece atenção à parte: as três ocorrências afetam diretamente quem tem deficiência visual ou usa cadeira de rodas, e só a do semáforo sonoro foi resolvida. A rampa (003) está em análise há 26 dias e o piso tátil (007) nem saiu da fila.

## 🖥️ Exemplo de uso

`python src/sistema.py --demo` roda o roteiro do exemplo do enunciado sem precisar digitar nada. Trechos da saída:

```
REGISTROS COM PROBLEMA (REGRAS DE VALIDAÇÃO)
Linha 14 do CSV (código 013): NÃO cadastrada
  - campo obrigatório 'categoria' ausente
Linha 15 do CSV (código 007): NÃO cadastrada
  - código 007 repetido (já existe outra ocorrência com ele)

AÇÃO 1: CADASTRAR UMA NOVA DEMANDA
Tentativa sem categoria:
  - recusada: campo obrigatório 'categoria' ausente
Tentativa com telefone na descrição:
  - recusada: o texto parece conter dado pessoal (e-mail ou telefone)
Tentativa correta:
  Cadastrada como 014 (status Aberta, entrou no fim da fila).

CONSULTA: OCORRÊNCIAS ABERTAS DE ILUMINAÇÃO
Código | Categoria  | Bairro    | Local                | Abertura | Status
-------+------------+-----------+----------------------+----------+-------
009    | Iluminação | Vila Nova | Quadra poliesportiva | dia 12   | Aberta
014    | Iluminação | Centro    | Praça Central        | dia 30   | Aberta

AÇÃO 2: ALTERAR A 014 PARA 'EM ANÁLISE'
Tentativa inválida (pular direto para concluída):
  Não é possível ir de 'Aberta' para 'Concluída'. Permitido: Em análise.
Tentativa válida:
  Ocorrência 014: 'Aberta' -> 'Em análise' (dia 30).
Código que não existe:
  Ocorrência 099 não encontrada.

FILA: EXAMINAR A DEMANDA ABERTA MAIS ANTIGA
Fila antes: 004, 007, 009, 012
Ocorrência 004: 'Aberta' -> 'Em análise' (dia 30).
Fila depois: 007, 009, 012

PAINEL DE INDICADORES (DIA 30 DA SIMULAÇÃO)
Categoria      | Aberta | Em análise | Concluída | Total
---------------+--------+------------+-----------+------
Iluminação     | 1      | 2          | 1         | 4
Acessibilidade | 1      | 1          | 1         | 3
Limpeza        | 0      | 1          | 2         | 3
Conservação    | 1      | 2          | 0         | 3
TOTAL          | 3      | 6          | 4         | 13
```

No menu interativo, as mesmas operações estão nas opções 2 (buscar), 3 (filtrar), 4 (cadastrar), 5 (atualizar status) e 9 (indicadores).

## ♿ Acessibilidade, inclusão e privacidade

- **Só texto, sem depender de cor**: tudo é escrito por extenso, então funciona em qualquer terminal e com leitor de tela. As tabelas usam colunas alinhadas e cabeçalho.
- **Entrada tolerante**: as opções são escolhidas pelo número ou pelo nome, com ou sem acento e em qualquer caixa (`Em Análise`, `em analise` e `2` dão no mesmo). Códigos aceitam `7` ou `007`.
- **Mensagens que explicam**: todo erro diz o que estava errado e o que é permitido, em vez de só "inválido".
- **Privacidade por padrão**: não há campo de nome, telefone ou endereço. O local é genérico ("Praça Central") e a validação recusa descrições com e-mail ou sequências longas de dígitos.
- **Inclusão no conteúdo**: a categoria Acessibilidade existe para que piso tátil, rampa e semáforo sonoro tenham o mesmo peso de um poste apagado.

## 📁 Estrutura de pastas

```
fiap-gs-01/
├── data/
│   ├── ocorrencias.csv   # 14 registros (12 válidos + 2 inconsistentes de propósito)
│   └── historico.csv     # 12 eventos de mudança de status
├── docs/
│   ├── atividade.md      # enunciado copiado do FIAP ON
│   └── uso_ia.md         # como a IA foi usada e como o resultado foi verificado
├── src/
│   ├── sistema.py        # interface textual (menu e --demo)
│   ├── painel.py         # carga, validação, estruturas, consultas e atualizações
│   ├── indicadores.py    # contagens, proporções, tempos e interpretação
│   └── utils.py          # funções genéricas: texto, leitura de CSV, porcentagem e média
├── tests/
│   └── test_sistema.py   # 15 testes automáticos
└── README.md
```

## 🔧 Como executar o código

Só precisa do **Python 3.8 ou mais novo**. Não há bibliotecas para instalar: tudo vem da biblioteca padrão (`csv`, `os`, `sys`, `unicodedata`, `collections`).

```bash
git clone https://github.com/IanLinario/fiap-gs-01.git
cd fiap-gs-01
python src/sistema.py           # menu interativo
python src/sistema.py --demo    # roteiro de demonstração, sem digitar nada
python -m unittest discover -s tests   # testes
```

As alterações feitas durante a execução ficam só na memória; os arquivos CSV não são modificados.

## 📎 Links e Observações

### 🔗 Links do Projeto

* **[Vídeo de apresentação no YouTube](TODO_LINK_VIDEO)** - Demonstração do sistema em funcionamento (não listado).

### 🧠 Decisões Técnicas

- **Python puro**, como pedem as regras técnicas: nada de pandas, banco de dados ou framework.
- **CSV com `;`** para os dados e o histórico, para que a pessoa avaliadora consiga abrir e editar os dados num editor de texto ou planilha.
- **Dias simulados** (1 a 30) em vez de datas: as contas de tempo são subtrações simples e o protótipo não parece um registro real.
- **Registros inválidos são recusados, não corrigidos.** Adivinhar a categoria de uma ocorrência sem categoria poderia esconder um erro; o sistema mostra o problema e a linha do CSV para alguém corrigir.
- **Transições de status num dicionário** (`TRANSICOES`). A regra de quem pode ir para onde fica num lugar só e a mensagem de erro é montada a partir dela.
- **Código dividido em quatro arquivos**: `painel.py` (dados e regras), `indicadores.py` (contas), `sistema.py` (tela) e `utils.py` (funções genéricas, como normalizar texto, ler CSV e calcular porcentagem e média, que não dependem das regras do painel e são usadas pelos outros três). Os testes usam o painel e os indicadores sem passar pelo menu.

### 📢 Observações Gerais

* **Participação na Competição:** [ ] Sim, aceitamos participar / [ ] Não vamos participar.

## 🧭 Conclusões, limitações e aprendizados

- **Conclusões:** com estruturas simples já dá para transformar relatos soltos em informação útil. A fila mostra quem espera há mais tempo, a pilha conta o que acabou de acontecer, e a matriz junto com o tempo médio mostra que o gargalo está no encaminhamento das demandas, não na quantidade delas.
- **Limitações:** os dados são inventados e poucos (12 registros), então as proporções servem para mostrar o método, não para tirar conclusões sobre um bairro real. O sistema não grava as alterações no CSV, não tem usuários nem permissões (qualquer um pode mudar um status) e não confirma se um problema foi de fato resolvido.
- **Aprendizados:** escolher a estrutura pelo uso (lista para percorrer, dicionário para achar, fila para ordem de chegada, pilha para o mais recente) deixou cada função curta. Validar na entrada, e explicar o motivo da recusa, saiu mais simples do que tratar dado ruim depois, no meio dos cálculos.

---

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/fiap-tutoria/FIAP-PORTFOLIO-AI">TEMPLATE - FIAP PORTFÓLIO AI</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">FIAP</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>
