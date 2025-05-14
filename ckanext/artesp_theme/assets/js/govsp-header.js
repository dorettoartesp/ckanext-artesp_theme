// JavaScript for São Paulo Government Header
document.addEventListener('DOMContentLoaded', function() {
  const topoGlobal = document.querySelector('#topbarGlobal');
  const BtnDigital = document.querySelectorAll('.govsp-link.digital');

  if (BtnDigital) {
    for (var i = 0; i < BtnDigital.length; i++) {
      var elemento = BtnDigital[i];
        if (elemento) {
          elemento.remove();
        }
    }
  }

  let kebabGov = document.querySelector('.govsp-kebab'),
    dropdownGov = document.querySelector('.govsp-dropdown');

  if(kebabGov && dropdownGov){
    // Initialize dropdown state
    dropdownGov.classList.remove('govsp-active');
    dropdownGov.setAttribute("aria-hidden", "true");
    kebabGov.setAttribute("aria-expanded", "false");

    // Add click event listener
    kebabGov.addEventListener('click', function (e) {
      e.preventDefault();
      dropdownGov.classList.toggle('govsp-active');
      kebabGov.classList.toggle('govsp-active');

      if(topoGlobal) {
        topoGlobal.classList.toggle('govsp-active');
      }

      if (dropdownGov.getAttribute("aria-hidden") === "true") {
          dropdownGov.setAttribute("aria-hidden", "false");
          kebabGov.setAttribute("aria-expanded", "true");
      } else {
          dropdownGov.setAttribute("aria-hidden", "true");
          kebabGov.setAttribute("aria-expanded", "false");
      }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function (e) {
      if (dropdownGov.classList.contains('govsp-active') &&
          !kebabGov.contains(e.target) &&
          !dropdownGov.contains(e.target)) {
        dropdownGov.classList.remove('govsp-active');
        kebabGov.classList.remove('govsp-active');
        dropdownGov.setAttribute("aria-hidden", "true");
        kebabGov.setAttribute("aria-expanded", "false");
      }
    });
  }
});
