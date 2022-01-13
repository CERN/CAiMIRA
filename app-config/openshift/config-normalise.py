import argparse
import pathlib

import ruamel.yaml


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = "Normalise openshift config files (by sorting and removing ephemeral values)"
    parser.set_defaults(handler=handler)
    parser.add_argument(
        "config-directory",
        help="The directory from which to find yaml files",
    )
    parser.add_argument(
        "output-directory",
        help="The directory to put normalized files (can be the same as config-directory)",
    )


def clean_ephemeral_config(config: dict):
    config = config.copy()
    config.get('metadata', []).clear()

    METADATA_TO_PRESERVE = ['labels', 'name']
    CERN_OKD4_METADATA_LABELS = ['migration.openshift.io', 'velero.io']

    for item in config.get('items', {}):
        item.pop('status', None)

        for key in list(item['metadata'].keys()):
            if key not in METADATA_TO_PRESERVE:
                del item['metadata'][key]

        item.get('spec', {}).pop('clusterIP', None)
        item.get('spec', {}).pop('clusterIPs', None)
        item.get('spec', {}).pop('revisionHistoryLimit', None)

        if item['kind'] == 'BuildConfig':
            for trigger in item.get('spec', {}).get('triggers', []):
                trigger.get('imageChange', {}).pop('lastTriggeredImageID', None)
            item.get('spec', {}).pop('failedBuildsHistoryLimit', None)
            item.get('spec', {}).pop('successfulBuildsHistoryLimit', None)

        if item['kind'] == 'DeploymentConfig':
            item['spec'].get('template', {}).get('metadata', {}).pop('creationTimestamp', None)

            for container in item['spec'].get('template', {}).get('spec', {}).get('containers', []):
                # Drop the specific image name (and hash).
                container.pop('image', None)
            item['spec'].get('template', {}).get('metadata', {}).pop('creationTimestamp', None)
            for trigger in item['spec'].get('triggers', []):
                trigger.get('imageChangeParams', {}).pop('lastTriggeredImage', None)

        if item['kind'] == 'Service':
            item['spec'].pop('ipFamilies', None)
            item['spec'].pop('ipFamilyPolicy', None)
            

        for label in list(item['metadata'].get('labels', {}).keys()):
            for prefix in CERN_OKD4_METADATA_LABELS:
                if label.startswith(prefix):
                    item['metadata']['labels'].pop(label)

        # Drop the template part of the config for now.
        # TODO: Remove this constraint to ensure our deployments reflect the fact that they are templated.
        r = item['metadata'].get('labels', {}).pop('template', None)

        if r is not None and not item['metadata']['labels']:
            # Remove the empty labels dict if there is nothing left after popping the template item.
            item['metadata'].pop('labels')

    return config


def deep_sort(item):
    if isinstance(item, dict):
        # Sort by the key.
        return {k: deep_sort(v) for k, v in sorted(item.items(), key=lambda i: i[0])}
    elif isinstance(item, list):
        # Use the metadata/name and fallback to the str representation to give a sort order.
        def sort_key(value):
            if isinstance(value, dict):
                return value.get('metadata', {}).get('name', '') or str(value)
            else:
                return str(value)

        return sorted(
            [deep_sort(v) for v in item],
            key=sort_key,
        )
    else:
        return item


def normalise_config(input_directory: pathlib.Path, output_directory: pathlib.Path):
    output_directory.mkdir(exist_ok=True, parents=True)

    files = sorted(input_directory.glob('*.yaml'))

    yaml = ruamel.yaml.YAML(typ='safe')

    for file in files:
        with file.open('rt') as fh:
            content = yaml.load(fh)

        config = clean_ephemeral_config(content)
        config = deep_sort(config)

        destination = output_directory / file.name
        with destination.open('wt') as fh:
            yaml.dump(config, fh)
        print(f'Normalised {file.name} in {destination}')
    print(f'Config in: {output_directory.absolute()}')


def handler(args: argparse.ArgumentParser) -> None:

    normalise_config(
        pathlib.Path(getattr(args, 'config-directory')),
        pathlib.Path(getattr(args, 'output-directory')),
    )


def main():
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    args = parser.parse_args()
    args.handler(args)


if __name__ == '__main__':
    main()
