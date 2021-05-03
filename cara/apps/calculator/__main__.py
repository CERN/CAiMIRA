import argparse
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
    return parser


def main():
    parser = configure_parser(argparse.ArgumentParser())
    args = parser.parse_args()
    theme_dir = args.theme
    if theme_dir is not None:
        theme_dir = Path(theme_dir).absolute()
        assert theme_dir.exists()
        assert (theme_dir / 'templates').exists()
    app = make_app(debug=args.no_debug, theme_dir=theme_dir)
    app.listen(8080)
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
