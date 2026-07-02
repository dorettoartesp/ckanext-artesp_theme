(function (root, factory) {
  "use strict";

  var api = factory();

  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }

  if (root) {
    root.artespPagination = api;
  }
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";

  var ALL_PAGES_THRESHOLD = 6;

  function clamp(value, minimum, maximum) {
    return Math.min(Math.max(value, minimum), maximum);
  }

  function getPaginationItems(currentPage, totalPages) {
    var total = Math.max(1, Math.trunc(Number(totalPages) || 1));
    var current = clamp(Math.trunc(Number(currentPage) || 1), 1, total);
    var visiblePages = new Set();
    var items = [];

    if (total <= ALL_PAGES_THRESHOLD) {
      for (var page = 1; page <= total; page += 1) {
        visiblePages.add(page);
      }
    } else {
      visiblePages.add(1);
      visiblePages.add(total);
      visiblePages.add(current - 1);
      visiblePages.add(current);
      visiblePages.add(current + 1);

      if (current <= 2) {
        visiblePages.add(2);
        visiblePages.add(3);
      }
      if (current >= total - 1) {
        visiblePages.add(total - 2);
        visiblePages.add(total - 1);
      }
    }

    var pages = Array.from(visiblePages)
      .filter(function (page) {
        return page >= 1 && page <= total;
      })
      .sort(function (left, right) {
        return left - right;
      });

    items.push({
      type: "prev",
      page: Math.max(1, current - 1),
      disabled: current === 1,
    });

    pages.forEach(function (page, index) {
      var previous = pages[index - 1];
      var gap = previous ? page - previous : 0;

      if (gap === 2) {
        items.push({ type: "page", page: previous + 1, current: false });
      } else if (gap > 2) {
        items.push({
          type: "ellipsis",
          key: page < current ? "left" : "right",
        });
      }

      items.push({ type: "page", page: page, current: page === current });
    });

    items.push({
      type: "next",
      page: Math.min(total, current + 1),
      disabled: current === total,
    });

    return items;
  }

  function invalidPage(totalPages) {
    return {
      valid: false,
      message: "Informe uma página entre 1 e " + totalPages,
    };
  }

  function validatePageInput(value, totalPages) {
    var total = Math.max(1, Math.trunc(Number(totalPages) || 1));
    var normalized = String(value == null ? "" : value).trim();

    if (!/^\d+$/.test(normalized)) {
      return invalidPage(total);
    }

    var page = Number(normalized);
    if (!Number.isSafeInteger(page) || page < 1 || page > total) {
      return invalidPage(total);
    }

    return { valid: true, page: page };
  }

  function inferPageParameter(pageLinks, currentHref) {
    var scores = {};

    pageLinks.forEach(function (link) {
      var url = new URL(link.href, currentHref);
      url.searchParams.forEach(function (value, key) {
        if (value === String(link.page)) {
          scores[key] = (scores[key] || 0) + 1;
        }
      });
    });

    return Object.keys(scores).sort(function (left, right) {
      return scores[right] - scores[left];
    })[0] || "page";
  }

  function createPageUrl(pageLinks, page, currentHref) {
    var knownLink = pageLinks.find(function (link) {
      return link.page === page;
    });
    if (knownLink) {
      return new URL(knownLink.href, currentHref).href;
    }

    var baseHref = pageLinks.length ? pageLinks[0].href : currentHref;
    var url = new URL(baseHref, currentHref);
    url.searchParams.set(inferPageParameter(pageLinks, currentHref), String(page));
    return url.href;
  }

  var activeJump = null;
  var jumpSequence = 0;

  function createControl(item, pageLinks, currentHref) {
    var listItem = document.createElement("li");
    listItem.className = "page-item";

    if (item.type === "page" && item.current) {
      var current = document.createElement("span");
      current.className = "page-link";
      current.setAttribute("aria-current", "page");
      current.setAttribute("aria-label", "Página " + item.page + ", atual");
      current.textContent = String(item.page);
      listItem.classList.add("active");
      listItem.appendChild(current);
      return listItem;
    }

    var label;
    var text;
    if (item.type === "prev") {
      label = "Página anterior";
      text = "«";
    } else if (item.type === "next") {
      label = "Próxima página";
      text = "»";
    } else {
      label = "Ir para página " + item.page;
      text = String(item.page);
    }

    if (item.disabled) {
      var disabled = document.createElement("button");
      disabled.className = "page-link";
      disabled.type = "button";
      disabled.disabled = true;
      disabled.setAttribute("aria-label", label);
      disabled.textContent = text;
      listItem.classList.add("disabled");
      listItem.appendChild(disabled);
      return listItem;
    }

    var link = document.createElement("a");
    link.className = "page-link";
    link.href = createPageUrl(pageLinks, item.page, currentHref);
    link.setAttribute("aria-label", label);
    link.textContent = text;
    listItem.appendChild(link);
    return listItem;
  }

  function positionPopover(jump) {
    var triggerRect = jump.trigger.getBoundingClientRect();
    var popoverRect = jump.popover.getBoundingClientRect();
    var gutter = 8;
    var left = triggerRect.left + (triggerRect.width - popoverRect.width) / 2;
    var top = triggerRect.bottom + gutter;

    left = clamp(left, gutter, window.innerWidth - popoverRect.width - gutter);
    if (top + popoverRect.height > window.innerHeight - gutter) {
      top = triggerRect.top - popoverRect.height - gutter;
    }

    jump.popover.style.left = Math.max(gutter, left) + "px";
    jump.popover.style.top =
      clamp(
        top,
        gutter,
        Math.max(gutter, window.innerHeight - popoverRect.height - gutter),
      ) + "px";
  }

  function closeJump(jump, returnFocus) {
    if (!jump || jump.popover.hidden) return;

    jump.popover.hidden = true;
    jump.trigger.setAttribute("aria-expanded", "false");
    jump.input.value = "";
    jump.input.removeAttribute("aria-invalid");
    jump.error.hidden = true;
    jump.error.textContent = "";
    if (activeJump === jump) activeJump = null;
    if (returnFocus) jump.trigger.focus();
  }

  function openJump(jump) {
    if (activeJump && activeJump !== jump) closeJump(activeJump, false);

    jump.popover.hidden = false;
    jump.trigger.setAttribute("aria-expanded", "true");
    activeJump = jump;
    positionPopover(jump);
    window.requestAnimationFrame(function () {
      jump.input.focus();
    });
  }

  function createJumpControl(item, totalPages, pageLinks, currentHref) {
    jumpSequence += 1;
    var id = "pagination-jump-" + jumpSequence;
    var inputId = id + "-input";
    var errorId = id + "-error";
    var listItem = document.createElement("li");
    var trigger = document.createElement("button");
    var popover = document.createElement("div");
    var form = document.createElement("form");
    var label = document.createElement("label");
    var controls = document.createElement("div");
    var input = document.createElement("input");
    var submit = document.createElement("button");
    var error = document.createElement("p");

    listItem.className = "page-item pagination-jump";
    trigger.className = "page-link pagination-ellipsis";
    trigger.type = "button";
    trigger.textContent = "...";
    trigger.setAttribute("aria-label", "Ir para uma página específica");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-controls", id);

    popover.className = "pagination-jump-popover";
    popover.id = id;
    popover.hidden = true;
    popover.setAttribute("role", "dialog");
    popover.setAttribute("aria-label", "Ir para página");

    form.className = "pagination-jump-form";
    form.noValidate = true;
    label.htmlFor = inputId;
    label.textContent = "Ir para página";
    controls.className = "pagination-jump-controls";

    input.id = inputId;
    input.className = "form-control";
    input.type = "number";
    input.inputMode = "numeric";
    input.min = "1";
    input.max = String(totalPages);
    input.step = "1";
    input.required = true;
    input.setAttribute("aria-describedby", errorId);

    submit.className = "btn btn-primary";
    submit.type = "submit";
    submit.textContent = "Ir";

    error.id = errorId;
    error.className = "pagination-jump-error";
    error.hidden = true;
    error.setAttribute("aria-live", "polite");

    controls.appendChild(input);
    controls.appendChild(submit);
    form.appendChild(label);
    form.appendChild(controls);
    form.appendChild(error);
    popover.appendChild(form);
    listItem.appendChild(trigger);
    listItem.appendChild(popover);

    var jump = {
      error: error,
      input: input,
      popover: popover,
      trigger: trigger,
    };

    trigger.addEventListener("click", function () {
      if (popover.hidden) openJump(jump);
      else closeJump(jump, true);
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var result = validatePageInput(input.value, totalPages);
      if (!result.valid) {
        input.setAttribute("aria-invalid", "true");
        error.textContent = result.message;
        error.hidden = false;
        input.focus();
        return;
      }

      closeJump(jump, false);
      window.location.assign(createPageUrl(pageLinks, result.page, currentHref));
    });

    return listItem;
  }

  function readPager(list) {
    var currentNode = list.querySelector(".active");
    var currentPage = currentNode && Number(currentNode.textContent.trim());
    var pageLinks = Array.from(list.querySelectorAll("a[href]")).reduce(
      function (links, anchor) {
        var text = anchor.textContent.trim();
        if (/^\d+$/.test(text)) {
          links.push({ page: Number(text), href: anchor.href });
        }
        return links;
      },
      [],
    );
    var pageNumbers = pageLinks.map(function (link) {
      return link.page;
    });

    if (Number.isInteger(currentPage)) pageNumbers.push(currentPage);
    if (!Number.isInteger(currentPage) || !pageNumbers.length) return null;

    return {
      currentPage: currentPage,
      pageLinks: pageLinks,
      totalPages: Math.max.apply(Math, pageNumbers),
    };
  }

  function enhancePagination(list) {
    if (list.dataset.artespPaginationEnhanced === "true") return;

    var pager = readPager(list);
    if (!pager || pager.totalPages <= 1) return;

    var currentHref = window.location.href;
    var fragment = document.createDocumentFragment();
    getPaginationItems(pager.currentPage, pager.totalPages).forEach(function (item) {
      fragment.appendChild(
        item.type === "ellipsis"
          ? createJumpControl(item, pager.totalPages, pager.pageLinks, currentHref)
          : createControl(item, pager.pageLinks, currentHref),
      );
    });

    list.replaceChildren(fragment);
    list.dataset.artespPaginationEnhanced = "true";

    var nav = list.closest("nav");
    if (!nav) {
      nav = document.createElement("nav");
      list.parentNode.insertBefore(nav, list);
      nav.appendChild(list);
    }
    nav.classList.add("artesp-pagination-nav");
    nav.setAttribute("aria-label", "Paginação");
  }

  function initialize() {
    document.querySelectorAll("ul.pagination").forEach(enhancePagination);
  }

  if (typeof window !== "undefined" && window.document) {
    document.addEventListener("click", function (event) {
      if (
        activeJump &&
        !activeJump.popover.contains(event.target) &&
        !activeJump.trigger.contains(event.target)
      ) {
        closeJump(activeJump, false);
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && activeJump) {
        closeJump(activeJump, true);
      }
    });
    window.addEventListener("resize", function () {
      if (activeJump) positionPopover(activeJump);
    });
    window.addEventListener(
      "scroll",
      function () {
        if (activeJump) positionPopover(activeJump);
      },
      true,
    );

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initialize);
    } else {
      initialize();
    }
    document.addEventListener("htmx:afterSwap", initialize);
  }

  return {
    createPageUrl: createPageUrl,
    getPaginationItems: getPaginationItems,
    initialize: initialize,
    validatePageInput: validatePageInput,
  };
});
