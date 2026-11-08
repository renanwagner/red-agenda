# RED Agenda — instruções para o Claude Code

MVP web de agendamento para a RED Barbearia (Estância Velha, RS), feito como projeto acadêmico individual (Projeto de Software, Ciência da Computação). Prazo de entrega: 17/11/2026.

Leia os arquivos em `docs/` antes de implementar qualquer coisa. Eles são a fonte de verdade. Se algo faltar ou divergir, **pergunte antes de decidir**; não invente campos, regras ou telas.

## Problema em uma frase
Hoje a RED marca horários manualmente pelo WhatsApp, o sábado lota e o cliente que fica sem horário procura outra barbearia. O MVP permite agendar por um link, sugere outro barbeiro quando o escolhido está ocupado e mantém uma lista de espera para recuperar o cliente quando houver cancelamento.

## Stack (fixa — não trocar nem acrescentar sem pedir)
- Python 3.12, Flask 3.x (Jinja2), SQLAlchemy 2.0 + Flask-SQLAlchemy 3.1
- Flask-Login 0.6 (sessão do painel), Flask-WTF 1.2 (validação e CSRF)
- Banco: SQLite no desenvolvimento e no protótipo; PostgreSQL 16 hospedado na entrega (driver psycopg 3.x). A troca é só a variável `DATABASE_URL`.
- Servidor de produção: Gunicorn 23.x com **1 processo e 4 threads** (o contador de tentativas de login fica em memória).
- Front-end: HTML5, CSS3 e JavaScript pontual. **Sem framework de front-end** (nada de React/Vue, nada de Lovable/Supabase).
- Testes: pytest 8.x e pytest-cov 6.x. Segurança de dependências: pip-audit.

## Arquitetura: monólito em três camadas
1. **Apresentação** (rotas/controladores Flask + templates Jinja2): só recebe requisições, chama a camada de regras e renderiza.
2. **Regras de negócio** (serviços): duração por serviço, blocos livres, sobreposição, sugestão de outro barbeiro, lista de espera. São funções que recebem e devolvem dados e **não conhecem HTML nem SQL**.
3. **Persistência** (repositórios + modelos SQLAlchemy): único lugar que acessa o banco.

Regra de ouro: cada camada só fala com a vizinha. A interface nunca acessa o banco; as regras nunca importam Flask nem templates.

Estrutura sugerida (confirmar no plano com o usuário):
```
app/
  __init__.py          # create_app, configuração por variáveis de ambiente
  models.py            # entidades SQLAlchemy
  repositories/        # persistência
  services/            # regras de negócio (testáveis sem navegador)
  web/                 # rotas, formulários (Flask-WTF), templates, static
tests/
  unit/                # regras
  acceptance/          # histórias e requisitos
scripts/
  criar_banco.py       # cria tabelas e carrega os 7 serviços (repetível, sem duplicar)
```

## Convenções
- Nomes das entidades e campos exatamente como em `docs/03-modelo-dados.md` (português, minúsculas, `_` como separador).
- Textos da interface exatamente como em `docs/05-telas.md`.
- Comentários e mensagens de commit em português, curtos.
- Nunca colocar segredo no código. `SECRET_KEY`, `DATABASE_URL` e `FLASK_DEBUG` vêm de variáveis de ambiente (`.env` no `.gitignore`).
- Dados de exemplo e testes usam apenas dados **fictícios** (nada de telefones ou nomes reais).

## Segurança (detalhes em `docs/02-requisitos.md`, RNF01 e RNF02)
- Senha **nunca** em texto limpo, nem MD5/SHA-1. Guardar só o hash scrypt (`werkzeug.security.generate_password_hash`) em `barbeiro.senha_hash`. Mínimo de 10 caracteres.
- Todo acesso ao banco via ORM com parâmetros; proibido montar SQL por concatenação.
- Validação **no servidor** em todo formulário (Flask-WTF) e token CSRF em todo POST. Alterações só por POST.
- Escape automático do Jinja2 ativo; não usar `|safe` em dado do usuário. Cabeçalho `Content-Security-Policy: default-src 'self'`.
- Autorização checada em cada rota protegida (perfil e dono do registro), não só escondendo botões.
- Cookie de sessão: HttpOnly, Secure, SameSite=Lax, expira em 8 h. Bloqueio de 15 min após 5 falhas de login seguidas por e-mail; mensagem de erro única.
- Erros 400/403/404/500 genéricos, sem rastreio. Debug desligado em produção.

## Acessibilidade (RNF04)
Área de toque ≥ 44×44 px; contraste ≥ 4,5:1 (texto) e 3:1 (componentes); rótulos visíveis e associados (`<label for>`); erro com ícone + texto + correção, anunciado por `aria-live`; estado nunca só por cor; operação por teclado com foco visível (contorno ≥ 2 px); sem rolagem horizontal em 360 px e texto ampliável a 200%; **sem CAPTCHA** e sem limite de tempo no formulário público.

## Desempenho (RNF03)
Página pública de horários: carregamento ≤ 3 s no Lighthouse mobile (Slow 4G, CPU 4x), ≤ 300 KB transferidos. Mediana de 5 medições após 1 de aquecimento. Primeiro acesso após inatividade (partida a frio): ≤ 10 s.

## Como trabalhar
1. **Testes das regras antes das telas.** Comece por RF01 e RF02 (sobreposição na transação de gravação).
2. Uma funcionalidade por vez, citando o requisito (RFxx/RNFxx). Mostre o plano antes de codificar mudanças grandes.
3. Rode `pytest --cov=app/services` antes de dar uma tarefa por concluída. Meta: ≥ 80% de cobertura nas regras de horário.
4. Não adicione funções fora do escopo (pagamento, lembretes automáticos por API do WhatsApp, múltiplas unidades). Estão registradas como evolução futura.
5. Em dúvida entre duas decisões, pergunte.

## Fora do escopo (não implementar)
Pagamento e valores de serviços; lembretes/mensagens automáticos pela API do WhatsApp; migrações com Flask-Migrate (usar `scripts/criar_banco.py`); app mobile nativo; CAPTCHA; dados de crianças (nome completo, idade); CPF, endereço, data de nascimento.

## Documentos
- `docs/01-contexto.md` — problema, público, diferencial, ODS, escopo
- `docs/02-requisitos.md` — RF01–RF10 e RNF01–RNF04
- `docs/03-modelo-dados.md` — seis entidades
- `docs/04-arquitetura.md` — camadas, tecnologias e justificativa
- `docs/05-telas.md` — três telas do protótipo
- `docs/06-plano.md` — ordem de implementação e datas
