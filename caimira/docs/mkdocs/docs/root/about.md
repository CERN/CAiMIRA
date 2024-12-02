Currently, the existing public health measures point to the importance of proper building and environmental engineering control measures, such as proper Indoor Air Quality (IAQ). This pandemic clearly raised increased awareness on airborne transmission of respiratory viruses in indoor settings. Out of the main modes of viral transmission, the airborne route of SARS-CoV-2 seems to have a significant importance to the spread of COVID-19 infections world-wide, hence proper guidance to building engineers or facility managers, on how to prevent on-site transmission, is essential.

For information on the Airborne Transmission of SARS-CoV-2, feel free to check out the special issue on the Interface Focus journal from Royal Society publishing: [Interface Focus: Volume 12, Issue 2](https://royalsocietypublishing.org/toc/rsfs/2022/12/2) and an CERN HSE Seminar: [https://cds.cern.ch/record/2743403](https://cds.cern.ch/record/2743403).

## What is CAiMIRA?

CAiMIRA stands for CERN Airborne Model for Indoor Risk Assessment, a tool developed to assess and model the concentration of airborne viruses in enclosed spaces, specifically focusing on the SARS-CoV-2 virus. Originally named CARA (COVID Airborne Risk Assessment), CAiMIRA was first developed in early 2020 to quantify the risk of long-range airborne spread of SARS-CoV-2 in workplaces. Over time, the model has expanded to include short-range transmission, allowing for comprehensive simulations of both background (room) concentration and close-proximity interactions.

CAiMIRA features applications with varying flexibility in setting input parameters:

- CAiMIRA Calculator App
- CAiMIRA Expert App (deprecated)

These applications produce clear and intuitive graphs, enabling users to adjust settings such as room volume, exposure time, activity type, mask-wearing, and ventilation levels. The tool generates reports indicating how users can avoid exceeding critical concentrations and reduce airborne transmission chains in spaces like individual offices, meeting rooms, and laboratories.

The mathematical and physical model simulates the airborne spread of SARS-CoV-2 in a finite volume, using a homogenous mixture assumption and a two-stage exhaled jet model to estimate the risk of COVID-19 airborne transmission. Results do not account for other SARS-CoV-2 transmission modes, such as fomite or blood-bound transmission, meaning the output is only valid when paired with public health measures like good hand hygiene and barrier practices.

The model is based on scientific publications on infectious disease transmission, virology, epidemiology, and aerosol science, as of February 2022. Its methodology, mathematical equations, and parameters are detailed in a peer-reviewed publication, Modelling airborne transmission of SARS-CoV-2 using CARA: risk assessment for enclosed spaces. The short-range model component draws from Jia et al. (2022), Exposure and respiratory infection risk via the short-range airborne route. This foundation enables CAiMIRA to compare the effectiveness of different airborne risk mitigation measures.

CAiMIRA’s methodology is divided into key steps:

- Estimating the emission rate of virions
- Estimating the removal rate of virions
- Modeling the concentration of virions within a specified volume over time
- Calculating the dose of inhaled infectious viruses during exposure
- Estimating the probability of COVID-19 infection and the potential number of new cases arising from an event

The model assumes a deterministic approach—at least one individual is infected and shedding virus into the simulated environment. While it calculates the infection probability for specific scenarios, the model's primary utility is in comparing the relative impact of different preventive measures, such as ventilation, filtration, exposure time, physical activity, and close-range interactions.

Although CAiMIRA allows users to calculate the infection probability for a specific event given pre-set protection measures, its primary function is to facilitate comparisons between different mitigation, helping users decide on measures to reduce airborne infection risks. Examples include:

- Comparing slight versus full window openings
- Evaluating intermittent versus continuous ventilation
- Assessing the impact of using FFP2 masks over Type I surgical masks or Cloth masks
- Determining maximum occupancy based on HEPA filter use

This approach supports informed decision-making and optimized investment by showing the relative effectiveness of each measure. Importantly, while CAiMIRA can guide users in reducing risk, it does not provide an absolute “zero risk” or “completely safe scenario”. 

Risk is unique to each event and setting, influenced by variables such as probability of exposure and input assumptions.

## Collaboration with the World Health Organization (WHO)

The tool has attracted the attention of many international organisations, including the World Health Organization (WHO) and the United Nations Office at Geneva (UNOG). In June 2021, CERN shared its own approach towards risk assessments for occupational hazards, which was at the time called CARA, to WHO's COVID Expert Panel.

As a result, WHO has invited CERN to become a member of a multidisciplinary expert group of international experts called ARIA, which will work to define a standardised algorithm to quantify airborne transmission risk in indoor settings. This will ensure that the model inculdes not only the science related to aerosol science but also the virological effects, such as host-pathogen interaction.

The collaboration takes place within CERNs wide-ranging engagement with other international organisations, promoting shared solutions to societal challenges.

## Authors

Andre Henriques<sup>1,2</sup>, Wei Jia<sup>3</sup>, Luis Aleixo<sup>1</sup>, Nicolas Mounet<sup>1</sup>, Luca Fontana<sup>4,5</sup>, Alice Simniceanu<sup>2,6</sup>, James Devine<sup>1</sup>, Philip Elson<sup>1</sup>, Gabriella Azzopardi<sup>1</sup>, Markus Kongstein Rognlien<sup>1,7</sup>, Marco Andreini<sup>1</sup>, Nicola Tarocco<sup>1</sup>, Olivia Keiser<sup>2</sup>, Yugou Li<sup>3</sup>, Julian Tang<sup>8</sup>

<sup>1</sup>CERN (European Organization for Nuclear Research), Geneva, Switzerland<br>
<sup>2</sup>Institute of Global Health, University of Geneva, Geneva, Switzerland<br>
<sup>3</sup>Department of Mechanical Engineering, University of Hong Kong, Hong Kong SAR, China<br>
<sup>4</sup>Strategic Health Operations, Operations Support and Logistic, Health Emergencies Programme, World Health Organization, Geneva, Switzerland<br>
<sup>5</sup>Department of Civil and Mechanical Engineering, Università degli studi di Cassino e del Lazio Meridionale (UNICAS), Cassino, Italy<br>
<sup>6</sup>Epidemic and Pandemic Preparedness, Health Emergencies Programme, World Health Organization, Geneva, Switzerland<br>
<sup>7</sup>Norwegian University of Science and Technology (NTNU), Torgarden, Norway<br>
<sup>8</sup>Respiratory Sciences, University of Leicester, Leicester, UK<br>

#### Other contributors

Anna Efimova<sup>1,2</sup>, Anel Massalimova<sup>1,3</sup>, Cole Austin Coughlin<sup>1,4</sup>, Germain Personne<sup>5</sup>, Matteo Manzinello<sup>6</sup>, Elias Sandner<sup>1</sup>

<sup>1</sup>CERN<br>
<sup>2</sup>M.V. Lomonosov Moscow State University<br>
<sup>3</sup>National Research Nuclear University "MEPhI"<br>
<sup>4</sup>University of Manitoba<br>
<sup>5</sup>Université Clermont Auvergne<br>
<sup>6</sup>World Health Organization (WHO)<br>

## Reference and Citation

**For the use of the CAiMIRA web app**

CAiMIRA – CERN Airborne Model for Indoor Risk Assessment tool

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6520431.svg)](https://doi.org/10.5281/zenodo.6520431)

© Copyright 2020 CERN. All rights not expressly granted are reserved.

**For use of the CAiMIRA model**

Henriques A, Mounet N, Aleixo L, Elson P, Devine J, Azzopardi G, Andreini M, Rognlien M, Tarocco N, Tang J. (2022). Modelling airborne transmission of SARS-CoV-2 using CARA: risk assessment for enclosed spaces. _Interface Focus 20210076_. [https://doi.org/10.1098/rsfs.2021.0076](https://doi.org/10.1098/rsfs.2021.0076)

Reference on the Short-range expiratory jet model from:
Jia W, Wei J, Cheng P, Wang Q, Li Y. (2022). Exposure and respiratory infection risk via the short-range airborne route. _Building and Environment_ *219*: 109166.
[https://doi.org/10.1016/j.buildenv.2022.109166](https://doi.org/10.1016/j.buildenv.2022.109166)

***Open Source Acknowledgments***

For a detailed list of the open-source dependencies used in this project along with their respective licenses, please refer to [Open Source Acknowledgments](open_source_acknowledgments.md). This includes both the core dependencies specified in the project's requirements and their transitive dependencies.

The information also features a distribution diagram of licenses and a brief description of each of them.

## Acknowledgements

We wish to thank CERN at the different Departments working on the project: Occupational Health & Safety and Environmental Protection Unit, Information Technology Department, Beams Department, Experimental Physics Department, Industry, Procurement and Knowledge Transfer Department and International Relations Sector for their support to the study. We also wish to thank our collaborators at the World Health Organization (WHO) for thier endless support to this project, in particular to the members of the ARIA Expert Group.

## Disclaimer

CAiMIRA has not undergone review, approval or certification by competent authorities, and as a result, it cannot be considered as a fully endorsed and reliable tool, namely in the assessment of potential viral emissions from infected hosts to be modelled.

The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and non-infringement.
In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.