# 02 — Requisitos

Padrão: RFxx (prioridade) — comportamento, usuário, regra, evidência, dependência. Toda evidência é um teste automatizado (pytest).

## Requisitos funcionais

### RF01 (Obrigatório) — Exibir horários livres
- **Comportamento:** exibir ao cliente, na página pública, os horários livres de um barbeiro em uma data, depois de escolhido o serviço; só aparecem horários em que o serviço cabe inteiro antes do próximo agendamento confirmado ou bloqueio.
- **Regra:** blocos livres usam a duração do serviço e consideram só janelas abertas, fora das bloqueadas e sem agendamentos confirmados do barbeiro.
- **Teste:** janela aberta 09:00–10:00 e agendamento confirmado 09:00–09:30 → serviço de 45 min não lista nada; o de 30 min lista 09:30.
- **Depende de:** RF07.

### RF02 (Obrigatório) — Registrar agendamento
- **Comportamento:** gravar o agendamento quando o cliente informa nome, telefone e escolhe um horário livre; mostrar confirmação (serviço, barbeiro, data, hora). Status `confirmado`, origem `link`; telefone já cadastrado reaproveita o cliente.
- **Regra:** telefone validado (DDD + 10 ou 11 dígitos); `fim` = início + duração; a gravação revalida sobreposição **na mesma transação** e rejeita horário ocupado.
- **Teste:** duas requisições simultâneas ao mesmo horário/barbeiro → um confirmado e uma recusa; mesmo telefone em dois agendamentos → um único cliente.
- **Depende de:** RF01.

### RF03 (Obrigatório) — Sugerir outro barbeiro
- **Comportamento:** sugerir horários livres de outros barbeiros ativos, para o mesmo serviço e data, quando o escolhido não tem vaga; o cliente pode confirmar no mesmo fluxo.
- **Regra:** só barbeiros ativos com janela aberta e bloco compatível com a duração; a sugestão é opcional.
- **Teste:** barbeiro A lotado e B livre → consulta a A devolve horários de B; sem ninguém livre → lista vazia.
- **Depende de:** RF01, RF02.

### RF04 (Obrigatório) — Lista de espera
- **Comportamento:** incluir o cliente na lista de espera quando não há horário livre para o serviço e a data e ele opta por aguardar; status `aguardando`, com data/hora de entrada.
- **Regra:** informa nome, telefone, serviço, data desejada e, opcional, barbeiro preferido; **sem segunda entrada `aguardando`** do mesmo cliente para o mesmo serviço e data.
- **Teste:** 1ª entrada gravada; 2ª igual recusada com mensagem de duplicidade.
- **Depende de:** RF01.

### RF05 (Obrigatório) — Cancelar e indicar próximo da lista
- **Comportamento:** o barbeiro autenticado cancela um agendamento e o painel indica o próximo cliente compatível da lista de espera. O agendamento passa a `cancelado` (não é excluído); o cliente indicado passa a `chamado`.
- **Regra:** compatível = `aguardando` para o mesmo serviço, data e, se informado, barbeiro, que caiba no horário liberado; ordem por `entrou_em`.
- **Teste:** com 3 entradas aguardando, exibe a de menor `entrou_em` que caiba; agendamento segue no banco como `cancelado`.
- **Depende de:** RF02, RF04, RF08.

### RF06 (Obrigatório) — Agenda do dia e da semana
- **Comportamento:** exibir ao barbeiro autenticado horário, cliente, telefone e serviço dos agendamentos confirmados do dia e da semana.
- **Regra:** barbeiro comum vê só a própria agenda; administrador escolhe qualquer barbeiro; cancelados não aparecem na lista principal.
- **Teste:** 5 confirmados e 1 cancelado → agenda do dia mostra os confirmados do barbeiro logado, ordenados por horário.
- **Depende de:** RF02, RF08.

### RF07 (Obrigatório) — Janelas de atendimento
- **Comportamento:** o barbeiro autenticado cria, altera e exclui janelas abertas ou bloqueadas para um dia (limita horários por dia, bloqueia pausas e folgas).
- **Regra:** `hora_fim > hora_inicio`; janelas do mesmo barbeiro, dia e tipo não se sobrepõem; não se exclui janela com agendamento confirmado dentro dela.
- **Teste:** janela 09:00–12:00 aparece no RF01; sobreposta é recusada; exclusão com agendamento confirmado é bloqueada.
- **Depende de:** RF08.

