import os
import sys
from argparse import ArgumentParser, ArgumentTypeError

from .pipeline import Config, Pipeline


def existing_path(value):
    value = str(value)
    if not os.path.exists(value):
        raise ArgumentTypeError('should be an existing file')
    return value

def create_parser(prog_name):
    parser = ArgumentParser(prog=prog_name, description='Run team4 pipeline')
    parser.add_argument('--config', '-c', metavar='CONFIG_PATH', default=None,
                        help='Configuration file')
    parser.add_argument('--experiment', '-e', metavar='EXPERIMENT_PATH', default=None,
                        help='Relative path for intermediate and final results of this experiment')
    return parser

def main(args=None):
    if args is None:
        args = sys.argv
    parser = create_parser(args[0])
    opts = parser.parse_args(args[1:])
    config = Config.load(opts.config)
    pipeline = Pipeline(config, opts.experiment)
    pipeline.setup()
    rc = pipeline.run()
    if rc:
        raise SystemExit(int(rc))

if __name__ == '__main__':
    main()
