# Altair Saver Change Log

## Version 0.5.0

- Fix bug when running as root user on linux (#59)
- node-based saver hides window warnings that were displayed when saving interactive charts
  (#53, #57)
- node-based saver now accepts ``vega_cli_options`` that will be passed to command line (#52)

## Version 0.4.0

- ``altair_saver.types`` is now a public module. (#47)
- ``altair_saver.JavascriptError`` now importable at top-level. (#46)
- Added top-level ``available_formats()`` function, which returns the set of
  available formats. (#43)

## Version 0.3.1

- Fix bug in detecting npm binary path (#42)

## Version 0.3.0

### Behavior changes

- ``save()`` now returns the serialized chart if ``fp`` is not specified (#41).
- ``fmt="json"`` now saves the input spec directly for both vega and vega-lite input.
  Additionally, the ``json`` format in ``render()`` outputs a JSON mimetype rather than
  a vega-lite mimetype (#34).
- ``render()`` and ``save()`` with HTML format now have a ``standalone`` argument
  that defaults to True for ``save()`` and False for ``render()``, so that HTML
  output will work better in a variety of notebook frontends (#33).
- HTML and Selenium output now respects embedding options set via 
  ``alt.renderers.set_embed_options`` (#30, #31).

### Maintenance
- much improved documentation & test coverage.

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