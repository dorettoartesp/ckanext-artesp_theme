# Modular CSS Structure for ARTESP Theme

This directory contains a modular CSS structure for the ARTESP theme. The CSS has been split into logical files to make it easier to maintain and update.

## Current Status

The CKAN theme is now using a modular CSS structure. Each CSS file in this directory is defined as a separate asset in the `webassets.yml` file, and the dependencies between the files are defined using the `preload` property.

## File Structure

- `variables.css`: Contains color definitions and other CSS variables
- `base.css`: Contains base styles, typography, and general elements
- `layout.css`: Contains layout components (header, containers, grid)
- `components.css`: Contains UI components (buttons, forms, cards)
- `components-additional.css`: Contains additional UI components
- `badges.css`: Contains badge and label styling
- `footer.css`: Contains footer-specific styles
- `homepage.css`: Contains homepage-specific styles
- `homepage-datasets.css`: Contains styles for the latest datasets section
- `homepage-stats.css`: Contains styles for the statistics section
- `responsive.css`: Contains responsive media queries

## How It Works

The modular CSS structure is defined in the `webassets.yml` file in the parent directory. Each CSS file is defined as a separate asset, and the dependencies between the files are defined using the `preload` property.

The main CSS bundle (`artesp-theme-css`) is included in the base.html template using the `{% asset 'artesp_theme/artesp-theme-css' %}` tag. This bundle doesn't contain any CSS files directly, but it preloads all the other CSS files in the correct order.

## Adding or Modifying CSS

To add or modify CSS:

1. Edit the appropriate CSS file in this directory
2. Rebuild the CKAN assets:

```bash
docker exec artesp-ckan-ui-ckan-dev-1 ckan asset build
```

3. Restart the CKAN container:

```bash
docker restart artesp-ckan-ui-ckan-dev-1
```

## Adding a New CSS File

To add a new CSS file:

1. Create the new CSS file in this directory
2. Update the `webassets.yml` file to include the new CSS file
3. Rebuild the CKAN assets and restart the container as described above

## Notes

- The modular CSS structure makes it easier to maintain and update the CSS, as each file has a specific purpose and contains only related styles.
- The dependencies between the files ensure that the CSS is loaded in the correct order.
- If you encounter any issues with the modular CSS structure, check the browser console for errors and make sure the paths in the `webassets.yml` file are correct.
