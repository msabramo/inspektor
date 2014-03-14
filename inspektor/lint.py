import logging
import os
import sys

from pylint.lint import Run

from inspector import PathInspector

log = logging.getLogger("inspektor.lint")


class Linter(object):

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.ignored_errors = 'E1002,E1101,E1103,E1120,F0401,I0011'
        # Be able to analyze all imports inside the project
        sys.path.insert(0, os.getcwd())
        self.failed_paths = []

    def set_verbose(self):
        self.verbose = True

    def get_opts(self):
        """
        If VERBOSE is set, show all complaints. If not, only errors.
        """
        if not self.verbose:
            return ['--disable=W,R,C,%s' % self.ignored_errors,
                    '--reports=no', '--rcfile=/dev/null',
                    '--good-names=i,j,k,Run,_,vm',
                    '--msg-template="{msg_id}:{line:3d},{column}: {obj}: {msg}"']
        else:
            return []

    def check_dir(self, path):
        """
        Recursively go on a directory checking files with pylint.

        :param path: Path to a directory.
        """
        def visit(arg, dirname, filenames):
            for filename in filenames:
                self.check_file(os.path.join(dirname, filename))

        os.path.walk(path, visit, None)
        return not self.failed_paths

    def check_file(self, path):
        """
        Check one regular file with pylint for py syntax errors.

        :param path: Path to a regular file.
        :return: False, if pylint found syntax problems, True, if pylint didn't
                 find problems, or path is not a python module or script.
        """
        inspector = PathInspector(path)
        if not inspector.is_python():
            return True
        runner = Run(self.get_opts() + [path], exit=False)
        if runner.linter.msg_status != 0:
            log.error('Pylint check fail: %s', path)
            self.failed_paths.append(path)
        return runner.linter.msg_status == 0

    def check(self, path):
        if os.path.isfile(path):
            return self.check_file(path)
        elif os.path.isdir(path):
            return self.check_dir(path)


def set_arguments(parser):
    plint = parser.add_parser('lint', help='check code with pylint')
    plint.add_argument('path', type=str,
                       help='Path to check (empty for full tree check)',
                       nargs='?',
                       default="")
    plint.set_defaults(func=run_lint)


def run_lint(args):
    path = args.path
    if not path:
        path = os.getcwd()

    linter = Linter(verbose=args.verbose)

    if linter.check(path):
        log.info("Syntax check PASS")
        sys.exit(0)
    else:
        log.error("Syntax check FAIL")
        sys.exit(1)
