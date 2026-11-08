# 04 — Arquitetura e tecnologias

## Padrão
Monólito web em Python (Flask), em **três camadas**: apresentação, regras de negócio e persistência. Cada camada tem uma responsabilidade e só conversa com a vizinha. A interface nunca acessa o banco; as regras não conhecem HTML.

Por que é proporcional ao MVP:
- **Desenvolvimento individual:** uma aplicação, um repositório, um deploy. Microsserviços ou front-end separado dobrariam a configuração para um escopo curto.
- **Funções essenciais primeiro:** as regras do diferencial (duração por serviço, outro barbeiro, lista de espera, limite de horários por dia) ficam na camada de regras e são testáveis antes das telas.
- **Testes:** as regras são funções que recebem e devolvem dados; testam-se sem navegador e sem banco real.
- **Manutenção:** mudar uma duração ou criar serviço é alteração de dados. Trocar SQLite por PostgreSQL afeta só a persistência.
- **Portabilidade:** monólito web responsivo atende celular do cliente e computador do barbeiro com o mesmo código.

## Tecnologias e função
| Tecnologia | Função / camada |
|---|---|
| Flask 3.x + Jinja2 | rotas, controladores e templates (apresentação) |
| SQLAlchemy 2.0 + Flask-SQLAlchemy 3.1 | mapeia as seis entidades; transações (persistência) |
| Flask-Login 0.6 | sessão do barbeiro; protege o painel |
| Flask-WTF 1.2 | validação de formulários e CSRF |
| psycopg 3.x | driver do PostgreSQL (só na entrega) |
| pytest 8.x + pytest-cov 6.x | testes das regras e aceitação; cobertura |
| Gunicorn 23.x | servidor de aplicação em produção |
| HTML5, CSS3, JS pontual | telas responsivas, leves; JS só para pequenos ajustes de interface (hoje, `static/js/tela1.js` aplica a data ao escolher); sem regra de negócio no navegador |

Fora de propósito: framework de front-end, outros pacotes sem contribuição clara. As versões acima são as séries pretendidas; confirmar ao instalar.

## Banco
PostgreSQL 16 hospedado e gerenciado (plano gratuito) na entrega; SQLite no dev/protótipo. A URL de conexão fica em `DATABASE_URL`; a troca de banco só exige essa variável e o driver. Motivos: vínculos claros (chaves estrangeiras), transações (impedem dois clientes no mesmo horário), unicidade (telefone, e-mail), volume pequeno, acesso simultâneo do link e do painel pela internet, backup automático da plataforma + `pg_dump` periódico guardado fora da hospedagem.

## Limitações e mitigação
1. Plano gratuito pode suspender a aplicação por inatividade; o monólito escala como bloco único. Mitigação: medir tempo de resposta na validação, manter `pg_dump`, camadas separadas facilitam migrar de hospedagem.
2. Curva de aprendizado de SQLAlchemy 2.0 e transações. Mitigação: começar pela regra de sobreposição, escrevendo os testes primeiro.

## Rastreabilidade
problema e público → fluxo (escolher serviço/barbeiro, ver horários, confirmar, sugestão ou lista de espera) → arquitetura em camadas → Flask e apoio → PostgreSQL e entidades → viabilidade individual.
- Necessidade atendida: marcação manual → regras centralizadas calculam blocos livres.
- Decisão que viabiliza o diferencial: transações do SQLAlchemy revalidam sobreposição, sustentando a lista de espera após cancelamento.
- Entidade indispensável: `lista_espera` (transforma cliente sem vaga em cliente recuperado; indicador ODS 8).
- Excluído deliberadamente: pagamento online e lembretes automáticos (contato segue pelo WhatsApp).
