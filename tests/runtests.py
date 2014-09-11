#!/usr/bin/env python

import sys
import glob
import os

from utils import run_tests

def main():
    test_dir = os.path.dirname(sys.argv[0])
    test_file_pattern = os.path.join(test_dir, 'test_*.py')
    test_files = [os.path.basename(f) for f in glob.glob(test_file_pattern)]
    test_modules = [f[:-3] for f in test_files]
    run_tests(test_modules)

if __name__ == '__main__':
    main()
