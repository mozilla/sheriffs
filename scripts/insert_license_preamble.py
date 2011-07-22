#!/usr/bin/env python
"""
Usage: %(file)s file1 [, file2]
Inserts a suitable MPL preamble into the top of the file if it's not
already there.

Options:
    n/a

(c) peterbe@mozilla.com, July 2011
""" % dict(
  file=__file__
)

START = '***** BEGIN LICENSE BLOCK *****'
FINISH = '***** END LICENSE BLOCK *****'
import re
import os
txt_file_path = os.path.join(os.path.dirname(
  os.path.abspath(__file__)),
  'default_preamble.txt')
try:
    PREAMBLE = open(txt_file_path).read().strip()
except IOError:
    print >>sys.stderr, "Create a file called 'default_preamble.txt' "\
                        "and place it in %s\n" % \
                        os.path.dirname(os.path.abspath(__file__))
    raise

preamble_py = '\n'.join('# %s' % x for x in PREAMBLE.splitlines())
preamble_html = '{#\n<!-- ' + '\n   - '.join(PREAMBLE.splitlines()) + '\n -->\n#}'
preamble_js = '/* ' + '\n * '.join(PREAMBLE.splitlines()) + ' */'
preamble_txt = '{% comment %}\n<!-- ' + '\n   - '.join(PREAMBLE.splitlines()) + '\n -->\n{% endcomment %}'

def wrap(extension):
    if extension == '.py':
        return preamble_py
    if extension == '.html':
        return preamble_html
    if extension == '.js' or extension == '.css':
        return preamble_js
    if extension == '.txt':
        return preamble_txt
    raise NotImplementedError(extension)

def fix(filename):
    extension = os.path.splitext(filename)[1]
    content = open(filename).read()
    if not content.strip():
        return

    lines = content.splitlines()
    if extension == '.py':
        # check that there's meat
        if len([x for x in lines
                if not x.startswith('#')]) <= 1:
            return
        if '#!/' in lines[0]:
            return

    preamble = wrap(extension)
    _fixed = False
    if START in content:
        regex = re.compile('%s(.*?)%s'% (re.escape(START),
                                         re.escape(FINISH)), re.DOTALL)
        existing = regex.findall(content)[0]
        new = regex.findall(preamble)[0]
        if new == existing:
            return
        else:
            content = content.replace(existing, new)
            _fixed = True

    if not _fixed:
        content = "%s\n\n%s" % (preamble, content)
        content = content.strip() + '\n'

    with file(filename, 'w') as f:
        f.write(content)

    return True

def run(*args):

    if not args:
        print __doc__
        return 1

    for arg in args:
        if fix(arg):
            print "FIXED", arg
        else:
            print "IGNORED", arg

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
