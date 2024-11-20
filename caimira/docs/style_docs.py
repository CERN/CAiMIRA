
""" Changes the .md files to contain desired styling """

import re
import os
import subprocess
import matplotlib.pyplot as plt
from collections import Counter

def get_package_info():
    """
    Retrieves package details (name, version, license, and homepage) for each installed package.
    Uses pip show to get detailed information.
    """
    # Get the list of installed packages using pip freeze
    packages = subprocess.check_output(["pip", "freeze"]).decode().splitlines()

    package_details = []
    for package in packages:
        package_name = package.split("==")[0]
        try:
            # Get detailed info about each package
            info = subprocess.check_output(["pip", "show", package_name]).decode().splitlines()
            
            details = {
                "name": package_name,
                "version": "",
                "license": "",
                "homepage": ""
            }
            
            for line in info:
                if line.startswith("Version:"):
                    details["version"] = line.split(":", 1)[1].strip()
                elif line.startswith("License:"):
                    details["license"] = line.split(":", 1)[1].strip()
                elif line.startswith("Home-page:"):
                    details["homepage"] = line.split(":", 1)[1].strip()
            
            # Append the details for the current package
            package_details.append(details)
        except subprocess.CalledProcessError:
            print(f"Error retrieving details for package: {package_name}")

    return package_details


def update_markdown_references(md_file_path):
    """
    Updates the code markdown file by adding headers for class definitions and modifying internal links.
    """
    # Read the original Markdown file
    with open(md_file_path, 'r') as file:
        md_content = file.read()

    # Regular expression to find all class definitions, including those without parameters
    class_pattern = re.compile(r'### \*class\* (\w+)(\(.*\))?')

    # Find all matches for class definitions
    class_matches = class_pattern.findall(md_content)

    # For each found class definition
    for match in class_matches:
        # Class name (e.g., 'Interval' or 'ConcentrationModel')
        class_name = match[0]

        # Create the header for this class
        header = f"## {class_name} Class\n"

        # Check if the header already exists in the file
        if header not in md_content:
            # If the header does not exist, insert it before the class definition
            md_content = md_content.replace(
                f"### *class* {class_name}", header + f"### *class* {class_name}")

        # Replace references like #models.models.ClassName with #className-class
        md_content = md_content.replace(
            f"#models.models.{class_name}", f"#{class_name.lower()}-class")

    # Write the updated content back to the file
    with open(md_file_path, 'w') as file:
        file.write(md_content)
    print(f"Markdown file '{md_file_path}' updated successfully.")


def unify_license(license_str):
    """
    Returns an unified license version.
    """
    license_map = {
        'MIT': 'MIT',
        'MIT License': 'MIT',
        'MIT license': 'MIT',
        'MIT-CMU': 'MIT',
        'http://www.opensource.org/licenses/mit-license.php': 'MIT',
        'BSD': 'BSD-3-Clause',
        'BSD-3-Clause': 'BSD-3-Clause',
        'BSD 3-Clause License': 'BSD-3-Clause',
        'BSD 3-Clause': 'BSD-3-Clause',
        'BSD-2-Clause': 'BSD-2-Clause',
        'BSD License': 'BSD-3-Clause',
        'new BSD License': 'BSD-3-Clause',
        'Modified BSD License': 'BSD-3-Clause',
        'BSD 2-Clause License': 'BSD-2-Clause',
        'Apache 2.0': 'Apache-2.0',
        'Apache Software License': 'Apache-2.0',
        'Apache 2.0 License': 'Apache-2.0',
        'Apache License, Version 2.0': 'Apache-2.0',
        'Apache 2.0 license': 'Apache-2.0',
        'Apache-2.0': 'Apache-2.0',
        'Apache Software License 2.0': 'Apache-2.0',
        'MPL-2.0': 'MPL-2.0',
        'MPL 2.0': 'MPL-2.0',
        'GPL-2.0-or-later': 'GPL-2.0-or-later',
        'LGPL-2.1-or-later': 'LGPL-2.1-or-later',
        'ISC license': 'ISC',
        'Expat license': 'Expat',
        'MIT OR Apache-2.0': 'Dual License',
        'Dual License': 'Dual License',
        'UNKNOWN': 'Unknown'
    }
    
    return license_map.get(license_str, 'Custom')


def add_python_dependencies_section(md_file_path, package_details):
    """
    Adds the Python package dependencies section to the Open Source Acknowledgments Markdown file.
    """
    # Section header for Python dependencies
    dependencies_section = '\n\n'
    for package in package_details:
        package_url = f"https://pypi.org/project/{package['name']}/{package['version']}/"
        package_title = f"    #### [{package['name']} {package['version']}]({package_url})"
        if package["license"]:
            license_text = f"    - License: {unify_license(package['license'])}"
        else:
            license_text = "    - License: Unknown"
        
        dependencies_section += f"{package_title}\n\n{license_text}\n\n"

    # Read the current content of the Markdown file
    with open(md_file_path, 'r') as file:
        md_content = file.read()

    # Regex to find the "Back-end (Python) Dependencies" section
    section_pattern = re.compile(
        r'(?<=\?\?\? "Back-end \(Python\) Dependencies")(.*?)(?=\n\?\?\?|\Z)', re.DOTALL)

    match = section_pattern.search(md_content)
    if match:
        updated_content = md_content[:match.start(1)] + dependencies_section + md_content[match.end(1):]
    else:
        raise ValueError("Error: '??? \"Back-end (Python) Dependencies\"' section not found in the file.")

    with open(md_file_path, 'w') as file:
        file.write(updated_content)

    print(f"Markdown file '{md_file_path}' updated with Python dependencies section.")


def generate_license_distribution_pie_chart(package_details, output_image_path):
    """
    Generates a pie chart showing the distribution of licenses from the package details.
    The chart is saved to the specified output image path.
    """
    try:
        licenses = [unify_license(pkg["license"]) for pkg in package_details if pkg["license"]]
        license_counts = Counter(licenses)

        # Create labels and sizes for the pie chart
        labels = list(license_counts.keys())
        sizes = list(license_counts.values())

        # Create the pie chart
        plt.figure(figsize=(8, 8), dpi=300)
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')

        # Save and show the pie chart
        plt.savefig(output_image_path, dpi=300)
        plt.close()

        print(f"License distribution pie chart saved to {output_image_path}")

    except Exception as e:
        print(f"Error generating license distribution chart: {e}")




def main():
    # Path to the index.md markdown file to be updated
    index_file_path = 'sphinx/_build/markdown/index.md'

    if os.path.isfile(index_file_path):
        update_markdown_references(index_file_path)
    else:
        print(f"File '{index_file_path}' does not exist, skipping update.")

    # Path to the open source acknowledgements markdown file to be updated
    acknowledgements_file_path = 'mkdocs/docs/root/open_source_acknowledgments.md'
    
    if os.path.isfile(acknowledgements_file_path):
        # Retrieve package details
        package_details = get_package_info()

        # Write the dependencies in the file
        add_python_dependencies_section(acknowledgements_file_path, package_details)

        # Generate the pie chart
        output_image_path = 'mkdocs/docs/root/license_distribution.png'
        generate_license_distribution_pie_chart(package_details, output_image_path)
    else:
        print(f"File '{acknowledgements_file_path}' does not exist, skipping update.")


if __name__ == "__main__":
    main()
