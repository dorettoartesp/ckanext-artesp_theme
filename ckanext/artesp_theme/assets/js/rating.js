/* Dataset rating widget interactivity */
(function () {
  "use strict";

  function initRatingWidget(root) {
    // Highlight stars on hover and selection
    var starInputs = root.querySelectorAll(
      ".artesp-rating__stars--input input[type=radio]"
    );
    starInputs.forEach(function (input) {
      input.addEventListener("change", function () {
        updateStarDisplay(root);
      });
    });

    // Highlight thumbs on selection
    var thumbInputs = root.querySelectorAll(".artesp-rating__thumb input");
    thumbInputs.forEach(function (input) {
      input.addEventListener("change", function () {
        var name = input.getAttribute("name");
        root
          .querySelectorAll(".artesp-rating__thumb input[name='" + name + "']")
          .forEach(function (sibling) {
            sibling.closest(".artesp-rating__thumb").classList.toggle(
              "artesp-rating__thumb--selected",
              sibling === input
            );
          });
      });
    });

    updateStarDisplay(root);
  }

  function updateStarDisplay(root) {
    var checked = root.querySelector(
      ".artesp-rating__stars--input input:checked"
    );
    var labels = root.querySelectorAll(".artesp-rating__star-label");
    var value = checked ? parseInt(checked.value, 10) : 0;
    labels.forEach(function (label) {
      var star = label.querySelector(".artesp-rating__star");
      var labelValue = parseInt(
        label.querySelector("input").value,
        10
      );
      star.style.color = labelValue <= value ? "#f0ad4e" : "#ccc";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".artesp-rating").forEach(initRatingWidget);
  });
})();
