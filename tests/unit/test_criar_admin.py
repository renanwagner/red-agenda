"""scripts/criar_admin.py: pede os dados no terminal, sem eco da senha e sem guardá-la em arquivo."""
from sqlalchemy import select

from app.models import Barbeiro, db
from scripts import criar_admin
from scripts.criar_banco import criar_banco

SENHA = "senha-de-teste-1"


def _respostas(*valores):
    fila = list(valores)
    return lambda *_args, **_kwargs: fila.pop(0)


def test_cria_administrador_pelo_terminal(tmp_path, capsys):
    url = f"sqlite:///{tmp_path / 'admin.db'}"
    criar_banco(url)
    app = criar_admin.main(url, entrada=_respostas("Admin Exemplo", "admin@exemplo.com"),
                           pedir_senha=_respostas(SENHA, SENHA))
    with app.app_context():
        b = db.session.scalar(select(Barbeiro))
        assert (b.nome, b.email, b.papel) == ("Admin Exemplo", "admin@exemplo.com", "administrador")
        assert b.senha_hash.startswith("scrypt:")
    saida = capsys.readouterr().out
    assert "Administrador criado" in saida and SENHA not in saida


def test_repete_a_pergunta_se_a_senha_e_curta_ou_nao_confere(tmp_path, capsys):
    url = f"sqlite:///{tmp_path / 'admin.db'}"
    criar_banco(url)
    criar_admin.main(url, entrada=_respostas("Admin Exemplo", "admin@exemplo.com"),
                     pedir_senha=_respostas("curta", "curta", SENHA, "outra-senha-1", SENHA, SENHA))
    saida = capsys.readouterr().out
    assert "pelo menos 10 caracteres" in saida and "não conferem" in saida


def test_email_em_uso_nao_cria(tmp_path, capsys):
    url = f"sqlite:///{tmp_path / 'admin.db'}"
    criar_banco(url)
    for _ in range(2):
        app = criar_admin.main(url, entrada=_respostas("Admin Exemplo", "admin@exemplo.com"),
                               pedir_senha=_respostas(SENHA, SENHA))
    assert "já está em uso" in capsys.readouterr().out
    with app.app_context():
        assert len(db.session.scalars(select(Barbeiro)).all()) == 1
