# RED Agenda

MVP de agendamento para a RED Barbearia (Estância Velha, RS). Projeto acadêmico de Projeto de Software.

## Rodar localmente (SQLite)
1. Criar o ambiente virtual:
   - Linux/macOS: `python3.12 -m venv .venv && source .venv/bin/activate`
   - Windows (PowerShell): `py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1`
2. Instalar as dependências: `pip install -r requirements.txt`
3. Definir as variáveis de ambiente (nunca versionar valores reais; `.env` está no `.gitignore`):
   - `SECRET_KEY`: obrigatória. Sem ela a aplicação não inicia.
   - `DATABASE_URL`: por exemplo `sqlite:///red_agenda.db`.
   - `FLASK_DEBUG=1`: só em desenvolvimento local.
4. Executar: `flask --app app run`

O protótipo atual usa dados de demonstração e ainda não acessa o banco. O script `scripts/criar_banco.py` (tabelas e 7 serviços) será criado na etapa de persistência.

## Testes
`pytest --cov=app` (as regras de horário ficarão em `app/services`; depois use `pytest --cov=app/services`).

## Produção
Gunicorn com 1 processo e 4 threads, `DATABASE_URL` apontando para o PostgreSQL 16 hospedado, HTTPS pela plataforma, `FLASK_DEBUG` desligado. Documentação completa em `docs/`.
