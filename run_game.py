#!/usr/bin/env python

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
    if len(sys.argv) >= 2:
        main(sys.argv[1])
    else:
        main()
