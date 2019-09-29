#!/usr/bin/env python

import sys

if sys.version_info < (3, 0):
    print("Sorry, but the game does not work with Python 2.  Please upgrade to")
    print("Python 3.  Thank you!")
    sys.exit(1)

try:
    import panda3d.core
except ImportError:
    print("Cannot import panda3d.  Did you install the requirements?  Try running:")
    print("")
    print("  pip install -r requirements.txt")
    print("")
    print("Original exception was:")

from game import main

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
        main(sys.argv[1])
    else:
        main()
