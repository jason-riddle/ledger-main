# Python Style Guide (Google)

This repository follows the Google Python Style Guide. The official guide is
available at:
https://google.github.io/styleguide/pyguide.html

## Local summary
- **Imports**: Import packages/modules only (use `import x` or `from pkg import
  module`). Avoid importing individual classes/functions. Typing helpers are
  allowed from `typing` and `collections.abc`. Use full package names and avoid
  relative imports.
- **Line length**: Keep code and docstrings within 80 columns.
- **Formatting**: 4-space indentation; no tabs; use parentheses for readable
  wrapping.
- **Docstrings**: Provide docstrings for modules, classes, and functions. Use a
  short summary line, blank line, then details.
- **Exceptions**: Prefer specific exceptions. Avoid broad `except` unless
  re-raising or isolating failures at a boundary (e.g., CLI entrypoint).
- **Naming**: `lower_with_underscores` for functions/variables, `UpperCamelCase`
  for classes, `UPPER_SNAKE_CASE` for constants. Avoid overly short names.
- **Resources**: Use context managers (e.g., `with open(...)`) for files and
  other stateful resources.
- **Main**: Use `if __name__ == "__main__":` for script entrypoints.

Refer to the official guide for the full set of language and style rules.
