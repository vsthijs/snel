from libsnel import parse
import sys


def main():
    args = sys.argv
    argc = len(args)
    fpath = args[1]
    parse(fpath)
