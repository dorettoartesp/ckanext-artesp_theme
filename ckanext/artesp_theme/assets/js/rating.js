(function () {
  "use strict";

  function initRatingWidget(root) {
    initStars(root);
    initThumbs(root);
    initCommentCaptcha(root);
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

  function initFormValidation(root) {
    var form = root.querySelector(".artesp-rating__form");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      var hiddenInput = root.querySelector("input[name='overall_rating']");
      if (!hiddenInput || !hiddenInput.value) {
        e.preventDefault();
        var starsInput = root.querySelector(".artesp-rating__stars-input");
        if (starsInput) {
          starsInput.classList.add("artesp-rating__stars-input--error");
          setTimeout(function () {
            starsInput.classList.remove("artesp-rating__stars-input--error");
          }, 2500);
        }
      }
    });
  }

  function initCommentCaptcha(root) {
    var form = root.querySelector(".artesp-rating__form");
    var commentInput = root.querySelector("textarea[name='comment']");
    var captchaBox = root.querySelector(".artesp-rating__comment-captcha");

    if (!form || !commentInput || !captchaBox) return;

    function hasComment() {
      return Boolean(commentInput.value && commentInput.value.trim());
    }

    function syncCaptchaVisibility() {
      var commentPresent = hasComment();
      captchaBox.hidden = !commentPresent;
      if (!commentPresent) {
        captchaBox.classList.remove("artesp-rating__comment-captcha--error");
      }
    }

    commentInput.addEventListener("input", syncCaptchaVisibility);
    syncCaptchaVisibility();

    form.addEventListener("submit", function (e) {
      if (!hasComment()) {
        return;
      }

      var altchaWidget = captchaBox.querySelector("altcha-widget");
      var altchaInput = form.querySelector("input[name='altcha']");
      var altchaVerified = Boolean(altchaInput && altchaInput.value);

      if (!altchaWidget || !altchaVerified) {
        e.preventDefault();
        captchaBox.hidden = false;
        captchaBox.classList.add("artesp-rating__comment-captcha--error");
        captchaBox.scrollIntoView({ block: "nearest", behavior: "smooth" });
      } else {
        captchaBox.classList.remove("artesp-rating__comment-captcha--error");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".artesp-rating").forEach(function (root) {
      initRatingWidget(root);
      initFormValidation(root);
    });
  });
})();
