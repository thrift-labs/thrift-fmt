import sys

from ptsd.parser import Parser


def format_tree(tree):
    print(tree)
    return ''


def format_file(filename):
    with open(filename) as f:
        tree = Parser().parse(f.read())
    content = str(tree)
    with open(filename, 'w') as f:
        f.write(content)


if __name__ == '__main__':
    filename = sys.argv[1]
    print('will format:', filename)
    format_file(filename)
