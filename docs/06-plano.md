# 06 — Plano de implementação

Projeto: 24/10/2026 a 17/11/2026. Diagnóstico e linha de base concluídos. Datas abaixo são a proposta a partir de 03/11; ajustar conforme o andamento.

| Etapa | Período | Entrega |
|---|---|---|
| 1. Base e telas estáticas | 03–04/11 | Projeto Flask, `requirements.txt`, templates das Telas 1–3 com textos e botões de 44 px; capturas do protótipo |
| 2. Modelos e regras | 05–08/11 | Entidades SQLAlchemy, `scripts/criar_banco.py`, serviços de horários livres e sobreposição; **testes primeiro** (RF01, RF02) |
| 3. Fluxo do cliente | 09–12/11 | Rotas e formulários (Flask-WTF), sugestão de outro barbeiro (RF03), lista de espera (RF04) |
| 4. Painel | 12–14/11 | Login (RF08), janelas (RF07), agenda (RF06), cancelamento e próximo da lista (RF05) |
| 5. Validação e medições | 15–16/11 | Teste com o cliente-base, Lighthouse/axe, medições do RNF03, correções |
| 6. Entrega | 17/11 | Deploy, README final, backup `pg_dump` |

Desejáveis (RF09, RF10) só se sobrar tempo.

## Ordem de implementação dos requisitos
RF08 → RF07 → RF01 → RF02 → RF03 → RF04 → RF06 → RF05 → RF09 → RF10.

## Critérios de pronto por tarefa
Teste do requisito passando; `pytest --cov=app/services` ≥ 80% nas regras de horário; sem segredo no código; textos conforme `05-telas.md`; checagem de acessibilidade da tela alterada.

## Validação com o representante externo
Um único cliente-base. Plano ainda a definir na etapa "Protótipo e plano de validação" da plataforma: ao menos 3 tarefas observáveis (ex.: agendar um serviço; agendar com outro barbeiro quando o escolhido está lotado; entrar na lista de espera) e critérios metrificados de usabilidade, eficiência e satisfação.

## Pendências e hipóteses abertas
- Familiaridade digital do público e uso de ampliação de texto: hipóteses, confirmar na validação.
- Sugestão de outro barbeiro vs. troca automática; lista vertical vs. grade: confirmar com o cliente-base.
- Numeração OWASP 2025 em `02-requisitos.md`: conferir em owasp.org/Top10.
- Versões exatas das dependências: confirmar ao instalar.
- Linha de base de clientes sem horário no sábado: não levantada.
