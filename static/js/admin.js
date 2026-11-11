/* Halaman admin: salin pertanyaan tidak dikenali ke clipboard. */
(function () {
  "use strict";
  var status = document.getElementById("copy-status");

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-copy]");
    if (!btn || !navigator.clipboard) return;
    var asli = btn.innerHTML;
    navigator.clipboard.writeText(btn.dataset.copy).then(function () {
      var tpl = document.getElementById("ikon-check");
      if (tpl) btn.replaceChildren(tpl.content.cloneNode(true));
      status.textContent = "Disalin: " + btn.dataset.copy;
      setTimeout(function () { btn.innerHTML = asli; }, 1500);
    });
  });
})();
