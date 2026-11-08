// Tela 1: aplica a data assim que ela é escolhida (sem botão "Aplicar").
// Sem JS a página continua funcionando: a data vai junto no próximo clique.
(function () {
  var campo = document.getElementById("data");
  if (!campo || !campo.form) return;
  var espera;
  campo.addEventListener("change", function () {
    clearTimeout(espera);
    // pequena espera para não recarregar enquanto a data é digitada pelo teclado
    espera = setTimeout(function () {
      if (!campo.value) return;
      var foco = document.createElement("input");
      foco.type = "hidden";
      foco.name = "foco";
      foco.value = "data";
      campo.form.appendChild(foco);
      campo.form.submit();
    }, 700);
  });
})();
