# Altair Saver Change Log

## Version 0.2.0

### Behavior changes
- selenium: prefer chromedriver over geckodriver when both are available (#27)

### Bug Fixes
- selenium: altair_saver respects altair themes (#22)
- selenium: improve javascript-side error handling (#19)

## Version 0.1.0

Initial release including:

- top-level ``save()`` function
- basic export (``.vl.json``, ``.html``)
- Selenium-based export (``.vg.json``, ``.png``, ``.svg``)
- Node-based export (``.vg.json``, ``.png``, ``.svg``, ``.pdf``)