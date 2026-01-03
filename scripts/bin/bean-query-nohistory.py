#!/usr/bin/env python3
import sys

import beanquery.shell as shell


def main() -> None:
    # Disable readline to avoid history file errors in some environments.
    shell.readline = None
    shell.main.main(args=sys.argv[1:], prog_name="bean-query")


if __name__ == "__main__":
    main()
