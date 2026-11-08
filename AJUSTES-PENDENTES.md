# Ajustes pendentes nos documentos

O protótipo (02/11/2026) passou a seguir um fluxo novo: o cliente escolhe serviço, data e horário e só depois o barbeiro, e há dois tipos de fila de espera. A pasta `docs/` **não foi alterada**. Abaixo está o que precisa ser atualizado nela antes de implementar as regras e o banco.

## docs/02-requisitos.md

- **RF01, exibir horários livres:** a consulta passa a ser por **serviço, data e horário**, e devolve os barbeiros livres naquele horário. Hoje o texto diz "horários livres de um barbeiro em uma data". O teste de aceitação precisa ser revisto.
- **RF03, sugerir outro barbeiro:** passa a ser "sugerir os barbeiros livres **no mesmo horário**" quando o barbeiro escolhido não está livre. Com "Qualquer barbeiro", a tela já lista os livres. A sugestão continua opcional, porque o cliente pode entrar na fila do barbeiro escolhido.
- **RF04, lista de espera:** passa a ter **dois tipos de fila**:
  - **fila por horário e barbeiro** (`fila_barbeiro`): o cliente quer aquele barbeiro naquele horário;
  - **fila por horário** (`fila_horario`): o cliente aceita qualquer barbeiro naquele horário.
  
  A regra de duplicidade passa a considerar também a hora e o barbeiro. Revisar o texto e o teste.
- **RF05, cancelar e indicar o próximo:** nova regra de chamada. Quando um horário é liberado, chama-se primeiro a **fila do barbeiro específico** (barbeiro e horário liberados) e, se ela estiver vazia, a **fila por horário**. Dentro de cada fila, a ordem é sempre por `entrou_em`.
- **RNF04:** "Escolha o horário" entra na lista de componentes com área de toque de 44 px.

## docs/03-modelo-dados.md

- **lista_espera:** novo campo **`hora_desejada`** (hora, obrigatória).
- **lista_espera.barbeiro_id:** deixa de ser só uma "preferência opcional" e passa a definir o tipo de fila:
  - `barbeiro_id` preenchido = fila do barbeiro;
  - `barbeiro_id` **nulo** = fila por horário.
- **Unicidade:** sem duas entradas `aguardando` do mesmo cliente, serviço, data, hora e barbeiro (o nulo conta como valor).
- **Fluxo de dados (CRUD), passo 1:** passa a ler os barbeiros livres em um horário, não os horários de um barbeiro.
- **Índice sugerido:** `lista_espera(data_desejada, hora_desejada, status)`.

## docs/05-telas.md

O documento passa de 3 para **4 telas**:
1. **Tela 1, escolha:** serviço, data (padrão 14/11/2026, aplicada ao escolher, sem botão), horário e barbeiro ("Qualquer barbeiro" como padrão). O botão "Ver disponibilidade" fica desabilitado até serviço, data e horário estarem escolhidos.
2. **Tela 2, disponibilidade:** casos a (barbeiro livre), b (barbeiro ocupado: fila do barbeiro ou outros livres), c (qualquer barbeiro, com livres) e d (ninguém livre: fila por horário).
3. **Tela 3, seus dados:** nome e telefone; o resumo mostra "Fila de espera" nos modos de fila.
4. **Tela 4, resultado:** confirmado, fila_horario e fila_barbeiro.

Outros pontos a atualizar no mesmo documento:
- Rótulos: sai "Entrar na lista de espera" e entram "Entrar na fila de espera", "Ver disponibilidade", "Qualquer barbeiro", "Escolha a data" e "Escolha o horário".
- Padrão do nome de serviço em todas as telas: "Corte – 30 min" (inclusive no resumo, onde hoje está "Corte + barba (45 min)").
- Textos que o protótipo criou e que precisam ser aprovados:
  - "Selecione serviço, data e horário para continuar" (texto de apoio da Tela 1);
  - "Escolha o barbeiro" como título do caso c;
  - "Informe seu nome." (erro do campo Nome);
  - "Página não encontrada." e "Requisição inválida. Tente novamente." (páginas de erro).
- A hipótese "sugestão escolhida pelo cliente × troca automática" fica resolvida: é escolha do cliente (caso b, botão "Ver outros barbeiros livres").

## docs/04-arquitetura.md

- O protótipo usa um JavaScript pontual (`static/js/tela1.js`) para aplicar a data ao escolher. Registrar isso na linha "HTML5, CSS3, JS pontual".

## docs/06-plano.md

- Etapa 1 (telas estáticas): passa de 3 para 4 telas.
- Etapa 3 (fluxo do cliente): incluir os dois tipos de fila (RF04) e a ordem de chamada (RF05).

## Código (quando sair do protótipo)

- A checagem do modo em `app/web/rotas.py` (`_modo_coerente`, que confere confirmação ou fila contra a disponibilidade) e a lista de barbeiros livres (`_livres`) são regras de negócio. Elas devem ir para `app/services/` com testes unitários e ler o banco pelos repositórios.
- A disponibilidade de demonstração ignora a data e a duração do serviço. A regra real (RF01) precisa considerar as duas.
