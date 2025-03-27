# Dynamic Occupancy Groups

The dynamic occupancy introduces the capability to handle multiple occupancy groups, composed of **infected** and/or **exposed** population within an event. Instead of having one single set of parameters for all the exposed (susceptible) occupants, this feature enables the model to have *n* groups, each with a specific occupancy profile and set of short-range interactions. This can also be used to define dynamic occupancy groups for the [CO<sub>2</sub> fitting algorithm](fitting_algorithm.md).

!!!note
    When in development mode, this feature enables the model to have *n* groups, each with their specific characteristics, e.g. masks, physical activity or host immunities. For more details see [here](#model-generator-development-mode).

This page covers the [description](#feature-description), [input structure](#input-structure), and [results structure](#output-structure) of this feature.

## Feature Description

The feature revolves around the concept of a new `ExposureModelGroup` class, which encapsulates a set of `ExposureModel` instances. Each `ExposureModel` represents a distinct group of exposed occupants.

### Input Structure

The modelling of dynamic occupancy with the definition of groups is controlled by the `occupancy` input, initially defined by an empty dictionary:

```
occupancy = "{}"
```

In case the `occupancy` is not given as input in the request, or if its value is set to the default (empty dictionary), the algorithm will execute as in the *legacy* version of CAiMIRA (i.e. without dynamic groups).

#### Parameters

The `occupancy` object defines the presence of occupancy groups, both composed of infected and/or exposed population over time. Each group should be identified by an unique key (`group_1`, `group_2`, etc.), mapping to an object that specifies:

- `total_people`: The total number of individuals in the group (infected and/or exposed).
- `infected`: The total number of infected individuals in the group.
- `presence`: A list of time intervals (`start_time` and `finish_time`) during which the group was present, formatted as `HH:MM`.

!!!note
    The `infected` entry is expected to be an integer that must be **less** or **equal** than the `total_people` input, with its minimum value as `0` (in the case the group is only composed of exposed people).

???+ example

        occupancy = {
            "group_1": {
                "total_people": 5,
                "infected": 2,
                "presence": [
                    {"start_time": "09:00", "finish_time": "12:00"},
                    {"start_time": "13:00", "finish_time": "17:00"}
                ]
            },
            "group_2": {
                "total_people": 10,
                "infected": 5,
                "presence": [
                    {"start_time": "10:00", "finish_time": "11:00"}
                ]
            }
        }

    - `group_1` consists of **5 individuals (3 exposed, 2 infected)**, present in two time intervals:
        - `09:00` to `12:00`.
        - `13:00` to `17:00`.
    - `group_2` consists of **10 individuals (5 exposed, 5 infected)**, present from:
        - `10:00` to `11:00`.

!!!info
    The number of groups in the `occupancy` input will result in the creation of multiple `ExposureModel` objects. 
    
    The combination of the `presence` and `infected` of all groups will lead to the creation of a single `InfectedPopulation` object, that is replicated across all `ExposureModel`. 
    
    This means that the `infected` population contributes uniformly to the concentration in each exposure model.

#### Short-range interactions

The `short_range_interactions` object defines the number of short-range interactions per occupancy group. Each set of interactions is identified by its corresponding group key (`group_1`, `group_2`, etc.), mapping to an object that specifies:

- `expiration`: expiration type of that short-range interaction (`Breathing`, `Speaking`, or `Shouting`).
- `start_time`: when the interaction starts, formatted as `HH:MM`.
- `duration`: duration of the interaction (in minutes). 

???+ example

        short_range_interactions = {
            "group_1": [
                {"expiration": "Shouting", "start_time": "10:00", "duration": 30},
                {"expiration": "Speaking", "start_time": "11:15", "duration": 15}
            ],
            "group_2": [
                {"expiration": "Shouting", "start_time": "10:15", "duration": 30}
            ]
        }

    - `group_1` has **2 interactions** in two time intervals:
        - `Shouting`, from `10:00` for `30` minutes,
        - `Speaking`, from `11:15` for `15` minutes.
    - `group_2` has **1 interaction**, in a single time interval:
        - `Shouting` from `10:15` for `30` minutes.

!!! note
    Regardless of whether the `occupancy` is defined or not, the input format should follow this structure.

    Extensive validation is conducted in the algorithm to guarantee that the interactions are related to an existing occupancy group, and that the times are within the concerned group simulation time.

!!! warning 
    Short-range interactions cannot overlap within the same group, i.e. only one short-range interaction per group is allowed for any given time.

#### Model generator (development mode)

Following the previous JSON example of the `occupancy` input, the `ExposureModelGroups` object that would be generated would have the following structure:

???+ note "Structure"
    
        ExposureModelGroup(
            ExposureModel(
                data_registry=...,
                concentration_model=concentration_model_infected,
                short_range=(
                    ShortRangeModel(
                        data_registry=...,
                        expiration="Shouting",
                        activity=...,
                        presence=SpecificInterval(((10., 11.5),)),
                        distance=...,
                    ),
                    ShortRangeModel(
                        data_registry=...,
                        expiration="Shouting",
                        activity=...,
                        presence=SpecificInterval(((11.25, 11.5),)),
                        distance=...,
                    ),
                ),
                exposed=Population(
                    number=3,
                    presence=SpecificInterval(((9., 12.), (13., 17.))),
                    activity=...,
                    mask=...,
                    host_immunity=...,
                ),
                geographical_data=...,
                exposed_to_short_range=...,
                identifier="group_1',
            ),
            ExposureModel(
                data_registry=...,
                concentration_model=concentration_model_infected,
                short_range=(
                    ShortRangeModel(
                        data_registry=...,
                        expiration="Shouting",
                        activity=...,
                        presence=SpecificInterval(((10.25, 10.75),)),
                        distance=...,
                    ),
                ),
                exposed=Population(
                    number=5,
                    presence=SpecificInterval(((10., 11.),)),
                    activity=...,
                    mask=...,
                    host_immunity=...,
                ),
                geographical_data=...,
                exposed_to_short_range=...,
                identifier="group_2",
            )
        )

    !!!note
        Each occupancy group (`group_1` and `group_2`) leads to the creation of one `ExposureModel`, and the `ConcentrationModel`, originated from the combination of the `presence` and `infected`, is the same for all `ExposureModel` groups.
       
        In this case, the `InfectedPopulation` will be composed of the following `number (IntPiecewiseConstant)`:
        
        - `2 people`, from `09:00` to `10:00`
        - `7 people`, from `10:00` to `11:00`
        - `2 people`, from `11:00` to `12:00`
        - `0 people`, from `12:00` to `13:00`
        - `2 people`, from `13:00` to `17:00`

### Results structure (model output)

After the defining the simulation and when making a request to the API, the response is structured as a JSON object that consists of a `status` field indicating success or failure, along with a `message` providing additional details. If successful, the `report_data` object contains the computed exposure results per group and model configuration.

???+ example

        {
            "status": "success",
            "message": "Results generated successfully",
            "report_data": {
                "model": ..., 
                "times": ..., 
                "CO2_concentrations": ..., 
                "groups": {
                    "group_1": { 
                        "prob_inf": ..., 
                        "prob_inf_sd": ..., 
                        "prob_dist": ..., 
                        "prob_hist_count": ..., 
                        "prob_hist_bins": ..., 
                        "expected_new_cases": ..., 
                        "exposed_presence_intervals": ..., 
                        "concentrations": ..., 
                        "cumulative_doses": ..., 
                        "long_range_prob": ..., 
                        "long_range_expected_new_cases": ..., 
                        "short_range_interactions": ..., 
                        "concentrations_zoomed": ..., 
                        "long_range_cumulative_doses": ...
                    },
                    "group_2": ...
                }
            }
        }

    The output response is structured as follows:

    - Top-Level Fields:

        - `status` (string) – Indicates whether the request was successful (`"success"`) or if an error occurred (`"error"`).
        - `message` (string) – Provides a brief description of the response outcome.

    - `report_data` Object:

        - `model` (object) – Representation of the exposure model used.
        - `times` (array) – Full simulation timestamps.
        - `CO2_concentrations` (array) – CO<sub>2</sub> concentration levels over time.
        - `groups` (object) – Contains the exposure results for each group.

    - `groups` Object:

        Each key inside groups corresponds to a specific group (e.g., `"group_1"`, `"group_2"`) and contains the following fields:

        - `prob_inf` (float) – Mean probability of infection. For occupant groups **with** short-range interactions, this includes both short- and long-range exposures.
        - `prob_inf_sd` (float) – Standard deviation of the probability of infection.
        - `prob_dist` (array) – Probability distribution values.
        - `prob_hist_count` (array) – Histogram counts for probability distribution.
        - `prob_hist_bins` (array) – Histogram bin edges for probability distribution.
        - `expected_new_cases` (float) – Expected number of new cases within the group.
        - `exposed_presence_intervals` (array) – Time intervals when group members were exposed.
        - `concentrations` (array) – Viral concentration levels over time.
        - `cumulative_doses` (array) – Accumulated viral doses over time.

        If short-range interactions are considered, additional fields will be included:

        - `long_range_prob` (float) – Mean probability of infection of occupant groups **without** short-range interactions.
        - `long_range_expected_new_cases` (float) – Expected number of new cases of occupant groups **without** short-range interactions.
        - `short_range_interactions` (object) – Contains expiration times and short-range exposure data.
        - `concentrations_zoomed` (array) – Higher-resolution long-range concentration data.
        - `long_range_cumulative_doses` (array) – Accumulated viral doses from long-range interactions.

    !!!note
        Regardless of whether the `occupancy` is defined or not, the output format will always follow the described structure.
        When using the *legacy* structure, a group object with a predefined identifier is created (`group_1`).

## Conclusion

The dynamic occupancy feature enhances CAiMIRA's flexibility by allowing to define different occupancy groups in a certain event, leading to a more detailed and accurate risk assessment in heterogenous environments.

For examples on how to extend and use the REST API, see [REST API](rest_api.md).
