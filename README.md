# RED Agenda

MVP de agendamento para a RED Barbearia (Estância Velha, RS). Projeto acadêmico de Projeto de Software.

## Rodar localmente (SQLite)
1. Criar o ambiente virtual:
   - Linux/macOS: `python3.12 -m venv .venv && source .venv/bin/activate`
   - Windows (PowerShell): `py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1`
2. Instalar as dependências: `pip install -r requirements.txt`
3. Definir as variáveis de ambiente (nunca versionar valores reais; `.env` está no `.gitignore`):
   - `SECRET_KEY`: obrigatória. Sem ela a aplicação não inicia.
   - `DATABASE_URL`: opcional no desenvolvimento. Sem ela, usa `sqlite:///red_agenda.db`, gravado em `instance/red_agenda.db` (fora do Git).
   - `FLASK_DEBUG=1`: só em desenvolvimento local.
4. Criar as tabelas e carregar os 7 serviços: `python scripts/criar_banco.py` (pode repetir: não duplica nem sobrescreve).
   - Para o protótipo e a validação, use `python scripts/criar_banco.py --demo`: carrega também 3 barbeiros, janelas e agendamentos **fictícios** por 30 dias a partir de 14/11/2026. Sem janelas abertas, a Tela 1 não mostra horários.
5. Criar o administrador do painel: `python scripts/criar_admin.py` (pede nome, e-mail e senha; a senha não aparece na tela e só o hash scrypt é gravado).
6. Executar: `flask --app app run`. Fluxo do cliente em `/`; painel do barbeiro em `/painel`.

## Conferir o banco SQLite
Sem instalar nada (usa o Python do `.venv`), da raiz do projeto:
```
python -c "import sqlite3; c=sqlite3.connect('instance/red_agenda.db'); [print(t, c.execute(f'select count(*) from {t}').fetchone()[0]) for t in ('servico','barbeiro','janela_atendimento','agendamento','cliente','lista_espera')]"
```
Para ver as linhas, abra `instance/red_agenda.db` no DB Browser for SQLite ou numa extensão de SQLite do VS Code.

## Testes
`pytest --cov=app/services` (meta: ≥ 80% nas regras). Suíte completa com cobertura geral: `pytest --cov=app`.

## Produção
Gunicorn com 1 processo e 4 threads, `DATABASE_URL` apontando para o PostgreSQL 16 hospedado, HTTPS pela plataforma, `FLASK_DEBUG` desligado. Documentação completa em `docs/`.
