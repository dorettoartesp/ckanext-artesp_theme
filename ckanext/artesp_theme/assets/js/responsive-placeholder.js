(function () {
  "use strict";

  var mobileViewport = window.matchMedia("(max-width: 575.98px)");

  function updatePlaceholder(input) {
    input.placeholder = mobileViewport.matches
      ? input.dataset.placeholderMobile
      : input.dataset.placeholderDesktop;
  }

  function initializeResponsivePlaceholders() {
    var inputs = document.querySelectorAll("[data-responsive-placeholder]");

    inputs.forEach(updatePlaceholder);
    var updateAll = function () {
      inputs.forEach(updatePlaceholder);
    };

    if (mobileViewport.addEventListener) {
      mobileViewport.addEventListener("change", updateAll);
    } else {
      mobileViewport.addListener(updateAll);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeResponsivePlaceholders);
  } else {
    initializeResponsivePlaceholders();
  }
})();
