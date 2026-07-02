# Accessible CKAN Pagination Design

## Scope

Enhance every CKAN pagination rendered as `.pagination` across public and
administrative pages. Preserve CKAN's server-generated links and query
parameters, including custom parameters such as `resource_page`.

The experimental `artesp-design-system` pagination is explicitly out of scope.

## Architecture

Use progressive enhancement in the active ARTESP theme. The existing CKAN
pager remains the server-rendered fallback. A small theme JavaScript module
reads the current page, total pages, and destination URL pattern from each
pager, calculates the desired items, and replaces its list contents with
accessible controls.

This avoids monkeypatching `ckan.lib.pagination.Page` and avoids overriding
every CKAN template that calls `page.pager()`.

## Pagination Model

`getPaginationItems(currentPage, totalPages)` is a pure function returning
explicit objects:

- `{ type: "prev", page }`
- `{ type: "page", page, current }`
- `{ type: "ellipsis", key: "left" | "right" }`
- `{ type: "next", page }`

When `totalPages <= 6`, every page is returned. For larger totals, preserve
the first page, last page, and a compact window around the current page.
Insert an ellipsis only when at least one page is hidden between visible
pages. Both left and right hidden intervals are supported.

## Navigation

Numeric, previous, and next controls retain real anchors and CKAN-generated
URLs. The enhancement infers the pagination query parameter from existing
numbered links, then uses the same URL pattern for direct jumps. A single
`navigateToPage(page)` path handles jump navigation; normal links continue to
work without JavaScript.

## Jump Popover

Each ellipsis is a `<button type="button">` with `aria-expanded`,
`aria-controls`, and `aria-label="Ir para uma página específica"`. Activating
it opens one small local popover without changing pagination layout.

The popover contains:

- label `Ir para página`;
- numeric input with integer step and translated accessible label;
- button `Ir`;
- inline validation message `Informe uma página entre 1 e X`.

Opening focuses the input. Enter confirms. Escape and outside click close it.
Closing returns focus to the ellipsis trigger. A valid page navigates and
clears the field; invalid input stays open and announces the error.

Only one popover can remain open at a time. Its position is adjusted so it
stays within the viewport on small screens.

## Visual Design

Use the approved compact option:

- `36px` consistent height and minimum width;
- `4px` gap and border radius;
- ARTESP secondary blue for interactive and active states;
- visible hover and `:focus-visible` states;
- centered numerals, chevrons, and ellipsis;
- active page retains the current blue treatment;
- disabled previous or next state follows the existing CKAN convention;
- popover uses a restrained border and shadow and is absolutely positioned.

## Accessibility

- Ensure the pagination is contained by `<nav aria-label="Paginação">`.
- Add page-specific `aria-label` values and `aria-current="page"`.
- Add `Página anterior` and `Próxima página` labels.
- Keep all clickable controls as anchors or buttons, never spans.
- Preserve visible keyboard focus.
- Use an `aria-live` validation message in the popover.

## Testing

- Unit-test visible item calculation at the beginning, middle, end, and small
  totals, including both ellipses and no false ellipses.
- Unit-test page input validation for empty, text, decimal, below-range,
  above-range, and valid values.
- DOM-test rendering semantics, focus, Enter, Escape, outside click, errors,
  and URL navigation.
- Browser-test representative public and administrative pagers at desktop and
  mobile widths.
- Confirm the original server links remain usable when enhancement is absent.
