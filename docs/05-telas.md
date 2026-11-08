# 05 — Telas do protótipo (fluxo do cliente)

Mobile-first (360 px). Textos exatos abaixo. O painel (RF05–RF08, RNF01) **não** faz parte das quatro telas.

Rótulos consistentes em todas as telas: "Serviço", "Barbeiro", "Data", "Horário", "Telefone (com DDD)", "Confirmar agendamento", "Entrar na fila de espera", "Voltar". Nome de serviço sempre no padrão "Corte – 30 min", inclusive nos resumos.

## Tela 1 — Escolha: serviço, data, horário e barbeiro
- **Requisitos:** RF01, RNF02, RNF03, RNF04.
- **Componentes:** título "Agende seu horário na RED Barbearia"; subtítulo "Estância Velha, RS"; logo no cabeçalho; "Escolha o serviço" com 7 botões (ex.: "Corte – 30 min", "Corte + barba – 45 min", "Barba – 15 min"); "Escolha a data" (padrão 14/11/2026, aplicada ao escolher, sem botão); "Escolha o horário" (09:30, 10:00, 10:30, 11:00); "Escolha o barbeiro" com "Qualquer barbeiro" como padrão e os 3 barbeiros; botão principal "Ver disponibilidade"; texto de apoio "Selecione serviço, data e horário para continuar" enquanto desabilitado.
- **Ação e navegação:** "Ver disponibilidade" com serviço, data e horário escolhidos → Tela 2. Botão desabilitado enquanto incompleto. Entrada: link público (WhatsApp ou navegador). Sem login nem cadastro.
- **Acessibilidade:** botões ≥ 44×44 px com 8 px de espaço; rótulos visíveis; contraste 4,5:1/3:1; foco com contorno de 3 px; seleção em texto ("Selecionado: …" e ✓), não só cor; sem rolagem horizontal em 360 px.
- **Dados fictícios:** sete serviços com as durações do modelo; "Barbeiro 1/2/3"; sábado 14/11/2026.

## Tela 2 — Disponibilidade no horário escolhido
- **Requisitos:** RF01, RF03, RF04, RNF04.
- **Resumo:** "Corte + barba – 45 min · 14/11/2026 às 10:00" e link "Voltar".
- **Caso a (barbeiro livre):** "Barbeiro 2 está livre às 10:00" e botão "Continuar com Barbeiro 2" → Tela 3 (modo `confirmacao`).
- **Caso b (barbeiro ocupado):** alerta com triângulo "Barbeiro 1 não está livre às 10:00"; botão "Entrar na fila para o Barbeiro 1 às 10:00" (modo `fila_barbeiro`); botão "Ver outros barbeiros livres às 10:00" que abre a lista, em botões 44×44 px ("Barbeiro 2 – 10:00", "Barbeiro 3 – 10:00"); tocar num deles → Tela 3 (modo `confirmacao`). Sem outros livres, o botão da lista não aparece.
- **Caso c ("Qualquer barbeiro" com livres):** "Escolha o barbeiro" com os livres naquele horário ("Barbeiro 2 – 10:00", "Barbeiro 3 – 10:00") → Tela 3 (modo `confirmacao`).
- **Caso d ("Qualquer barbeiro", ninguém livre):** "Nenhum barbeiro está livre às 11:00" e botão "Entrar na fila para 11:00" → Tela 3 (modo `fila_horario`).
- **Acessibilidade:** ícone + título + texto (a cor só reforça); botões ≥ 44 px com 8 px entre eles; a lista abre por teclado (Enter).
- **Dados fictícios (iguais para qualquer data):** 09:30 → Barbeiro 2; 10:00 → Barbeiros 2 e 3; 10:30 → Barbeiro 3; 11:00 → nenhum.

