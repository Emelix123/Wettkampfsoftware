/* Auto-Save der Eingabemaske.
 *
 * Jedes Versuchs-<form data-autosave> wird beim Tippen (entprellt) bzw. beim
 * Aendern der "gueltig"-Checkbox automatisch per fetch() gespeichert — ohne
 * Seiten-Reload, ohne Enter, ohne dass die Seite nach oben springt.
 *
 * Der Server antwortet auf X-Requested-With: fetch mit JSON
 * ({score, status, ist_gueltig, updated_at, warn|error}); daraus werden das
 * Score-Badge und der optimistische Sperr-Token (updated_at) aktualisiert.
 */
(function () {
  "use strict";
  var DEBOUNCE_MS = 700;

  function statusEl(form) {
    var el = form.querySelector(".save-status");
    if (!el) {
      el = document.createElement("span");
      el.className = "save-status text-xs ml-2";
      var anchor = form.querySelector("[data-save-anchor]") ||
                   form.querySelector('button:not([formaction])');
      if (anchor && anchor.parentNode) {
        anchor.parentNode.insertBefore(el, anchor.nextSibling);
      } else {
        form.appendChild(el);
      }
    }
    return el;
  }

  function setStatus(form, text, cls) {
    var el = statusEl(form);
    el.textContent = text;
    el.className = "save-status text-xs ml-2 " + (cls || "");
  }

  function updateBadge(form, data) {
    var badge = form.querySelector(".score-badge");
    if (!badge) return;
    if (data.ist_gueltig === false) {
      badge.textContent = "Fehlversuch";
      badge.className = "score-badge badge badge-red";
    } else if (data.score !== null && data.score !== undefined) {
      badge.textContent = "Score: " + data.score;
      badge.className = "score-badge badge badge-green";
    } else if (data.status) {
      badge.textContent = (data.status === "In_Bewertung") ? "in Bewertung" : data.status;
      badge.className = "score-badge badge badge-amber";
    } else {
      badge.textContent = "";
      badge.className = "score-badge";
    }
  }

  function doSave(form) {
    if (form.__saving) { form.__dirty = true; return; }
    form.__saving = true;
    form.__dirty = false;
    setStatus(form, "speichert…", "text-slate-400");
    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "fetch" },
      credentials: "same-origin"
    }).then(function (r) {
      return r.json().then(function (data) { return { ok: r.ok, data: data }; });
    }).then(function (res) {
      var data = res.data || {};
      if (!res.ok || data.error) {
        setStatus(form, data.error || "Fehler beim Speichern", "text-red-600");
        return;
      }
      var ua = form.querySelector('input[name="updated_at"]');
      if (ua) ua.value = data.updated_at || "";
      updateBadge(form, data);
      setStatus(form, data.warn ? ("⚠ " + data.warn) : "✓ gespeichert",
                data.warn ? "text-amber-600" : "text-green-600");
    }).catch(function () {
      setStatus(form, "Netzwerkfehler – bitte erneut", "text-red-600");
    }).then(function () {
      form.__saving = false;
      if (form.__dirty) { doSave(form); }
    });
  }

  function wire(form) {
    var timer = null;
    function schedule() {
      clearTimeout(timer);
      timer = setTimeout(function () { doSave(form); }, DEBOUNCE_MS);
    }
    form.addEventListener("input", function (ev) {
      if (ev.target.classList.contains("score-input")) schedule();
    });
    form.addEventListener("change", function (ev) {
      if (ev.target.name === "ist_gueltig") { clearTimeout(timer); doSave(form); }
    });
    form.addEventListener("submit", function (ev) {
      // Loeschen/Zuruecksetzen/Slot-Delete (Buttons mit formaction) normal posten
      if (ev.submitter && ev.submitter.getAttribute("formaction")) return;
      ev.preventDefault();
      clearTimeout(timer);
      doSave(form);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form[data-autosave]").forEach(wire);
  });
})();
