import argparse
import pathlib
import subprocess
import sys
import typing


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = "Generate the config files which can be later submitted to openshift"
    parser.set_defaults(handler=handler)
    parser.add_argument(
        "instance", choices=['cara', 'test-cara'],
        help="Pick the instance for which you want to generate the config",
    )
    parser.add_argument(
        "--output-directory", default='config',
        help="Location to put the config files",
    )


def generate_config(output_directory: pathlib.Path, project_name: str, hostname: str, branch: str):
    output_directory.mkdir(exist_ok=True, parents=True)

    def oc_process(component_name: str, context: typing.Optional[dict] = None):
        cmd = ['oc', 'process', '--local', '-f', f'{component_name}.yaml']
        for ctx_name, ctx_value in (context or {}).items():
            cmd.extend(['--param', f'{ctx_name}={ctx_value}'])
        with (output_directory / f'{component_name}.json').open('wt') as fh:
            print(f'Running: {" ".join(cmd)}')
            subprocess.run(cmd, stdout=fh, check=True)

    # oc_process('route', oc_process + ['route.yaml', '--param', f'HOST={hostname}'])
    oc_process('routes', context={'HOST': hostname})
    oc_process('configmap')
    oc_process('services')
    oc_process('imagestreams')
    oc_process('buildconfig', context={'GIT_BRANCH': branch})
    oc_process('deploymentconfig', context={'PROJECT_NAME': project_name})

    print(f'Config in: {output_directory.absolute()}')


def handler(args: argparse.ArgumentParser) -> None:
    if args.instance == 'cara':
        project_name = 'cara'
        branch = 'master'
        hostname = 'cara.web.cern.ch'
    elif args.instance == 'test-cara':
        branch = 'live/test-cara'
        project_name = 'test-cara'
        hostname = 'test-cara.web.cern.ch'

    generate_config(pathlib.Path(args.output_directory), project_name, hostname, branch)


def main():
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    args = parser.parse_args()
    args.handler(args)


if __name__ == '__main__':
    main()