### RF08 (Obrigatório) — Login do painel
- **Comportamento:** exigir login (e-mail e senha) para o painel e encerrar a sessão ao sair.
- **Regra:** só barbeiros ativos entram; só o administrador cadastra barbeiros e altera serviços; credenciais inválidas → mensagem única, sem dizer se errou e-mail ou senha.
- **Teste:** rota do painel sem sessão redireciona para a entrada; login válido libera; barbeiro inativo é recusado.
- **Depende de:** nenhuma.

### RF09 (Desejável) — Botão WhatsApp com mensagem pronta
- **Comportamento:** botão no painel que abre o WhatsApp (`wa.me/55<telefone>`) com mensagem pronta (nome, serviço, data e hora) para o cliente chamado.
- **Regra:** o envio é feito pelo barbeiro, sem integração por API.
- **Teste:** link gerado no formato `wa.me/55…` com texto codificado contendo nome, serviço e horário.
- **Depende de:** RF05.

### RF10 (Desejável) — Totais para o administrador
- **Comportamento:** exibir contagem de agendamentos pelo link, entradas na lista de espera e chamados que agendaram, em um período.
- **Regra:** usa dados já gravados; sem entidade nova; sem dados pessoais nos totais.
- **Teste:** totais exibidos = contagem direta no banco com dados de teste.
- **Depende de:** RF02, RF04, RF05.

### Ordem recomendada
RF08 → RF07 → RF01 → RF02 → RF03 → RF04 → RF06 → RF05 → RF09 → RF10.

## Requisitos não funcionais

### RNF01 (Obrigatório) — Autenticação e acesso
- Perfis: barbeiro e administrador (`barbeiro.papel`). Exigem login: agenda, cancelamento, janelas, lista de espera; só administrador: cadastro de barbeiros e alteração de serviços. A página pública não exige login.
- Senha definida pelo administrador no cadastro, mínimo 10 caracteres, validada no servidor; trafega por POST sobre HTTPS; não vai em URL nem em log.
- Armazenamento: **somente hash scrypt** com salt (`generate_password_hash` do Werkzeug) em `barbeiro.senha_hash`. Proibido texto limpo, MD5 e SHA-1. Hash é mão única; criptografia reversível não é usada.
- Sessão: Flask-Login; cookie HttpOnly, Secure, SameSite=Lax; expira em 8 h; invalidado no logout; `SECRET_KEY` em variável de ambiente.
- Tentativas: bloqueio de 15 min após 5 falhas seguidas para o mesmo e-mail; contador em memória (1 processo Gunicorn); mensagem única.
- **Verificação:** (1) inspeção do banco sem senha legível, só prefixo scrypt; (2) login válido e inválido; (3) 6ª tentativa errada bloqueada mesmo com senha correta; (4) rota do painel sem login redireciona, barbeiro comum recebe 403 ao cadastrar barbeiro; (5) após logout, rota protegida redireciona.

### RNF02 (Obrigatório) — OWASP e proteção de dados
- Validação no cliente só orienta; a que vale é no servidor (Flask-WTF): nome até 100, telefone DDD + 10/11 dígitos, data válida, serviço e barbeiro existentes.
- Consultas só via SQLAlchemy ORM com parâmetros.
- Escape automático do Jinja2; sem `|safe` em dado do usuário; CSP `default-src 'self'`; token CSRF em todo formulário que altera dados.
- Autorização em cada rota protegida (perfil e dono do registro).
- Erros genéricos, sem rastreio, caminho de arquivo ou SQL; detalhes só no log do servidor, sem senhas nem telefones completos.
- Minimização: só nome e telefone do cliente; telefone só no painel autenticado; página pública nunca mostra dados de outros clientes.
- Segredos fora do repositório; debug desligado; só HTTPS; dependências fixadas e verificadas com `pip-audit`.
- **Aceitação:** 100% das rotas do painel sem login redirecionam; entradas de injeção de SQL/script não alteram registros nem executam; página pública sem telefone; erro 500 forçado sem rastreio; repositório sem segredos; `pip-audit` sem vulnerabilidade alta/crítica.

