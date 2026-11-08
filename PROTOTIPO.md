# Protótipo: roteiro de captura (4 telas)

Fluxo do cliente: **Tela 1** escolha → **Tela 2** disponibilidade → **Tela 3** seus dados → **Tela 4** resultado.
Só dados fictícios (`app/web/dados_demo.py`), sem banco e sem gravação. O que mudou em relação aos documentos está em `AJUSTES-PENDENTES.md`.

## Rodar

PowerShell (Windows), na raiz do projeto:
```powershell
.venv\Scripts\activate
$env:SECRET_KEY = "qualquer-valor-local"
flask --app app run
```
Abra **http://localhost:5000** no Chrome ou no Edge **em português**. O campo de data nativo usa o formato do idioma do navegador, então em português aparece dd/mm/aaaa. O cookie de sessão é `Secure`, e esses navegadores o aceitam em `localhost`.

Testes: `pytest -q`.

## Preparar o navegador
1. F12 → **Toggle device toolbar** (Ctrl+Shift+M).
2. **Responsive**, largura **360**, altura **800**, zoom 100%.
3. Captura: menu ⋮ da barra do dispositivo → **Capture full size screenshot**.
4. Conferir: sem barra de rolagem horizontal.

Disponibilidade de demonstração (igual para qualquer data):

| Horário | Barbeiros livres |
|---|---|
| 09:30 | Barbeiro 2 |
| 10:00 | Barbeiro 2, Barbeiro 3 |
| 10:30 | Barbeiro 3 |
| 11:00 | nenhum |

`P` = `servico=2&data=2026-11-14` (Corte + barba, 14/11/2026).

## Capturas obrigatórias (uma por tela)

### 1. Tela 1, escolha
**URL:** `http://localhost:5000/?servico=2&hora=10:00`

O que deve aparecer:
- título "Agende seu horário na RED Barbearia", subtítulo "Estância Velha, RS" e o logo no cabeçalho;
- "Escolha o serviço" com 7 botões no padrão "Corte – 30 min", e "Corte + barba – 45 min" com ✓;
- "Escolha a data" com 14/11/2026 e "Selecionado: 14/11/2026";
- "Escolha o horário" (09:30, 10:00, 10:30, 11:00), com 10:00 selecionado;
- "Escolha o barbeiro", com "Qualquer barbeiro" selecionado por padrão;
- "Selecionado: ..." abaixo de cada grupo e o botão "Ver disponibilidade" habilitado.

Acessibilidade visível: botões ≥ 44×44 px com 8 px de espaço; rótulos visíveis; seleção em texto (✓ e "Selecionado"), não só por cor; foco com contorno azul de 3 px (aperte Tab).

*Extra:* `http://localhost:5000/` mostra o botão **desabilitado** e o texto "Selecione serviço, data e horário para continuar".

### 2. Tela 2, disponibilidade (caso b)
**URL:** `http://localhost:5000/disponibilidade?P&hora=10:00&barbeiro=1`. Depois toque em "Ver outros barbeiros livres às 10:00".

O que deve aparecer:
- resumo "Corte + barba – 45 min · 14/11/2026 às 10:00";
- alerta com triângulo: "Barbeiro 1 não está livre às 10:00";
- botão "Entrar na fila para o Barbeiro 1 às 10:00";
- lista aberta com "Barbeiro 2 – 10:00" e "Barbeiro 3 – 10:00";
- link "Voltar".

Acessibilidade visível: ícone, título e cor (a cor só reforça); botões ≥ 44 px com 8 px entre eles; a lista abre por teclado (Enter no "Ver outros...").

*Extras (os outros casos):*

| Caso | URL | O que deve aparecer |
|---|---|---|
| a | `/disponibilidade?P&hora=10:00&barbeiro=2` | "Barbeiro 2 está livre às 10:00" e "Continuar com Barbeiro 2" |
| c | `/disponibilidade?P&hora=10:00&barbeiro=qualquer` | "Barbeiro 2 – 10:00" e "Barbeiro 3 – 10:00" |
| d | `/disponibilidade?P&hora=11:00&barbeiro=qualquer` | "Nenhum barbeiro está livre às 11:00" e "Entrar na fila para 11:00" |

### 3. Tela 3, seus dados (com erro)
**URL:** `http://localhost:5000/dados?P&hora=10:00&barbeiro=2&modo=confirmacao`

Passos: em **Nome**, digite `Cliente Exemplo`. Em **Telefone (com DDD)**, digite `51 9000`. Toque em **Confirmar agendamento**.

O que deve aparecer:
- título "Seus dados" e resumo "Corte + barba – 45 min · Barbeiro 2 · 14/11/2026 às 10:00";
- campos "Nome" e "Telefone (com DDD)" com rótulos visíveis;
- erro com ícone e o texto "Telefone incompleto. Informe DDD e número, como 51 90000-0000", com borda de 3 px no campo e o foco no telefone;
- link "Voltar".

Acessibilidade visível: erro com ícone, texto e correção (`aria-live`); foco no campo com erro; rótulo não substituído pelo placeholder.

*Extra (modo fila):* `/dados?P&hora=11:00&barbeiro=qualquer&modo=fila_horario`. O resumo começa com "Fila de espera · ..." e o botão é "Entrar na fila de espera". Os campos aparecem vazios, com os exemplos só como placeholder.

### 4. Tela 4, resultado (confirmado)
**Caminho:** corrija o telefone na Tela 3 para `51 90000-0000` e confirme. Ou abra `/resultado/confirmado?P&hora=10:00&barbeiro=2`.

O que deve aparecer:
- alerta verde com check e "Agendamento confirmado";
- tabela com Serviço ("Corte + barba – 45 min"), Barbeiro ("Barbeiro 2"), Data ("14/11/2026") e Hora ("10:00");
- botão "Voltar ao início".

Acessibilidade visível: ícone, título (h1) e texto (a cor só reforça); título anunciado (`role="status"`); botão ≥ 44 px. A URL não contém nome nem telefone.

*Extras (filas):*

| Estado | URL | O que deve aparecer |
|---|---|---|
| fila_horario | `/resultado/fila_horario?P&hora=11:00&barbeiro=qualquer` | "Você está na fila de espera para 14/11/2026 às 11:00" e "Vamos chamar você pelo WhatsApp se surgir vaga em qualquer barbeiro neste horário." |
| fila_barbeiro | `/resultado/fila_barbeiro?P&hora=10:00&barbeiro=1` | "Você está na fila do Barbeiro 1 para 14/11/2026 às 10:00" e "Vamos chamar você pelo WhatsApp se o Barbeiro 1 liberar este horário." |

## Conferências antes de entregar
- Lighthouse (Mobile → Accessibility) em cada tela: meta ≥ 90.
- Zoom de 200% (Ctrl +): sem corte e sem rolagem horizontal.
- Só teclado: Tab, Shift+Tab e Enter na ordem visual, com foco visível.
- Nenhuma data aparece em mm/dd/aaaa.
