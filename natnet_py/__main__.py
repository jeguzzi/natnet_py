import sys

from .natnet_main import main

if __name__ == '__main__':
    # `None` is accepted by sys.exit and is equivalent to 0
    sys.exit(main())  # type: ignore[func-returns-value]
