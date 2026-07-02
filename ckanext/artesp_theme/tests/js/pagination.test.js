const test = require("node:test");
const assert = require("node:assert/strict");

const {
  createPageUrl,
  getPaginationItems,
  validatePageInput,
} = require("../../assets/js/pagination.js");

function compact(items) {
  return items.map((item) => {
    if (item.type === "ellipsis") return `ellipsis:${item.key}`;
    if (item.type === "page") return `page:${item.page}${item.current ? ":current" : ""}`;
    return `${item.type}:${item.page}${item.disabled ? ":disabled" : ""}`;
  });
}

test("shows every page when total is six or less", () => {
  assert.deepEqual(compact(getPaginationItems(3, 6)), [
    "prev:2",
    "page:1",
    "page:2",
    "page:3:current",
    "page:4",
    "page:5",
    "page:6",
    "next:4",
  ]);
});

test("shows a right ellipsis near the beginning", () => {
  assert.deepEqual(compact(getPaginationItems(1, 20)), [
    "prev:1:disabled",
    "page:1:current",
    "page:2",
    "page:3",
    "ellipsis:right",
    "page:20",
    "next:2",
  ]);
});

test("shows two ellipses in the middle", () => {
  assert.deepEqual(compact(getPaginationItems(6, 20)), [
    "prev:5",
    "page:1",
    "ellipsis:left",
    "page:5",
    "page:6:current",
    "page:7",
    "ellipsis:right",
    "page:20",
    "next:7",
  ]);
});

test("shows a left ellipsis near the end", () => {
  assert.deepEqual(compact(getPaginationItems(20, 20)), [
    "prev:19",
    "page:1",
    "ellipsis:left",
    "page:18",
    "page:19",
    "page:20:current",
    "next:20:disabled",
  ]);
});

test("does not use ellipsis for a single hidden page", () => {
  assert.deepEqual(compact(getPaginationItems(4, 7)), [
    "prev:3",
    "page:1",
    "page:2",
    "page:3",
    "page:4:current",
    "page:5",
    "page:6",
    "page:7",
    "next:5",
  ]);
});

test("validates direct page input", () => {
  const invalid = ["", "abc", "1.5", "0", "-2", "21"];
  invalid.forEach((value) => {
    assert.deepEqual(validatePageInput(value, 20), {
      valid: false,
      message: "Informe uma página entre 1 e 20",
    });
  });
  assert.deepEqual(validatePageInput(" 8 ", 20), { valid: true, page: 8 });
});

test("builds hidden-page URLs with the existing page parameter", () => {
  const pageLinks = [
    { page: 1, href: "https://example.test/resources?format=CSV&page=1" },
    { page: 2, href: "https://example.test/resources?format=CSV&page=2" },
  ];
  assert.equal(
    createPageUrl(pageLinks, 8, "https://example.test/resources?format=CSV"),
    "https://example.test/resources?format=CSV&page=8",
  );

  const resourceLinks = [
    { page: 2, href: "https://example.test/dataset/teste?resource_q=mapa&resource_page=2" },
    { page: 3, href: "https://example.test/dataset/teste?resource_q=mapa&resource_page=3" },
  ];
  assert.equal(
    createPageUrl(resourceLinks, 12, "https://example.test/dataset/teste?resource_q=mapa"),
    "https://example.test/dataset/teste?resource_q=mapa&resource_page=12",
  );
});
