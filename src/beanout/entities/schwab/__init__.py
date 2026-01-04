"""Schwab bank statement parser.

This package provides parsing support for Schwab bank statements in JSON and XML formats.

Organization:
- config.py: Configuration dataclass for account settings
- json_parser.py: JSON format parser
- xml_parser.py: XML format parser
- parser.py: Main public API module
"""

from beanout.entities.schwab.parser import *  # noqa: F401, F403
