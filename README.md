# RED Agenda

MVP de agendamento para a RED Barbearia (Estância Velha, RS). Projeto acadêmico de Projeto de Software.

## Rodar localmente (SQLite)
1. Criar o ambiente: `python3.12 -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
2. Instalar: `pip install -r requirements.txt`
3. Definir variáveis de ambiente: `SECRET_KEY`, `DATABASE_URL` (ex.: `sqlite:///red_agenda.db`), `FLASK_DEBUG=1` (só local)
4. Criar tabelas e carregar os 7 serviços: `python scripts/criar_banco.py`
5. Executar: `flask --app app run`

## Testes
`pytest --cov=app/services`

## Produção
Gunicorn com 1 processo e 4 threads, `DATABASE_URL` apontando para o PostgreSQL 16 hospedado, HTTPS pela plataforma, `FLASK_DEBUG` desligado. Documentação completa em `docs/`.
