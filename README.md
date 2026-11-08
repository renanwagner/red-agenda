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
4. Criar as tabelas e carregar os 7 serviços: `python scripts/criar_banco.py` (pode repetir: não duplica nem sobrescreve).
5. Executar: `flask --app app run`

As telas do cliente ainda usam dados de demonstração; a leitura do banco entra nas próximas etapas.

## Testes
`pytest --cov=app` (as regras de horário ficarão em `app/services`; depois use `pytest --cov=app/services`).

## Produção
Gunicorn com 1 processo e 4 threads, `DATABASE_URL` apontando para o PostgreSQL 16 hospedado, HTTPS pela plataforma, `FLASK_DEBUG` desligado. Documentação completa em `docs/`.
