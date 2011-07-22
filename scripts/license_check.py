#!/usr/bin/env python
"""
Usage: licence_check.py [options] [directory]
Finds all checked in files that suspiciously lack a MPL licensing header.

Options:
  -h, --help            show this help message and exit
  -v, --verbose         more human-friendly verbage

(c) peterbe@mozilla.com, July 2011
"""

import subprocess
from collections import defaultdict


def check(filename):
    content = open(filename).read()
    if 'MPL 1.1' not in content:
        if content.strip():
            if len(content.splitlines()) > 1:
                return True


def search(dir):
    command = "git ls-files %s | grep -v vendor-local | "\
              " grep -E '\.(js|css|py|txt|html)$'" % dir
    out, err = subprocess.Popen(command, shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE
                                ).communicate()
    for filename in out.splitlines():
        if check(filename):
            yield filename


def main(*args):
    args = list(args)
    verbose = False
    if '-v' in args:
        args.remove('-v')
        verbose = True
    if '--verbose' in args:
        args.remove('--verbose')
        verbose = True

    if '-h' in args or '--help' in args:
        print __doc__
        return 1
    groups = defaultdict(list)
    if not args:
        args = ('apps',)
    for arg in args:
        for filename in search(arg):
            groups[filename.split('.')[-1]].append(filename)

    if verbose:
        print sum(len(x) for x in groups.values()), "suspicious files found"
    for ext in sorted(groups):
        if verbose:
            print ext.upper()
        for name in groups[ext]:
            print name
        if verbose:
            print

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(*sys.argv[1:]))
