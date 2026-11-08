# 06 — Plano de implementação

Projeto: 24/10/2026 a 17/11/2026. Diagnóstico e linha de base concluídos. Datas abaixo são a proposta a partir de 03/11; ajustar conforme o andamento.

| Etapa | Período | Entrega |
|---|---|---|
| 1. Base e telas estáticas | 03–04/11 | Projeto Flask, `requirements.txt`, templates das 4 telas com textos e botões de 44 px; capturas do protótipo |
| 2. Modelos e regras | 05–08/11 | Entidades SQLAlchemy, `scripts/criar_banco.py`, serviços de horários livres e sobreposição; **testes primeiro** (RF01, RF02) |
| 3. Fluxo do cliente | 09–12/11 | Rotas e formulários (Flask-WTF), sugestão de outro barbeiro (RF03), dois tipos de fila com `hora_desejada` (RF04) e regra de chamada (RF05) em `app/services` |
| 4. Painel | 12–14/11 | Login (RF08), janelas (RF07), agenda do dia (RF06); cancelamento e próximo da fila (RF05) só se sobrar tempo |
| 5. Validação e medições | 15–16/11 | Teste com o cliente-base, Lighthouse/axe, medições do RNF03, correções |
| 6. Entrega | 17/11 | Deploy, README final, backup `pg_dump` |

Desejáveis (RF09, RF10) ficam fora desta entrega. RF05 (tela de cancelamento) é condicional; a regra de chamada da fila é implementada e testada de qualquer forma.

## Ordem de implementação dos requisitos
RF08 → RF07 → RF01 → RF02 → RF03 → RF04 → RF06 → RF05 → RF09 → RF10.

## Critérios de pronto por tarefa
Teste do requisito passando; `pytest --cov=app/services` ≥ 80% nas regras de horário; sem segredo no código; textos conforme `05-telas.md`; checagem de acessibilidade da tela alterada.

## Validação com o representante externo
Um único cliente-base. Plano ainda a definir na etapa "Protótipo e plano de validação" da plataforma: ao menos 3 tarefas observáveis (ex.: agendar um serviço; agendar com outro barbeiro quando o escolhido está lotado; entrar na lista de espera) e critérios metrificados de usabilidade, eficiência e satisfação.

## Decisões do MVP (08/11/2026)
- `hora_desejada` é hora obrigatória, comparada por igualdade com o início do horário liberado.
- Chamada da fila: primeiro a fila do barbeiro (mesmo serviço, data e hora, serviço cabe no bloco), depois a fila por horário; dentro de cada uma, por `entrou_em`. O painel indica um cliente por vez.
- Limite de horários por dia: só as janelas abertas (RF07); sem campo nem teto novo.
- Painel da entrega: RF08, RF07 e RF06. RF05 (tela) só se sobrar tempo.
- RF05 entrou nesta entrega (08/11/2026), com "Chamar o próximo" (chamado → `desistiu`).

## Evolução futura (registrada em 08/11/2026)
- Marcar a entrada da fila como `atendido` quando o cliente chamado agenda (exige agendar pelo painel, origem `painel`, ou ligar o agendamento do link à entrada).
- Reservar o horário liberado para o cliente chamado; hoje ele volta ao link público e outra pessoa pode agendar antes.

## Pendências e hipóteses abertas
- Familiaridade digital do público e uso de ampliação de texto: hipóteses, confirmar na validação.
- Lista vertical vs. grade para os horários: confirmar com o cliente-base. (A sugestão de outro barbeiro é escolha do cliente.)
- Numeração OWASP 2025 em `02-requisitos.md`: conferir em owasp.org/Top10.
- Versões exatas das dependências: confirmar ao instalar.
- Linha de base de clientes sem horário no sábado: não levantada.
