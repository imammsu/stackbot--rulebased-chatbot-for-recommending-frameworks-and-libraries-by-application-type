/* Toggle mode gelap/terang. Default gelap; pilihan disimpan di localStorage. */
(function () {
  "use strict";
  var root = document.documentElement;

  function render() {
    var gelap = root.dataset.theme !== "light";
    var tpl = document.getElementById(gelap ? "ikon-sun" : "ikon-moon");
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      if (tpl) btn.replaceChildren(tpl.content.cloneNode(true));
      btn.setAttribute("aria-label", gelap ? "Ganti ke mode terang" : "Ganti ke mode gelap");
      btn.setAttribute("title", gelap ? "Mode terang" : "Mode gelap");
    });
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
    try { localStorage.setItem("tema-ui", root.dataset.theme); } catch (err) {}
    render();
  });

  render();
})();
