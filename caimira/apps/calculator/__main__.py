import argparse
import logging
from pathlib import Path

from tornado.ioloop import IOLoop

from . import make_app


def configure_parser(parser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--no-debug", help="Don't enable debug mode",
        action="store_false",
    )
    parser.add_argument(
        "--theme",
        help="A directory containing extensions for templates and static data",
        default=None,
    )
    parser.add_argument(
        "--app_root",
        help="Change the APPLICATION_ROOT of the app",
        default="/"
    )
    parser.add_argument(
        "--prefix",
        help="Change the URL path prefix to the calculator app",
        default="/calculator"
    )
    parser.add_argument(
        "--port",
        help="The port to listen on",
        default="8080"
    )
    return parser


def _init_logging(debug=False):
    # Set the logging level for urllib3 and requests to WARNING
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # set app root log level
    logger = logging.getLogger()
    root_log_level = logging.DEBUG if debug else logging.WARNING
    logger.setLevel(root_log_level)


def main():
    parser = configure_parser(argparse.ArgumentParser())
    args = parser.parse_args()

    debug = args.no_debug
    _init_logging(debug)

    theme_dir = args.theme
    if theme_dir is not None:
        theme_dir = Path(theme_dir).absolute()
        assert theme_dir.exists()

    app = make_app(debug=debug, APPLICATION_ROOT=args.app_root, calculator_prefix=args.prefix, theme_dir=theme_dir)
    app.listen(args.port)
    IOLoop.current().start()


if __name__ == '__main__':
    main()
