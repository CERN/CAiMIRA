# CAiMIRA - CERN Airborne Model for Risk Assessment

CAiMIRA is a risk assessment tool developed to model the concentration of viruses in enclosed spaces, in order to inform space-management decisions.

CAiMIRA models the concentration profile of potential virions in enclosed spaces , both as background (room) concentration and during close-proximity interactions, with clear and intuitive graphs.
The user can set a number of parameters, including room volume, exposure time, activity type, mask-wearing and ventilation.
The report generated indicates how to avoid exceeding critical concentrations and chains of airborne transmission in spaces such as individual offices, meeting rooms and labs.

The risk assessment tool simulates the airborne spread SARS-CoV-2 virus in a finite volume, assuming a homogenous mixture and a two-stage exhaled jet model, and estimates the risk of COVID-19 infection therein.
The results DO NOT include the other known modes of SARS-CoV-2 transmission, such as fomite or blood-bound.
Hence, the output from this model is only valid when the other recommended public health & safety instructions are observed, such as good hand hygiene and other barrier measures.

The model used is based on scientific publications relating to airborne transmission of infectious diseases, dose-response exposures and aerosol science, as of February 2022.
It can be used to compare the effectiveness of different airborne-related risk mitigation measures.
Note that this model applies a deterministic approach, i.e., it is assumed at least one person is infected and shedding viruses into the simulated volume.
Nonetheless, it is also important to understand that the absolute risk of infection is uncertain, as it will depend on the probability that someone infected attends the event.
The model is most useful for comparing the impact and effectiveness of different mitigation measures such as ventilation, filtration, exposure time, physical activity, amount and nature of close-range interactions and
the size of the room, considering both long- and short-range airborne transmission modes of COVID-19 in indoor settings.

This tool is designed to be informative, allowing the user to adapt different settings and model the relative impact on the estimated infection probabilities.
The objective is to facilitate targeted decision-making and investment through comparisons, rather than a singular determination of absolute risk.
While the SARS-CoV-2 virus is in circulation among the population, the notion of 'zero risk' or 'completely safe scenario' does not exist.
Each event modelled is unique, and the results generated therein are only as accurate as the inputs and assumptions.

## Calculator

The CAiMIRA Calculator can be accessed online [here](https://caimira.web.cern.ch/), provided you have CERN SSO (Single Sign-On) credentials. For local usage, please refer to the [documentation](#documentation) on how to install and run the calculator locally.

## Documentation

All instructions for installation, deployment, usage, and model assumptions and references can be found in the [official documentation](https://caimira.docs.cern.ch/).

## Contributing

Contributions are welcome on our [GitHub repository](https://github.com/CERN/CAiMIRA).

## Authors & License

Developed by CERN's HSE, Beams, and IT departments, in collaboration with WHO.

© Copyright 2020 CERN. All rights not expressly granted are reserved.<br>
Licensed under the Apache License, Version 2.0

See the full [license](caimira/LICENSE) for details.
