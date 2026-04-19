(function () {
  function setPanelState(toggle, panel, isOpen) {
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    panel.hidden = !isOpen;

    var icon = toggle.querySelector(".artesp-ldap-toggle__icon");
    if (!icon) {
      return;
    }

    icon.classList.toggle("fa-chevron-up", isOpen);
    icon.classList.toggle("fa-chevron-down", !isOpen);
  }

  function bindToggle(toggle) {
    var panelId = toggle.getAttribute("aria-controls");
    var panel = panelId ? document.getElementById(panelId) : null;
    if (!panel) {
      return;
    }

    toggle.addEventListener("click", function () {
      var isOpen = toggle.getAttribute("aria-expanded") === "true";
      setPanelState(toggle, panel, !isOpen);
    });
  }

  function initLoginToggles() {
    var toggles = document.querySelectorAll("[data-artesp-login-toggle]");
    Array.prototype.forEach.call(toggles, bindToggle);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLoginToggles);
  } else {
    initLoginToggles();
  }
})();
