import argparse

from tornado.ioloop import IOLoop

from . import make_app


def configure_parser(parser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--no-debug", help="Don't enable debug mode",
        action="store_false",
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
    app = make_app(debug=args.no_debug)
    app.listen(args.port)
    IOLoop.instance().start()


if __name__ == "__main__":
    main()
