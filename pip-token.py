"""
Designed to run both from Python2 and Python3.
"""

from tempfile import NamedTemporaryFile
from subprocess import check_call
import argparse
import logging
import re
import os

LOG_FMT = "%(asctime)s {prog}(%(process)s):%(levelname)s:%(funcName)s() %(message)s"


class UsageError(Exception):
    """Something went wrong"""


def get_token(token_name):
    token = os.environ.get(token_name)
    if not token:
        raise UsageError(
            "no ENV variable {} is present in environment".format(token_name))


def pip_token(req_path, file_prefix, pip_path, pip_args, log, token, delete=False):
    processed = []
    with open(req_path, 'rt') as fd:
        for linenum, rawline in enumerate(fd.readlines(), 1):
            rawline = rawline.strip('\n')
            if rawline.find('github') < 0:
                processed.append(rawline)
                continue

            r = re.match(
                "(?P<proto>.+?)://(?P<host>.+?)/(?P<rest>.+)", rawline)
            if r is None:
                raise Exception("cannot parse line %s in \"%s\": \"%s\"" % (
                    linenum, req_path, rawline))
            d = r.groupdict()
            newurl = "git+https://{token}@github.com/{rest}".format(
                token=token, rest=d['rest'])
            processed.append(newurl)

    with NamedTemporaryFile(prefix=file_prefix, suffix='.txt', mode='w+t', delete=delete) as fd:
        log.debug("writing to \"%s\"", fd.name)
        for line in processed:
            fd.write(line + '\n')
        fd.flush()

        pip_cmd = [pip_path] + pip_args + ['-r', fd.name]
        log.debug("calling %s", pip_cmd)
        check_call(pip_cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--requirement')
    parser.add_argument('--token-name', default='GITHUB_DEPLOY_TOKEN')
    parser.add_argument('--pip-path', default='pip')
    args, pip_args = parser.parse_known_args()

    logging.basicConfig(
        level=logging.DEBUG, format=LOG_FMT.format(prog=parser.prog))
    log = logging.getLogger(parser.prog)
    log.debug("argumens: %s %s", args, pip_args)

    try:
        token = get_token(args.token_name)
        pip_token(req_path=args.requirement,
                  pip_path=args.pip_path,
                  pip_args=pip_args,
                  log=log,
                  file_prefix="%s_" % parser.prog,
                  token=token)
    except UsageError as e:
        raise SystemExit("Error: %s" % e)


if __name__ == '__main__':
    main()
