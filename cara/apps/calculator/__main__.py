import argparse

from tornado.ioloop import IOLoop

from . import make_app


def configure_parser(parser):
    parser.add_argument(
        "--no-debug", help="Don't enable debug mode",
        action="store_false",
    )
    return parser


def main():
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    args = parser.parse_args()
    app = make_app(debug=args.no_debug)
    app.listen(8080)
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
