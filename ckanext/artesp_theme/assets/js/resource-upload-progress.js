(function () {
  "use strict";

  var BYTES_PER_MB = 1024 * 1024;

  function formatBytes(bytes) {
    if (!Number.isFinite(bytes) || bytes <= 0) {
      return "";
    }
    if (bytes < BYTES_PER_MB) {
      return Math.max(1, Math.round(bytes / 1024)) + " KB";
    }
    return (bytes / BYTES_PER_MB).toFixed(1).replace(".0", "") + " MB";
  }

  function getSelectedFile(container) {
    var input = container.querySelector('input[type="file"][name="upload"]');
    if (!input || !input.files || !input.files.length) {
      return null;
    }
    return input.files[0];
  }

  function setStatus(container, message, options) {
    var summary = container.querySelector("[data-resource-upload-file-name]");
    var meta = container.querySelector("[data-resource-upload-file-size]");
    var opts = options || {};

    container.classList.toggle("artesp-resource-upload-feedback--error", !!opts.error);

    if (summary) {
      summary.textContent = message || "";
    }
    if (meta) {
      meta.textContent = opts.meta || "";
    }
  }

  function validateSelection(container) {
    var file = getSelectedFile(container);
    var maxSizeMb = Number(container.dataset.resourceUploadMaxSizeMb || 0);
    var maxBytes = maxSizeMb * BYTES_PER_MB;
    var emptyText = container.dataset.resourceUploadEmptyText || "Nenhum arquivo selecionado";
    var readyText = container.dataset.resourceUploadReadyText || "Pronto para enviar";
    var tooLargeText = container.dataset.resourceUploadTooLargeText || "Arquivo maior que o limite permitido.";

    if (!file) {
      setStatus(container, emptyText);
      return true;
    }

    if (maxBytes && file.size > maxBytes) {
      setStatus(container, tooLargeText, {
        error: true,
        meta: file.name + " - " + formatBytes(file.size),
      });
      return false;
    }

    setStatus(container, file.name, {
      meta: readyText + " - " + formatBytes(file.size),
    });
    return true;
  }

  function setFormSubmitting(form, submitting) {
    form.dataset.artespResourceUploadSubmitting = submitting ? "true" : "false";
    form.querySelectorAll('button[type="submit"]').forEach(function (button) {
      button.disabled = submitting;
      if (submitting && !button.dataset.originalText) {
        button.dataset.originalText = button.textContent;
      }
    });
  }

  function preserveSubmitAction(form) {
    var input = form.querySelector('input[type="hidden"][name="save"][data-resource-upload-submit-action]');
    var button = document.activeElement;

    if (!button || button.form !== form || button.name !== "save") {
      button = form.querySelector('button[type="submit"][name="save"]');
    }
    if (!button) {
      return;
    }
    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = "save";
      input.dataset.resourceUploadSubmitAction = "true";
      form.appendChild(input);
    }
    input.value = button.value || "";
  }

  function showBlockingOverlay(container) {
    var overlay = container.querySelector("[data-resource-upload-overlay]");
    var message = container.querySelector("[data-resource-upload-overlay-message]");

    if (message) {
      message.textContent = container.dataset.resourceUploadSendingText || "Enviando arquivo. Aguarde.";
    }
    if (overlay) {
      overlay.hidden = false;
      document.documentElement.classList.add("artesp-resource-upload-is-blocked");
      document.body.classList.add("artesp-resource-upload-is-blocked");
    }
  }

  function bindContainer(container) {
    var form = container.closest("form");
    if (!form || container.dataset.artespUploadBound === "true") {
      return;
    }
    container.dataset.artespUploadBound = "true";

    container.addEventListener("change", function (event) {
      if (event.target && event.target.matches('input[type="file"][name="upload"]')) {
        validateSelection(container);
      }
    });

    form.addEventListener("submit", function (event) {
      if (!getSelectedFile(container)) {
        return;
      }

      if (form.dataset.artespResourceUploadSubmitting === "true") {
        event.preventDefault();
        return;
      }

      if (!validateSelection(container)) {
        event.preventDefault();
        return;
      }

      preserveSubmitAction(form);
      setFormSubmitting(form, true);
      showBlockingOverlay(container);
    });
  }

  function init() {
    document.querySelectorAll("[data-artesp-resource-upload]").forEach(bindContainer);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
