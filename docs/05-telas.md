# 05 — Telas do protótipo (fluxo do cliente)

Mobile-first (360 px). Textos exatos abaixo. O painel (RF05–RF08, RNF01) **não** faz parte das três telas.

Rótulos consistentes em todas as telas: "Serviço", "Barbeiro", "Data", "Telefone (com DDD)", "Confirmar agendamento", "Entrar na lista de espera", "Voltar".

## Tela 1 — Entrada: escolha de serviço e barbeiro
- **Requisitos:** RF01, RNF03, RNF04, RNF02.
- **Componentes:** título "Agende seu horário na RED Barbearia"; subtítulo "Estância Velha, RS"; rótulo persistente "Escolha o serviço" com 7 botões (ex.: "Corte – 30 min", "Corte + barba – 45 min", "Barba – 15 min"), 44×44 px e 8 px de espaço; rótulo "Escolha o barbeiro" com seletor de 3 barbeiros; campo "Data" com rótulo; botão principal "Ver horários"; texto de apoio "Selecione serviço, barbeiro e data para continuar" enquanto desabilitado.
- **Ação e navegação:** tocar em "Ver horários" com tudo preenchido → Tela 2. Botão desabilitado enquanto incompleto. Entrada: link público (WhatsApp ou navegador). Sem login nem cadastro.
- **Acessibilidade:** botões ≥ 44 px; rótulos visíveis; contraste 4,5:1/3:1; foco com contorno de 2 px; seleção em texto ("Selecionado: Corte"); sem rolagem horizontal em 360 px.
- **Dados fictícios:** sete serviços com as durações do modelo; "Barbeiro 1/2/3"; data sábado 14/11/2026.

## Tela 2 — Execução: horários livres e dados do cliente
- **Requisitos:** RF01, RF02, RNF02, RNF04.
- **Componentes:** resumo "Corte + barba (45 min) · Barbeiro 1 · 14/11/2026" com botão "Alterar"; **apenas horários livres** em botões 44×44 px com texto "Livre" (ex.: "09:30 – Livre"); horário escolhido com "Selecionado" e borda de 3 px; campos "Nome" e "Telefone (com DDD)" com rótulo persistente; erro de telefone com ícone + texto "Telefone incompleto. Informe DDD e número, como 51 90000-0000" (aria-live); botão "Confirmar agendamento" (largura total); link "Voltar".
- **Ação e navegação:** "Confirmar agendamento" com horário, nome e telefone válidos → grava e vai à Tela 3 (confirmação). Telefone incompleto → não envia e o foco vai ao campo com erro. "Voltar" → Tela 1 mantendo a seleção.
- **Acessibilidade:** estado em texto e borda; erro por ícone+texto+foco, lido pelo TalkBack; contraste 4,5:1; toque 44 px; Tab/Enter com foco visível; Lighthouse ≥ 90; zoom 200% sem perda.
- **Dados fictícios:** Corte + barba (45 min), Barbeiro 1, 14/11/2026; livres 09:30, 10:00, 10:30, 11:00; "Cliente Exemplo", "51 90000-0000".

## Tela 3 — Resultado: confirmação, sugestão ou lista de espera
- **Requisitos:** RF02, RF03, RF04, RNF02, RNF04.
- **Estado A (confirmação):** alerta de sucesso com ícone de check e "Agendamento confirmado"; resumo (serviço, barbeiro, data e hora); botão "Voltar ao início".
- **Estado B (sem vaga com o barbeiro escolhido):** alerta de atenção com triângulo e "Barbeiro 1 não tem horário nesta data"; até 3 sugestões em botões 44×44 px ("Barbeiro 2 – 10:00", "Barbeiro 3 – 10:30"); botão "Entrar na lista de espera".
- **Estado C (sem sugestão):** alerta com ícone e "Nenhum horário livre nesta data"; botão "Entrar na lista de espera"; texto "Você será chamado pelo WhatsApp se surgir vaga".
- **Erro genérico:** "Não foi possível confirmar agora. Tente novamente."
- **Ação e navegação:** A → "Voltar ao início" (Tela 1). B → tocar numa sugestão confirma com o outro barbeiro e mostra A. C → "Entrar na lista de espera" grava e mostra "Você está na lista de espera para 14/11/2026".
- **Acessibilidade:** ícone + título + texto em cada estado (cor só reforça); contraste 4,5:1; botões 44 px; título de cada estado em h1 anunciado por aria-live; erro sem código nem rastreio; Tab na ordem visual; zoom 200% sem cortar sugestões.
- **Dados fictícios:** A: Corte + barba, Barbeiro 1, 14/11/2026, 09:30. B: "Barbeiro 2 – 10:00", "Barbeiro 3 – 10:30". C: nenhum livre.

## Coerência
- Fluxo: T1 escolhe → T2 vê só horários livres e confirma → T3 mostra resultado, sugestão ou lista de espera. Retorno: "Voltar" (T2) mantém a seleção; "Voltar ao início" (T3) recomeça.
- Sem contradição segurança × usabilidade: bloqueio de login vale só para o painel; o formulário público **não usa CAPTCHA**; proteção por validação no servidor, CSRF e a regra de uma entrada de espera por cliente/serviço/data.
- As telas só exibem o que a camada de regras devolve (sem regra de negócio no navegador).
- Função desejável fora do protótipo: RF09 e RF10.
- **Hipótese a confirmar com o cliente-base:** se a sugestão de outro barbeiro é entendida como alternativa escolhida por ele (não troca automática); lista vertical ou grade para os horários.
