/*
 * Logika halaman chat.
 * - Mengirim pesan ke /api/chat/<tema> dengan fetch.
 * - Memformat respons daftar framework ("• Label: Nama (Bahasa), ...") menjadi
 *   kelompok + tag agar respons panjang mudah dibaca.
 * - Menampilkan pertanyaan lanjutan & quick replies (intent berkonteks).
 * Semua teks dari server dimasukkan lewat textContent (aman dari XSS).
 */
(function () {
  "use strict";

  var cfg = window.CHAT_CONFIG;
  var log = document.getElementById("log");
  var scroller = document.querySelector(".chat-main");
  var form = document.getElementById("form");
  var input = document.getElementById("input");
  var sendBtn = document.getElementById("send");
  var counter = document.getElementById("counter");
  var errorBox = document.getElementById("error");
  var typing = document.getElementById("typing");
  var resetBtn = document.getElementById("btn-reset");
  var sibuk = false;

  // ---------- utilitas DOM ----------
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function ikon(id) {
    var t = document.getElementById(id);
    return t ? t.content.cloneNode(true) : document.createTextNode("");
  }
  function gulirKeBawah() {
    requestAnimationFrame(function () { scroller.scrollTop = scroller.scrollHeight; });
  }

  // ---------- parser respons ----------
  /** Pisah berdasarkan koma tingkat atas (koma di dalam kurung diabaikan). */
  function pisahItem(teks) {
    var hasil = [], buf = "", dalam = 0;
    for (var i = 0; i < teks.length; i++) {
      var c = teks[i];
      if (c === "(") dalam++;
      if (c === ")") dalam = Math.max(0, dalam - 1);
      if (c === "," && dalam === 0) { hasil.push(buf.trim()); buf = ""; continue; }
      buf += c;
    }
    if (buf.trim()) hasil.push(buf.trim());
    return hasil;
  }

  /** "Flask (Python)" -> {nama: "Flask", bahasa: "Python"} */
  function urai(item) {
    var m = item.match(/^(.*?)\s*\(([^()]*)\)$/);
    return m ? { nama: m[1], bahasa: m[2] } : { nama: item, bahasa: "" };
  }

  /** Kembalikan elemen bubble; format kaya bila ada baris "• ". */
  function buatBubble(teks) {
    var baris = teks.split("\n").map(function (s) { return s.trim(); }).filter(Boolean);
    var adaDaftar = baris.some(function (b) { return b.indexOf("• ") === 0; });
    if (!adaDaftar) return el("div", "bubble", teks);

    var bubble = el("div", "bubble bubble--rich");
    var groups = el("ul", "groups");
    groups.setAttribute("role", "list");
    var sumber = null, introDipasang = false;

    baris.forEach(function (b) {
      if (b.indexOf("• ") === 0) {
        var isi = b.slice(2), titik = isi.indexOf(": ");
        var label = titik > -1 ? isi.slice(0, titik) : "";
        var items = pisahItem(titik > -1 ? isi.slice(titik + 2) : isi);
        var li = el("li", "group");
        if (label) li.appendChild(el("span", "group__label", label));
        var tags = el("ul", "tags");
        tags.setAttribute("role", "list");
        items.forEach(function (it) {
          var u = urai(it), tag = el("li", "tag");
          tag.appendChild(el("span", "tag__name", u.nama));
          if (u.bahasa) tag.appendChild(el("span", "tag__lang", u.bahasa));
          tags.appendChild(tag);
        });
        li.appendChild(tags);
        groups.appendChild(li);
        if (!groups.parentNode) bubble.appendChild(groups);
      } else if (/Sumber:/i.test(b) || /bukan peringkat/i.test(b)) {
        sumber = b;
      } else if (!introDipasang && !groups.parentNode) {
        bubble.appendChild(el("p", "rich__intro", b));
        introDipasang = true;
      } else {
        bubble.appendChild(el("p", "rich__note", b));
      }
    });

    if (sumber) {
      var s = el("p", "source");
      s.appendChild(ikon("ikon-info"));
      s.appendChild(el("span", null, sumber));
      bubble.appendChild(s);
    }
    return bubble;
  }

  // ---------- render pesan ----------
  function tambahPesan(peran, teks, opsi) {
    opsi = opsi || {};
    var li = el("li", "msg msg--" + peran + (opsi.error ? " msg--error" : ""));
    var avatar = el("span", "avatar avatar--sm" + (peran === "user" ? " avatar--user" : ""));
    avatar.appendChild(ikon(peran === "user" ? "ikon-user" : "ikon-bot"));
    var body = el("div", "msg__body");
    var label = el("span", "sr-only", peran === "user" ? "Kamu: " : cfg.botName + ": ");
    var bubble = peran === "bot" ? buatBubble(teks) : el("div", "bubble", teks);
    bubble.prepend(label);
    body.appendChild(bubble);

    if (opsi.quickReplies && opsi.quickReplies.length) {
      var grup = el("div", "quick-replies");
      grup.setAttribute("role", "group");
      grup.setAttribute("aria-label", "Pilihan jawaban");
      opsi.quickReplies.forEach(function (q) {
        var b = el("button", "chip chip--accent", q);
        b.type = "button";
        b.dataset.quick = q;
        grup.appendChild(b);
      });
      body.appendChild(grup);
    }
    li.appendChild(avatar);
    li.appendChild(body);
    log.appendChild(li);
    gulirKeBawah();
  }

  function nonaktifkanQuickReplyLama() {
    log.querySelectorAll("[data-quick]").forEach(function (b) { b.disabled = true; });
  }

  // ---------- input ----------
  function perbaruiInput() {
    var n = input.value.length;
    counter.textContent = n + "/" + cfg.maks;
    counter.classList.toggle("counter--warn", n > cfg.maks * 0.9);
    sendBtn.disabled = sibuk || input.value.trim() === "";
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 160) + "px";
  }
  function tampilkanGalat(pesan) {
    errorBox.textContent = pesan || "";
    errorBox.hidden = !pesan;
  }

  // ---------- kirim ----------
  function kirim(teks) {
    teks = (teks || "").trim();
    if (sibuk) return;
    if (!teks) { tampilkanGalat("Pesan tidak boleh kosong."); return; }
    if (teks.length > cfg.maks) { tampilkanGalat("Pesan maksimal " + cfg.maks + " karakter."); return; }

    tampilkanGalat("");
    nonaktifkanQuickReplyLama();
    tambahPesan("user", teks);
    input.value = "";
    sibuk = true;
    perbaruiInput();
    log.setAttribute("aria-busy", "true");

    // Indikator mengetik hanya muncul bila respons > 150 ms (hindari kedip).
    var timer = setTimeout(function () { typing.hidden = false; gulirKeBawah(); }, 150);

    fetch(cfg.apiChat, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: teks })
    })
      .then(function (res) {
        return res.json().then(function (data) { return { ok: res.ok, data: data }; });
      })
      .then(function (r) {
        if (!r.ok) {
          tampilkanGalat(r.data.error || "Terjadi kesalahan.");
          return;
        }
        var d = r.data;
        if (d.follow_up) {
          tambahPesan("bot", d.reply);
          tambahPesan("bot", d.follow_up, { quickReplies: d.quick_replies });
        } else {
          tambahPesan("bot", d.reply, { quickReplies: d.quick_replies });
        }
      })
      .catch(function () {
        tambahPesan("bot", "Gagal terhubung ke server. Periksa apakah aplikasi masih berjalan, lalu coba lagi.", { error: true });
      })
      .finally(function () {
        clearTimeout(timer);
        typing.hidden = true;
        sibuk = false;
        log.removeAttribute("aria-busy");
        perbaruiInput();
        input.focus();
      });
  }

  // ---------- event ----------
  form.addEventListener("submit", function (e) { e.preventDefault(); kirim(input.value); });
  input.addEventListener("input", function () { perbaruiInput(); if (!errorBox.hidden) tampilkanGalat(""); });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); kirim(input.value); }
  });
  document.addEventListener("click", function (e) {
    var s = e.target.closest("[data-suggest]");
    if (s) { kirim(s.dataset.suggest); return; }
    var q = e.target.closest("[data-quick]");
    if (q && !q.disabled) kirim(q.dataset.quick);
  });
  resetBtn.addEventListener("click", function () {
    fetch(cfg.apiReset, { method: "POST" }).finally(function () {
      log.replaceChildren();
      tampilkanGalat("");
      tambahPesan("bot", cfg.greeting);
      input.focus();
    });
  });

  // ---------- mulai ----------
  tambahPesan("bot", cfg.greeting);
  perbaruiInput();
})();
