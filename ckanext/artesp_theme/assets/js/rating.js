(function () {
  "use strict";

  function initRatingWidget(root) {
    initStars(root);
    initThumbs(root);
  }

  function initStars(root) {
    var starsInput = root.querySelector(".artesp-rating__stars-input");
    if (!starsInput) return;

    var starBtns = Array.prototype.slice.call(
      starsInput.querySelectorAll(".artesp-rating__star-btn")
    );
    var hiddenInput = root.querySelector("input[name='overall_rating']");
    if (!hiddenInput) return;

    var currentValue = parseInt(starsInput.getAttribute("data-rating") || "0", 10);

    function applyFill(upTo) {
      starBtns.forEach(function (btn) {
        var v = parseInt(btn.getAttribute("data-value"), 10);
        btn.classList.toggle("filled", v <= upTo);
      });
    }

    function selectRating(value) {
      currentValue = value;
      hiddenInput.value = value;
      starsInput.setAttribute("data-rating", value);
      applyFill(value);
      starBtns.forEach(function (btn) {
        var v = parseInt(btn.getAttribute("data-value"), 10);
        btn.setAttribute("aria-checked", v === value ? "true" : "false");
      });
    }

    starBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        selectRating(parseInt(btn.getAttribute("data-value"), 10));
      });

      btn.addEventListener("mouseenter", function () {
        applyFill(parseInt(btn.getAttribute("data-value"), 10));
      });

      btn.addEventListener("mouseleave", function () {
        applyFill(currentValue);
      });

      btn.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectRating(parseInt(btn.getAttribute("data-value"), 10));
        }
      });
    });

    applyFill(currentValue);
  }

  function initThumbs(root) {
    var thumbBtns = Array.prototype.slice.call(
      root.querySelectorAll(".artesp-rating__thumb")
    );

    thumbBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var criterion = btn.getAttribute("data-criterion");
        var value = btn.getAttribute("data-value");
        var hiddenInput = root.querySelector(
          "input[name='criteria_" + criterion + "']"
        );
        var siblings = Array.prototype.slice.call(
          root.querySelectorAll(
            ".artesp-rating__thumb[data-criterion='" + criterion + "']"
          )
        );

        var wasSelected = btn.classList.contains("selected");

        siblings.forEach(function (b) {
          b.classList.remove("selected");
          b.setAttribute("aria-pressed", "false");
        });

        if (!wasSelected) {
          btn.classList.add("selected");
          btn.setAttribute("aria-pressed", "true");
          if (hiddenInput) hiddenInput.value = value;
        } else {
          if (hiddenInput) hiddenInput.value = "";
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".artesp-rating").forEach(initRatingWidget);
  });
})();
