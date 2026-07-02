# Accessible CKAN Pagination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Progressively enhance every active CKAN pager with consistent compact controls and accessible direct-page jump popovers.

**Architecture:** Keep CKAN's server-rendered anchors as the no-JavaScript fallback. Add one dependency-free JavaScript module that parses each `.pagination`, derives its URL pattern, uses pure calculation and validation functions, then renders accessible controls. Add one focused CSS module for the approved 36px visual treatment and fixed-position popover.

**Tech Stack:** CKAN 2.11, Bootstrap-compatible HTML, vanilla JavaScript, Node `node:test`, CSS, Chrome DevTools Protocol

---

### Task 1: Pure pagination logic

**Files:**
- Create: `ckanext/artesp_theme/assets/js/pagination.js`
- Create: `ckanext/artesp_theme/tests/js/pagination.test.js`

- [ ] **Step 1: Write failing tests for visible items**

Test totals up to six, first-page right ellipsis, middle dual ellipses, last-page left ellipsis, and adjacency without a false ellipsis. Assert explicit objects such as `{ type: "page", page: 1, current: true }` and `{ type: "ellipsis", key: "right" }`.

- [ ] **Step 2: Run tests and verify the missing module failure**

Run `node --test ckanext/artesp_theme/tests/js/pagination.test.js` and expect failure because `assets/js/pagination.js` does not exist.

- [ ] **Step 3: Implement `getPaginationItems`**

Return `prev`, `page`, `ellipsis`, and `next` objects. Show all pages when `totalPages <= 6`; otherwise preserve first, last, current neighbors, and three edge pages. Insert ellipses only when the gap between visible pages exceeds one.

- [ ] **Step 4: Add validation tests**

Assert `validatePageInput` rejects empty, text, decimal, zero, negative, and above-total values and accepts integer strings within `1..totalPages`.

- [ ] **Step 5: Implement `validatePageInput` and rerun Node tests**

Return `{ valid: true, page }` for valid input and `{ valid: false, message: "Informe uma página entre 1 e X" }` otherwise.

### Task 2: Global progressive enhancement

**Files:**
- Modify: `ckanext/artesp_theme/assets/js/pagination.js`
- Modify: `ckanext/artesp_theme/assets/webassets.yml`
- Test: `ckanext/artesp_theme/tests/js/pagination.test.js`

- [ ] **Step 1: Test URL parameter inference**

Use representative `page`, `resource_page`, and filtered URLs. Verify hidden-page destinations preserve every unrelated query parameter.

- [ ] **Step 2: Implement URL derivation**

Read numeric anchors before rebuilding the list, infer the query parameter whose values track page labels, retain known URLs, and build hidden-page URLs from the same base.

- [ ] **Step 3: Render semantic controls**

Wrap each pager in `<nav aria-label="Paginação">`, render numeric anchors with page labels, mark the current page with `aria-current="page"`, label previous/next anchors, and render each ellipsis as a `button type="button"`.

- [ ] **Step 4: Implement the jump popover**

Create the translated label, integer input, `Ir` button, and `aria-live` error. Implement autofocus, Enter, Escape, outside click, one-open-popover behavior, input reset, focus return, and valid URL navigation.

- [ ] **Step 5: Register the JavaScript asset**

Add `js/pagination.js` to `artesp-theme-js` after the existing focused modules.

### Task 3: Compact visual system and browser verification

**Files:**
- Create: `ckanext/artesp_theme/assets/css/modules/pagination.css`
- Modify: `ckanext/artesp_theme/assets/webassets.yml`

- [ ] **Step 1: Add compact control styles**

Use 36px height/minimum width, 4px radius/gap, centered content, consistent border, ARTESP secondary blue active state, and visible hover/focus-visible/disabled states.

- [ ] **Step 2: Add non-shifting popover styles**

Use fixed positioning, constrained width, discreet border/shadow, compact form controls, and `max-width: calc(100vw - 16px)`.

- [ ] **Step 3: Register the CSS asset**

Add `css/modules/pagination.css` after `components.css` so focused overrides win consistently.

- [ ] **Step 4: Run automated verification**

Run Node tests, the focused CKAN pagination pytest slice, and `git diff --check`.

- [ ] **Step 5: Run browser verification**

Verify first, middle, and last pages; one and two ellipses; Enter, Escape, outside click, invalid input, focus transfer, direct navigation, no layout shift, and viewport containment at 375px and 1280px.

- [ ] **Step 6: Leave functional changes uncommitted for review**

Report implementation decisions and manual test evidence. Commit only when requested.
