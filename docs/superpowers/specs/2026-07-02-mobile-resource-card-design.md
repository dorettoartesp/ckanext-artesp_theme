# Mobile Resource Card Design

## Scope

Improve resource selection on dataset pages only on viewports narrower than
576px. Desktop and tablet layouts at 576px or wider remain unchanged.

## Interaction

- The entire resource card opens the existing resource detail URL.
- The existing title link remains the semantic and keyboard-accessible link.
- A CSS-only expanded hit area covers the card; no JavaScript navigation is
  introduced.
- The desktop `Explore` action remains unchanged. It is already hidden below
  576px, so there is no competing action inside the mobile hit area.

## Presentation

- Add a subtle shadow, border, 6px radius, and stable internal spacing.
- Provide visible focus and pressed feedback without relying only on color.
- Scope every new rule to `max-width: 575.98px`.

## Implementation

Add a dedicated class to the resource title link. On mobile, position the
resource item relatively and expand the link pseudo-element across the card.
Keep content above the card background and preserve current resource metadata.

## Verification

- Template test confirms the semantic link class is rendered.
- Existing resource pagination and translation tests remain green.
- Browser checks at 375px confirm the card shadow and full-card navigation.
- Browser checks at 576px or wider confirm the existing desktop behavior.
