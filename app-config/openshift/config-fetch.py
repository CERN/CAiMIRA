import argparse
import pathlib
import subprocess
import sys
import typing


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = "Fetch the openshift config for CARA"
    parser.set_defaults(handler=handler)
    parser.add_argument(
        "instance", choices=['cara', 'test-cara'],
        help="Pick the instance for which you want to fetch the config",
    )
    parser.add_argument(
        "-o", "--output-directory", default='config',
        help="Location to put the config files",
    )


def get_oc_server() -> typing.Optional[str]:
    # Return the openshift server that is currently logged in, or None if not logged in
    # (or other issues getting the information from the oc client).
    try:
        subprocess.check_output(['oc', 'whoami'], stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        # User not logged on, or oc command missing.
        return None

    return subprocess.run([
        'oc', 'whoami', '--show-server'
    ], check=True, stdout=subprocess.PIPE).stdout.decode().strip()


def fetch_config(output_directory: pathlib.Path, okd_version: int):
    output_directory.mkdir(exist_ok=True, parents=True)

    for component, name in [
            ('routes', None),
            ('configmap', 'auth-service'),
            ('services', None),
            ('imagestreams', None),
            ('buildconfig', None),
            ('deploymentconfig', None)]:

        with (output_directory / f'{component}.yaml').open('wt') as fh:
            cmdOKD4 = ['oc', 'get', '-o', 'yaml', component]
            cmdOKD3 = ['oc', 'get', '--export', '-o', 'yaml', component]
            cmd = cmdOKD4 if okd_version == 4 else cmdOKD3
            if name:
                cmd += [name]
            print(f'Running: {" ".join(cmd)}')
            subprocess.run(cmd, stdout=fh, check=True)
    print(f'Config in: {output_directory.absolute()}')


def handler(args: argparse.ArgumentParser) -> None:
    if args.instance == 'cara':
        login_server = 'https://openshift.cern.ch:443'
        project_name = 'cara'
        okd_version = 3
    elif args.instance == 'test-cara':
        login_server = 'https://api.paas.okd.cern.ch:443'
        project_name = 'test-cara'
        okd_version = 4

    actual_login_server = get_oc_server()
    if actual_login_server != login_server:
        print(f'\nPlease login to the correct OpenShift server with: \n\n oc login {login_server}\n', file=sys.stderr)
        sys.exit(1)

    subprocess.run(['oc', 'project', project_name], stdout=subprocess.DEVNULL, check=True)

    fetch_config(pathlib.Path(args.output_directory), okd_version)


def main():
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    args = parser.parse_args()
    args.handler(args)


if __name__ == '__main__':
    main()