## Tela 3 — Seus dados
- **Requisitos:** RF02, RF04, RNF02, RNF04.
- **Componentes:** título "Seus dados"; resumo "Corte + barba – 45 min · Barbeiro 2 · 14/11/2026 às 10:00" (nos modos de fila começa com "Fila de espera · …"); campos "Nome" e "Telefone (com DDD)" com rótulo persistente (os exemplos "Cliente Exemplo" e "51 90000-0000" ficam só como placeholder); botão "Confirmar agendamento" (modo `confirmacao`) ou "Entrar na fila de espera" (modos de fila), largura total; link "Voltar".
- **Erros (ícone + texto + correção, `aria-live`, foco no campo):** telefone: "Telefone incompleto. Informe DDD e número, como 51 90000-0000"; nome: "Informe seu nome."
- **Ação e navegação:** dados válidos → grava e vai à Tela 4. Telefone incompleto → não envia e o foco vai ao campo com erro. "Voltar" → Tela 2 mantendo a escolha. O servidor valida a coerência entre a escolha e o modo; incoerente volta à Tela 2.
- **Acessibilidade:** erro com ícone, texto e borda de 3 px; rótulo não substituído pelo placeholder; Tab/Enter com foco visível; zoom 200% sem perda.

## Tela 4 — Resultado
- **Requisitos:** RF02, RF03, RF04, RNF02, RNF04.
- **Estado `confirmado`:** alerta de sucesso com check e "Agendamento confirmado"; tabela com Serviço, Barbeiro, Data e Hora; botão "Voltar ao início".
- **Estado `fila_horario`:** "Você está na fila de espera para 14/11/2026 às 11:00" e "Vamos chamar você pelo WhatsApp se surgir vaga em qualquer barbeiro neste horário."
- **Estado `fila_barbeiro`:** "Você está na fila do Barbeiro 1 para 14/11/2026 às 10:00" e "Vamos chamar você pelo WhatsApp se o Barbeiro 1 liberar este horário."
- **Estado de duplicidade (RF04):** quem já está na mesma fila (cliente, serviço, data, hora e barbeiro) não é gravado de novo; alerta de informação com ícone e título "Você já está nesta fila de espera.", resumo "Corte + barba – 45 min · Qualquer barbeiro · 14/11/2026 às 11:00" e o mesmo aviso de WhatsApp da fila.
- **Erro genérico:** "Não foi possível confirmar agora. Tente novamente." Páginas de erro: "Requisição inválida. Tente novamente.", "Acesso não permitido." e "Página não encontrada."
- **Acessibilidade:** ícone + título (h1) + texto em cada estado (cor só reforça); título anunciado (`role="status"`); botão ≥ 44 px; a URL (`/resultado`, sem parâmetros) não contém nome nem telefone; erro sem código nem rastreio.

## Painel — Entrar (RF08, RNF01)
Fora das quatro telas do cliente; textos aprovados em 08/11/2026.
- **Componentes:** título "Entrar no painel"; subtítulo "RED Barbearia – área do barbeiro"; campos "E-mail" e "Senha" com rótulo persistente; botão "Entrar".
- **Erros (ícone + texto, `aria-live`):** credenciais inválidas, barbeiro inativo ou e-mail inexistente: mensagem única "E-mail ou senha incorretos. Confira e tente novamente."; campo vazio: "Informe o e-mail." / "Informe a senha."; após 5 falhas seguidas para o mesmo e-mail: "Muitas tentativas. Tente novamente em 15 minutos."
- **Após entrar:** "Painel – {nome do barbeiro}" com botão "Sair" (POST); sair volta a "Entrar no painel". Rotas do painel sem login redirecionam para a entrada.
- **Primeiro administrador:** criado no terminal com `python scripts/criar_admin.py`.

## Coerência
- Fluxo: T1 escolhe serviço, data, horário e barbeiro → T2 mostra a disponibilidade e as opções → T3 pede os dados → T4 mostra confirmação ou fila. "Voltar" mantém a escolha; "Voltar ao início" recomeça.
- Sem contradição segurança × usabilidade: bloqueio de login vale só para o painel; o formulário público **não usa CAPTCHA**; proteção por validação no servidor, CSRF e a regra de uma entrada de fila por cliente, serviço, data, hora e barbeiro.
- As telas só exibem o que a camada de regras devolve (sem regra de negócio no navegador). O estado da Tela 4 vem do servidor: a sessão assinada guarda só o id do registro gravado, e a tela lê o registro no banco (não aceita estado pela URL).
- Função desejável fora do protótipo: RF09 e RF10.
- **Resolvido:** a sugestão de outro barbeiro é escolha do cliente (caso b), não troca automática.
- **Hipótese a confirmar com o cliente-base:** lista vertical ou grade para os horários.
