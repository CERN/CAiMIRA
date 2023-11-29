import re
from collections import Counter
import matplotlib.pyplot as plt

# Open the acknowledgments file for reading
with open('acknowledgments.md', 'r') as file:
    lines = file.readlines()

# Regular expression to match package names and licenses
package_pattern = r'^#### (.+)$'
license_pattern = r'- License: \[([^\]]+)\]'

# Lists to store licenses
bsd_licenses = []
other_licenses = []

# Iterate through the lines and extract licenses
for line in lines:
    license_match = re.search(license_pattern, line)
    if license_match:
        license = license_match.group(1)
        if license.startswith('BSD'):
            bsd_licenses.append(license)
        else:
            other_licenses.append(license)

# Count the occurrences of each license
bsd_license_counts = Counter(bsd_licenses)
other_license_counts = Counter(other_licenses)

# Print the BSD license counts
for license, count in bsd_license_counts.items():
    print(f'BSD License: {license}, Count: {count}')

# Print the counts of other licenses
for license, count in other_license_counts.items():
    print(f'Other License: {license}, Count: {count}')

# Combine BSD licenses into one category
bsd_combined_count = sum(bsd_license_counts.values())

# Create labels and sizes for the pie chart
labels = ['BSD Licenses', *other_license_counts.keys()]
sizes = [bsd_combined_count, *other_license_counts.values()]

# Create the pie chart
plt.figure(figsize=(8, 8), dpi=300)
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
plt.axis('equal')
plt.savefig('licence_distribution.png', dpi=300)
plt.show()
