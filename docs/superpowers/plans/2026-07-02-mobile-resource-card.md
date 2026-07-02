# Mobile Resource Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each resource item a clearly selectable, fully clickable card on viewports narrower than 576px.

**Architecture:** Keep the existing title anchor as the sole navigation element and expand its pseudo-element over the card on mobile. Add presentation and interaction states in the existing component stylesheet; desktop markup and behavior remain unchanged.

**Tech Stack:** CKAN 2.11, Jinja2, CSS, pytest, Chrome headless

---

### Task 1: Mobile resource card

**Files:**
- Modify: `ckanext/artesp_theme/templates/package/snippets/resource_item.html`
- Modify: `ckanext/artesp_theme/assets/css/modules/components.css`
- Test: `ckanext/artesp_theme/tests/app/test_dataset_resource_pagination.py`

- [ ] **Step 1: Write the failing template test**

Add this assertion to `test_resource_list_renders_server_side_search_and_pagination`:

```python
assert 'class="heading resource-card-link"' in html
```

- [ ] **Step 2: Run the focused test and verify failure**

Run:

```bash
docker exec -w /srv/app/src_extensions/ckanext-artesp_theme \
  artesp-ckan-ui-ckan-dev-1 pytest -q \
  ckanext/artesp_theme/tests/app/test_dataset_resource_pagination.py \
  -k renders_server_side
```

Expected: FAIL because `resource-card-link` is absent.

- [ ] **Step 3: Add semantic link hook and mobile styles**

Change the title link to:

```jinja2
<a class="heading resource-card-link" href="{{ url }}" title="{{ res.name or res.description }}">
```

Add a `max-width: 575.98px` rule that gives `.resource-item` a border, 6px radius, subtle shadow, padding, and pressed/focus feedback. Set `.resource-card-link::after` to `position: absolute; inset: 0` so the existing link covers the card without JavaScript.

- [ ] **Step 4: Run the app test file**

Run the test file from Step 2 without `-k`.

Expected: all tests PASS.

- [ ] **Step 5: Verify browser behavior**

Use Chrome headless at `375x800` and confirm the resource item has a shadow and that a click near the card edge navigates to its resource URL. Repeat at `1280x800` and confirm desktop styling remains unchanged.

- [ ] **Step 6: Leave implementation uncommitted for review**

Report test and browser evidence. Do not commit functional changes until requested.
