## Backend Structure

The `caimira.calculator.validators` package contains modules responsible for binding all input values from the request to their respective model variables. These modules, `co2.co2_validator` and `virus.virus_validator`, inherit from the parent `form_validator` module, and handle input validation for the CO<sub>2</sub> and virus model generators, respectively.
The `caimira.calculator.report` package contains modules responsible for binding all results from the model calculations into the respective output variables in the request output. These modules, `co2_report_data` and `virus_report_data`, handle outputs for the CO<sub>2</sub> and virus model, respectively.
The `caimira.calculator.store.data_registry` contains input values to CAiMIRA that are not user-defined. These are collected in a class **DataRegistry**.
The `caimira.calculator.models.models.py` and `caimira.calculator.models.monte_carlo` implements the core CAiMIRA methods. A useful feature of the implementation is that we can benefit from vectorization, which allows running multiple parameterizations of the model at the same time.


## CAiMIRA High-level Diagram

The following diagram contains a high-level diagram of the data classes and their relations under the `models.py` file<sup>1</sup>.

[![CAiMIRA High-level diagram](CAiMIRA_05_2025.png)](CAiMIRA_05_2025.png)

<sup>1</sup>Please note that the diagram was built based on a CAiMIRA version that might not be the latest one.

## CAiMIRA UML Diagram

The following diagram describes all the data classes and their relations under the `models.py` file.

[![CAiMIRA UML diagram](classes_UML-CAiMIRA.png)](classes_UML-CAiMIRA.png)

CAiMIRA `models.py` file UML diagram.