### Ameaças priorizadas (referência OWASP 2025 / 2021)
| Ameaça | OWASP | Controle principal | Teste |
|---|---|---|---|
| Acesso indevido a dados/funções do painel | A01 Broken Access Control | login em todas as rotas; checar `barbeiro_id` e papel no servidor; página pública sem dados de clientes | sem login → 302; barbeiro A em registro de B → 403/404 |
| Injeção de SQL | A05:2025 Injection (A03:2021) | ORM parametrizado; validação Flask-WTF | `' OR 1=1 --` sem alterar registros |
| XSS pelo nome do cliente | A05:2025 Injection – XSS | escape Jinja2; validação; CSP | `<script>` recusado ou escapado |
| Força bruta e sessão | A07:2025 Authentication Failures | hash scrypt; bloqueio 5 falhas/15 min; cookie seguro | 6ª tentativa bloqueada |
| CSRF | A01 (CWE-352) | token Flask-WTF; só POST; SameSite=Lax | POST sem token → 400 |
| Configuração insegura/segredos | A02:2025 / A03:2025 | debug off; segredos em env; erros genéricos; pip-audit | erro 500 sem rastreio; repositório sem segredos |
> A numeração OWASP 2025 foi inserida sem conferência em fonte; confirmar em owasp.org/Top10.

### RNF03 (Obrigatório) — Hospedagem, portabilidade e desempenho
- Hospedagem: plataforma de nuvem com plano gratuito e HTTPS; Gunicorn 1 processo + 4 threads; PostgreSQL 16 gerenciado; SQLite no dev.
- Ambientes: dev em Windows, Linux e macOS com Python 3.12; navegadores: duas últimas versões de Chrome, Safari, Firefox e Edge.
- Reprodução: README com 4 passos (venv, instalar, variáveis de ambiente, `scripts/criar_banco.py` repetível e sem duplicar dados). Fora do código: `SECRET_KEY`, `DATABASE_URL`, `FLASK_DEBUG`.
- Limites do plano gratuito: pode suspender por inatividade, limitar armazenamento/tráfego/banco. Aceitável se: partida a frio ≤ 10 s medida à parte; `pg_dump` semanal e antes da entrega; armazenamento abaixo do limite.
- **Meta:** página de horários livres carrega em ≤ 3 s (load e LCP) no Lighthouse mobile (Slow 4G ≈ 1,6 Mbps/150 ms, CPU 4x), ≤ 300 KB. Dados de teste: 3 barbeiros, 7 serviços, 200 clientes, 500 agendamentos, 30 dias de janelas. 1 aquecimento + 5 medições, mediana. Conferência em celular real na rede local.
- Se falhar, nesta ordem: gzip, reduzir/remover imagens, índices em `agendamento(barbeiro_id, inicio)` e `janela_atendimento(barbeiro_id, data)`, reduzir JS, cache de estáticos, paginar listas.

### RNF04 (Obrigatório) — Acessibilidade
1. Toque ≥ 44×44 px em botões de serviço, barbeiro, horário, confirmar e cancelar, com 8 px de espaço.
2. Contraste ≥ 4,5:1 (texto) e 3:1 (bordas/componentes).
3. Todo campo com rótulo visível e associado; placeholder não substitui rótulo.
4. Erros em texto junto ao campo, com problema e correção (ex.: "Telefone incompleto. Informe DDD e número, como 51 90000-0000"), ícone + texto, `aria-live`.
5. Estado do horário (livre/selecionado) em texto, não só cor.
6. Teclado completo, ordem de foco lógica, foco visível com contorno ≥ 2 px.
7. Texto a 200% sem perda de conteúdo e sem rolagem horizontal em 360 px.
8. Sem CAPTCHA e sem limite de tempo no formulário público.
- **Aplica-se a:** escolha de serviço/barbeiro, horários e dados, resultado e login do painel.
- **Verificação:** Lighthouse Acessibilidade ≥ 90 por tela; axe DevTools sem erros críticos/sérios; 100% dos botões ≥ 44 px no DevTools; verificador de contraste; teste só com teclado e zoom 200%; TalkBack; cliente-base conclui o agendamento no celular sem ajuda.
- **Vínculo ODS 8:** cliente excluído por barreira de interface vira receita perdida; ampliar quem conclui o fluxo amplia a demanda convertida em atendimentos. Limite: não resolve exclusão digital (falta de celular/internet) nem equivale a certificação.
