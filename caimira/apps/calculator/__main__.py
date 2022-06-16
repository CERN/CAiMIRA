import argparse
from pathlib import Path

from tornado.ioloop import IOLoop
import tornado.web

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


def main():
    parser = configure_parser(argparse.ArgumentParser())
    args = parser.parse_args()
    theme_dir = args.theme
    if theme_dir is not None:
        theme_dir = Path(theme_dir).absolute()
        assert theme_dir.exists()
    tornado.locale.load_gettext_translations('cara/apps/locale', 'messages')
    app = make_app(debug=args.no_debug, calculator_prefix=args.prefix, theme_dir=theme_dir)
    app.listen(args.port)
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
