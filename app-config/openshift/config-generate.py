import argparse
import pathlib
import subprocess
import typing


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = "Generate the config files which can be later submitted to openshift"
    parser.set_defaults(handler=handler)
    parser.add_argument(
        "instance", choices=['caimira-prod', 'caimira-test'],
        help="Pick the instance for which you want to generate the config",
    )
    parser.add_argument(
        "-o", "--output-directory", default='config',
        help="Location to put the config files",
    )


def generate_config(output_directory: pathlib.Path):
    output_directory.mkdir(exist_ok=True, parents=True)

    def oc_process(component_name: str, context: typing.Optional[dict] = None):
        cmd = ['oc', 'process', '--local', '-f', f'{component_name}.yaml', '-o', 'yaml']
        for ctx_name, ctx_value in (context or {}).items():
            cmd.extend(['--param', f'{ctx_name}={ctx_value}'])
        with (output_directory / f'{component_name}.yaml').open('wt') as fh:
            print(f'Running: {" ".join(cmd)}')
            subprocess.run(cmd, stdout=fh, check=True)

    oc_process('configmap')
    oc_process('services')
    oc_process('deployments')

    print(f'Config in: {output_directory.absolute()}')


def handler(args: argparse.ArgumentParser) -> None:
    if args.instance == 'caimira-prod':
        pass
    elif args.instance == 'caimira-test':
        pass

    generate_config(pathlib.Path(args.output_directory))


def main():
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    args = parser.parse_args()
    args.handler(args)


if __name__ == '__main__':
    main()

