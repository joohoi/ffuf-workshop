#!/usr/bin/env python3
import argparse
import sys

from fnmatch import fnmatch
from os.path import dirname
from urllib.parse import urlparse


def is_http(url):
    """Return true if URL scheme is http or https"""
    return urlparse(url).scheme == "http" or urlparse(url).scheme == "https"
        
def in_scope(url, scope):
    """Return true if `url` is either exactly the scope domain
    or a subdomain of it."""
    hostname = urlparse(url).hostname
    return fnmatch(hostname, "*."+scope) or fnmatch(hostname, scope) 

def print_success(url):
    """Print the URL in a format defined in the command line"""
    parsed = urlparse(url)
    if args.output == "domain":
        print(parsed.hostname)
    elif args.output == "schemedomain":
        print(parsed.scheme + "://" + parsed.hostname)
    elif args.output == "dirpath":
        print(parsed.scheme + "://" + parsed.hostname + dirname(parsed.path))
    elif args.output == "path":
        print(parsed.scheme + "://" + parsed.hostname + parsed.path)
    else:
        print(url)


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--scope", help="Commma separated list of in-scope domains", required=True, type=str)
parser.add_argument("-o", "--output", help="Output format: domain, schemedomain, dirpath, path, full. Default: full", default="full", type=str)
args = parser.parse_args()

if "://" in args.scope:
    args.scope = "".join(args.scope.split("://")[1:])

for line in sys.stdin:
    line = line.strip()
    if is_http(line) and in_scope(line, args.scope):
        print_success(line)
