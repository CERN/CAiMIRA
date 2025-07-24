# 4.18.0 (July 24, 2025)

## Feature Added
- Dynamic occupancy: groups of exposed + infected may now be defined.
Model and calculator updated, and tests added. Documentation still to
be updated. User interface mostly unchanged (the new feature is not
visible there).

## Bug Fixes
- Fix in profiler to adapt to a non back-compatible change in pyinstrument
package.
- Type ignored in the expert app.

## Other
- Update of mypy, pytest-mypy and pyinstrument dependencies (version).

# 4.17.8 (March 13, 2025)

## Bug Fixes
- Implemented missing preflight CORS request handling.

## Other
- Changed CO₂ transition times API response to split occupancy
  and ventilation times. Adapted documentation.

# 4.17.7 (December 4, 2024)

## Features Added
- Added new route for the suggested ventilation transition times
- Small updates on routes' nomenclatures
- Updated documentation

## Bug Fixes
- Wrong URL in README (related to CAiMIRA reference)

# 4.17.6 (December 4, 2024)

## Features Added
- Data registry update
- REST API adjustments in docs
- Release to PyPI

## Bug Fixes
- Corrected user guide and about doc refs
- Minor fix in docker pre-built instruction

# 4.17.5 (November 21, 2024)

## Features Added
- Mkdocs documentation
- Folder layout adapted

## Bug Fixes
- N/A

# 4.17.4 (November 05, 2024)

## Features Added
- CO2 fitting algorithm post-review changes

## Bug Fixes
- N/A

# 4.17.3 (October 16, 2024)

## Features Added
- UI changes - calculator: Added Eq. ventilation to HEPA question

## Bug Fixes
- N/A

# 4.17.2 (September 19, 2024)

## Features Added
- Initial commit with changelog file.
- New project layout architecture.
- Added CAiMIRA REST API features.

## Bug Fixes
- Virus and CO2 routes and controllers.
