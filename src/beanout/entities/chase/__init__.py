"""Chase credit card statement parser.

This package provides parsing support for Chase credit card statements in CSV and QFX formats.

Organization:
- config.py: Configuration dataclass for account settings
- csv_parser.py: CSV format parser
- qfx_parser.py: QFX/OFX format parser
- parser.py: Main public API module
"""

from beanout.entities.chase.parser import *  # noqa: F401, F403
