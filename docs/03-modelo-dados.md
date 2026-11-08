# 03 — Modelo de dados (PostgreSQL 16 / SQLite no dev, via SQLAlchemy)

Seis entidades. Não criar campos ou tabelas além destas sem pedir. Identificadores `id_<entidade>`: inteiro, chave primária, autoincremento.

## barbeiro
Profissional que atende e acessa o painel.
| Campo | Tipo | Regras |
|---|---|---|
| id_barbeiro | inteiro PK | automático |
| nome | texto(100) | obrigatório |
| email | texto(120) | obrigatório, **único** (login) |
| senha_hash | texto | obrigatório; **só o hash scrypt**, nunca a senha |
| papel | texto | `administrador` ou `barbeiro` |
| ativo | lógico | padrão verdadeiro |

Regras: `senha_hash` nunca é exibida nem registrada em log. Barbeiro inativo some do agendamento e das sugestões, mas o histórico fica (inativa-se, não exclui). Só o administrador edita serviços e cria barbeiros.
Relações: 1 barbeiro → N janelas_atendimento; 1 → N agendamentos; pode ser preferência de N entradas de lista_espera (opcional).

## cliente
Quem agenda pelo link. Guarda só o necessário para identificar e chamar pelo WhatsApp. Quando é um responsável, o nome é o de quem agenda.
| Campo | Tipo | Regras |
|---|---|---|
| id_cliente | inteiro PK | automático |
| nome | texto(100) | obrigatório |
| telefone | texto(13) | obrigatório, só dígitos com DDD, **único** |
| criado_em | data/hora | automático |

Regras: formato validado (DDD + 10 ou 11 dígitos). **Não há** CPF, endereço nem data de nascimento. Cliente com agendamentos não é excluído.
Relações: 1 cliente → N agendamentos; 1 → N lista_espera.

## servico
Catálogo com a duração de cada serviço.
| Campo | Tipo | Regras |
|---|---|---|
| id_servico | inteiro PK | automático |
| nome | texto(60) | obrigatório, **único** |
| duracao_min | inteiro | obrigatório, > 0 e múltiplo de 5 |
| ativo | lógico | padrão verdadeiro |

Valores iniciais: corte 30; corte + barba 45; corte infantil 45; barba 15; sobrancelha 10; corte na zero 15; zero + barba 30.
Regras: serviço inativo some do agendamento mas permanece nos antigos. O `fim` de um agendamento usa a duração vigente na gravação.
Relações: 1 servico → N agendamentos; N lista_espera.

## janela_atendimento
Períodos de um barbeiro em um dia: abertos ou bloqueados. Concentra a demanda (quantos horários abrir) e impede marcações em pausas e folgas.
| Campo | Tipo | Regras |
|---|---|---|
| id_janela | inteiro PK | automático |
| barbeiro_id | ref. barbeiro | obrigatória |
| data | data | obrigatória |
| hora_inicio | hora | obrigatória |
| hora_fim | hora | obrigatória, > hora_inicio |
| tipo | texto | `aberto` ou `bloqueado` |

Regras: mesmo barbeiro, dia e tipo não se sobrepõem. Um horário só é oferecido dentro de janela aberta e fora de qualquer bloqueada. Não existe sem barbeiro.
Relações: N janelas → 1 barbeiro.

## agendamento
Reserva de um cliente com um barbeiro para um serviço. Registro central do fluxo e origem dos indicadores.
| Campo | Tipo | Regras |
|---|---|---|
| id_agendamento | inteiro PK | automático |
| cliente_id, barbeiro_id, servico_id | refs | obrigatórias |
| inicio | data/hora | obrigatório |
| fim | data/hora | obrigatório (= inicio + duração do serviço), > inicio |
| status | texto | `confirmado`, `cancelado` ou `concluido` |
| origem | texto | `link` ou `painel` |
| criado_em | data/hora | automático |

Regras: para o mesmo barbeiro, **nunca dois confirmados sobrepostos** (verificado na transação de gravação). Início dentro de janela aberta e fora das bloqueadas. Cancelar muda o status; **não apaga**.
Relações: N agendamentos → 1 cliente, 1 barbeiro, 1 servico.
Índice sugerido: `(barbeiro_id, inicio)`.

## lista_espera
Fila de quem não achou vaga; permite chamar o próximo compatível quando um cancelamento libera horário.
| Campo | Tipo | Regras |
|---|---|---|
| id_espera | inteiro PK | automático |
| cliente_id, servico_id | refs | obrigatórias |
| barbeiro_id | ref | opcional (preferência) |
| data_desejada | data | obrigatória |
| entrou_em | data/hora | automático; define a ordem |
| status | texto | `aguardando`, `chamado`, `atendido` ou `desistiu` |

Regras: sem duas entradas `aguardando` do mesmo cliente para o mesmo serviço e data. Ordem de chamada por `entrou_em`. Ao chamar → `chamado`; ao agendar → `atendido`. O desfecho **não é apagado** (alimenta a taxa de recuperação).
Relações: N entradas → 1 cliente, 1 servico, opcionalmente 1 barbeiro.

## Fluxo de dados (CRUD por momento)
1. **Consulta de horários:** lê servico, janela_atendimento e agendamento; calcula blocos livres; não grava. Sem vaga, lê os mesmos dados dos outros barbeiros ativos para sugerir.
2. **Confirmação:** cria ou reaproveita cliente (telefone único) e cria agendamento `confirmado`/`link`, em transação que revalida sobreposição.
3. **Sem vaga:** cria lista_espera `aguardando`.
4. **Cancelamento (painel):** atualiza agendamento → `cancelado`; consulta lista_espera e indica o próximo (`chamado`); se agendar → `atendido`.
5. **Painel:** cria/altera/exclui janelas_atendimento; lê agendamentos do dia e da semana.

## Minimização
Armazena: telefone (necessário para chamar pelo WhatsApp). Não coleta: CPF, endereço, data de nascimento, nome completo ou idade de criança (o serviço "corte infantil" já define a duração).
Evolução fora do escopo: entidades de pagamento (valores) e de lembretes (mensagens automáticas por API do WhatsApp).
