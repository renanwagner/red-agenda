# 01 — Contexto

## Parceiro e problema
- **Parceiro:** RED Barbearia, Estância Velha (RS). Contato: contato do parceiro. A equipe tem mais de um barbeiro. A barbearia é referência em cortes infantis.
- **Problema relatado:** os horários são marcados manualmente pelo WhatsApp; o sábado fica lotado; o cliente que não consegue horário procura outra barbearia.

## Público
- **Clientes:** adultos que marcam para si e responsáveis que marcam para crianças. Agendam pelo celular, geralmente a partir do WhatsApp, com pouco tempo.
- **Barbeiros (incluindo o contato do parceiro):** definem horários e dias, acompanham a agenda, gerenciam lista de espera e cancelamentos, a partir de computador ou celular na barbearia, entre atendimentos.
- **Beneficiários indiretos:** outros barbeiros da RED (recebem clientes quando o principal está ocupado), a própria RED (perde menos clientes) e famílias de Estância Velha (agenda mais previsível).
- Familiaridade digital e uso de ampliação de texto são **hipóteses** a confirmar na validação (não vêm do diagnóstico).

## Solução (MVP)
Aplicação web responsiva, com link público para o cliente e painel para o barbeiro.
- Agendamento por link com horários calculados pela **duração de cada serviço**.
- **Sugestão de outro barbeiro** quando o escolhido não tem vaga.
- **Lista de espera** ligada a cancelamentos, para recuperar o cliente.
- Painel do barbeiro para janelas de atendimento (abrir/bloquear horários e limitar horários por dia), agenda e cancelamentos.
- Contato continua pelo WhatsApp (link com mensagem pronta é desejável, RF09).

### Durações dos serviços (minutos)
corte 30 · corte + barba 45 · corte infantil 45 · barba 15 · sobrancelha 10 · corte na zero 15 · zero + barba 30

## ODS
**ODS 8 — Trabalho decente e crescimento econômico**, foco na Meta 8.3 (apoio a atividades produtivas e ao crescimento de micro e pequenas empresas). Contribuição realista: transformar demanda que hoje se perde em atendimentos, distribuir a carga entre barbeiros e reduzir o tempo gasto em marcações. Limites: o MVP não cria empregos nem resolve o ODS; mercado local, preços e concorrência estão fora do seu controle. Indicador social: taxa de recuperação de clientes via lista de espera.

## Metas e indicadores do projeto
- Período: 24/10/2026 a 17/11/2026. Diagnóstico e linha de base considerados concluídos.
- Indicadores de processo de implantação, entre eles: cobertura mínima de 80% nas regras de horário e zero defeitos críticos.
- Validação com **um único cliente-base** (representante real).

## Fora do escopo
Pagamento e valores; lembretes automáticos pela API do WhatsApp; múltiplas unidades; dados de criança; CPF/endereço/data de nascimento.
