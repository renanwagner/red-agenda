"""RF08 e RNF01: login do painel. Sem Flask: recebe e devolve dados.

- Senha só como hash scrypt com salt (Werkzeug); mínimo de 10 caracteres.
- Bloqueio de 15 min após 5 falhas seguidas para o mesmo e-mail, com contador em memória
  (por isso o Gunicorn roda com 1 processo). Falhas de e-mail inexistente também contam,
  para o bloqueio não revelar quais e-mails existem.
- Mesmo resultado ("invalido") para e-mail inexistente, senha errada ou barbeiro inativo.
"""
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from app.repositories import barbeiros as repo

SENHA_MINIMA = 10
LIMITE_FALHAS = 5
TEMPO_BLOQUEIO = timedelta(minutes=15)
_hash_falso = None  # usado quando o e-mail não existe, para o tempo de resposta não denunciar


class SenhaCurta(ValueError):
    pass


class EmailEmUso(ValueError):
    pass


def normalizar_email(email):
    return (email or "").strip().lower()


def gerar_hash(senha):
    if len(senha) < SENHA_MINIMA:
        raise SenhaCurta(f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres.")
    return generate_password_hash(senha, method="scrypt")


class ControleTentativas:
    """Falhas seguidas por e-mail, em memória e protegidas entre threads."""

    def __init__(self, limite=LIMITE_FALHAS, bloqueio=TEMPO_BLOQUEIO, relogio=datetime.now):
        self._limite, self._bloqueio, self._relogio = limite, bloqueio, relogio
        self._falhas = {}       # email -> quantidade
        self._ate = {}          # email -> fim do bloqueio
        self._trava = threading.Lock()

    def bloqueado(self, email):
        email = normalizar_email(email)
        with self._trava:
            fim = self._ate.get(email)
            if fim is None:
                return False
            if self._relogio() >= fim:      # bloqueio venceu: recomeça a contagem
                del self._ate[email]
                self._falhas.pop(email, None)
                return False
            return True

    def registrar_falha(self, email):
        email = normalizar_email(email)
        with self._trava:
            self._falhas[email] = self._falhas.get(email, 0) + 1
            if self._falhas[email] >= self._limite:
                self._ate[email] = self._relogio() + self._bloqueio

    def registrar_sucesso(self, email):
        email = normalizar_email(email)
        with self._trava:
            self._falhas.pop(email, None)
            self._ate.pop(email, None)


@dataclass
class Autenticacao:
    status: str                 # "ok", "invalido" ou "bloqueado"
    barbeiro: dict | None = None


def autenticar(email, senha, controle):
    global _hash_falso
    email = normalizar_email(email)
    if controle.bloqueado(email):
        return Autenticacao("bloqueado")
    dados = repo.credenciais_por_email(email)
    if dados is None:
        if _hash_falso is None:
            _hash_falso = generate_password_hash("senha-inexistente", method="scrypt")
        check_password_hash(_hash_falso, senha)
        valido = False
    else:
        valido = check_password_hash(dados["senha_hash"], senha) and dados["ativo"]
    if not valido:
        controle.registrar_falha(email)
        return Autenticacao("invalido")
    controle.registrar_sucesso(email)
    return Autenticacao("ok", {k: dados[k] for k in ("id_barbeiro", "nome", "papel")})


def barbeiro_da_sessao(id_barbeiro):
    """Perfil do barbeiro logado (a cada requisição): None se não existe mais ou foi inativado."""
    try:
        id_barbeiro = int(id_barbeiro)
    except (TypeError, ValueError):
        return None
    return repo.perfil_ativo(id_barbeiro)


def criar_administrador(nome, email, senha):
    """Cadastra o administrador (primeiro acesso, pelo terminal). Devolve o id."""
    email = normalizar_email(email)
    senha_hash = gerar_hash(senha)
    if repo.email_em_uso(email):
        raise EmailEmUso("Este e-mail já está em uso.")
    return repo.criar_barbeiro(nome.strip(), email, senha_hash, "administrador")
