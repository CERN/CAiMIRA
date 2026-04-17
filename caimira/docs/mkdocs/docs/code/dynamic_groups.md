# Dynamic Occupancy Groups

The dynamic occupancy introduces the capability to handle multiple occupancy
groups, composed of **infected** and/or **exposed** population, within an event.
Instead of having one single set of parameters for all the exposed (susceptible)
occupants, this feature allows the model to have *n* groups, each with a
specific occupancy profile and set of short-range interactions. This can
also be used to define dynamic occupancy groups for the
[CO<sub>2</sub> fitting algorithm](fitting_algorithm.md).

!!!tip
    When in [development mode](#model-generator-development-mode), this
    feature allows the model to have *n* groups, each with their specific
    characteristics, e.g. masks, physical activity or host immunities.
    Check below for more details.

This page covers the [description](#feature-description),
[input structure](#input-structure),
and [results structure](#results-structure-model-output) of this feature.

## Feature Description

The feature revolves around the concept of a new
[`ExposureModelGroup`](models.md/#exposuremodelgroup-class) class, which
encapsulates a set of [`ExposureModel`](models.md/#exposuremodel-class)
instances. Each `ExposureModel` represents a distinct group of exposed occupants.

### Input Structure

The modelling of dynamic occupancy with the definition of groups is
controlled by the `occupancy` input sent by the frontend (in
`src/caimira/calculator/validators/form_validator.py`), initially defined
by an empty dictionary:

```
occupancy = {}
```

In case the `occupancy` is not given as input in the request, or if its
value is set to the default (empty dictionary), the algorithm will work
as in the *legacy* version of CAiMIRA, i.e. with a single group, the timing
of which are defined via the keys (sent by the frontend):
```
{
    'infected_coffee_break_option': 'coffee_break_0',
    'infected_coffee_duration': 5,
    'infected_dont_have_breaks_with_exposed': False,
    'infected_finish': '17:30',
    'infected_lunch_finish': '13:30',
    'infected_lunch_option': True,
    'infected_lunch_start': '12:30',
    'infected_people': 1,
    'infected_start': '08:30',
    'exposed_coffee_break_option': 'coffee_break_0',
    'exposed_coffee_duration': 5,
    'exposed_finish': '17:30',
    'exposed_lunch_finish': '13:30',
    'exposed_lunch_option': True,
    'exposed_lunch_start': '12:30',
    'exposed_start': '08:30',
}
```

here given with their default values.

#### Parameters

The `occupancy` object defines various occupancy groups, each identified
by an unique key (`group_1`, `group_2`, etc.). Each group includes:

- `total_people`: The total number of individuals in the group, including
both infected and exposed individuals
- `infected`: The total number of infected individuals in the group
- `presence`: A list of time intervals (`start_time` and `finish_time`)
during which the group was present, formatted as `HH:MM`

!!!note
    The `infected` value must be an integer that does not exceed
    `total_people` and has a minimum value of `0` (case when the group
    consists solely of exposed individuals). The group key is a custom
    string chosen by the user to identify the respective group.

<span id="Example">
???+ example "Example"

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

    - The first group, identified by `group_1`, consists of
    **5 individuals (3 exposed, 2 infected)**, present in two time intervals:
        - `09:00` to `12:00`
        - `13:00` to `17:00`
    - The second group, identified by `group_2`, consists of
    **10 individuals (5 exposed, 5 infected)**, present from:
        - `10:00` to `11:00`

!!!info
    The number of groups in the `occupancy` input results in the creation
    of multiple `ExposureModel` objects. From the previous example, where
    two groups are defined, the two exposure instances will have the
    following exposed population, respectively:

    - **Exposed population from `group_1`** - `3` people from `09:00`
    to `12:00` and from `13:00` to `17:00`
    - **Exposed population from `group_2`** - `5` people from `10:00` to `11:00`
    
    The combination of the `presence` and number of `infected` of all groups
    leads to the creation of a single infected object **(`InfectedPopulation`)**,
    which is replicated across all groups. From the previous example, the
    respective instance will be composed of the following structure:
        
    - **`2` infected**, from `09:00` to `10:00` (`2` people from `group_1` and `0` people from `group_2`)
    - **`7` infected**, from `10:00` to `11:00` (`2` people from `group_1` and `5` people from `group_2`)
    - **`2` infected**, from `11:00` to `12:00` (`2` people from `group_1` and `0` people from `group_2`)
    - **`0` infected**, from `12:00` to `13:00` (`0` people from `group_1` and `0` people from `group_2`)
    - **`2` infected**, from `13:00` to `17:00` (`2` people from `group_1` and `0` people from `group_2`)
    
    Note that the infected population contributes equally to the **long-range**
    concentration in **all the occupant groups**.

#### Short-range interactions

In the frontend (in `src/caimira/calculator/validators/virus/virus_validator.py`),
the `short_range_interactions` object defines the short-range interactions
for each occupancy group. Each set of interactions is identified by its
corresponding group key (`group_1`, `group_2`, etc.), mapping to an object
that specifies:

- `expiration`: expiration type of that short-range interaction (`Breathing`,
`Speaking`, or `Shouting`)
- `start_time`: when the interaction starts, formatted as `HH:MM`
- `duration`: duration of the interaction (in minutes)

Short-range interactions are processed separately from the long-range
exposure. Each short-range object in the same group assumes that the same
exposed occupant in that group is interacting with one of the infectors
during the specified period. In other words, these interactions are all
linked to the same occupant and the total short-range exposure will be
the cumulative sum of all the short-range objects in the occupancy group.
To be able to appoint different short-range interactions to different
exposed occupants in a given group, a workaround is to subdivide them
into smaller groups --- see examples below.

<span id="Example-1">
???+ example "Example 1"

    The occupancy object is the one defined above ([here](#parameters)).

        short_range_interactions = {
            "group_1": [
                {"expiration": "Shouting", "start_time": "10:00", "duration": 30},
                {"expiration": "Speaking", "start_time": "11:15", "duration": 15}
            ],
            "group_2": [
                {"expiration": "Shouting", "start_time": "10:15", "duration": 30}
            ]
        }

    - `group_1` has **2 interactions with exposed occupant A** in two time intervals:
        - `Shouting`, from `10:00` for `30` minutes
        - `Speaking`, from `11:15` for `15` minutes
    - `group_2` has **1 interaction with exposed occupant B**, in a single time interval:
        - `Shouting` from `10:15` for `30` minutes

???+ example "Example 2"

        occupancy = {
            "group_1_A": {
                "total_people": 4,
                "infected": 1,
                "presence": [
                    {"start_time": "09:00", "finish_time": "12:00"},
                    {"start_time": "13:00", "finish_time": "17:00"}
                ]
            },
            "group_1_B": {
                "total_people": 1,
                "infected": 1,
                "presence": [
                    {"start_time": "09:00", "finish_time": "12:00"},
                    {"start_time": "13:00", "finish_time": "17:00"}
                ]
            },
            ...
        }

        ...

        short_range_interactions = {
            "group_1_A": [
                {"expiration": "Shouting", "start_time": "10:00", "duration": 30},
            ],
            "group_1_B": [
                {"expiration": "Speaking", "start_time": "11:15", "duration": 15}
            ],
        }

    - `group_1_A` has **1 interaction with exposed occupant A** in a single time interval:

        - `Shouting`, from `10:00` for `30` minutes,

    - `group_1_B` has **1 interaction with exposed occupant B** in a single time interval:

        - `Speaking`, from `11:15` for `15` minutes.


!!! note
    The input format must follow this dictionary structure, regardless of
    whether `occupancy` is defined. For example, in the *legacy* format,
    the short-range group should always be specified within a dictionary
    under the identifier `group_1`, as this is the default single-group
    identifier (see [here](../models/#identifier-str-group_1)).

    Extensive validation is conducted in the algorithm to guarantee that
    the interactions are related to an existing occupancy group (if applicable),
    and that the times are within the concerned group simulation time.

!!! warning 
    Short-range interactions cannot overlap within the same group. At any
    given time, only one short-range interaction between the exposed and
    infected individuals is allowed per group.

#### Model generator (development mode)

Following the previous example ([here](#Example) and [here](#Example-1))
of the `occupancy` input, the `ExposureModelGroup` object that would be
generated should have the following structure:

???+ note "Structure"
    
        model=ExposureModelGroup(
            exposure_models=(
                ExposureModel(
                    data_registry=...,
                    concentration_model=concentration_model_infected,
                    short_range=(
                        ShortRangeModel(
                            data_registry=...,
                            infected=...,
                            short_range_activity=...,
                            short_range_expiration=...,
                            presence=SpecificInterval(((10., 10.5),)),
                            distance=...,
                        ),
                        ShortRangeModel(
                            data_registry=...,
                            infected=...,
                            short_range_activity=...,
                            short_range_expiration=...,
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
                            infected=...,
                            short_range_activity=...,
                            short_range_expiration=...,
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
            ),
            data_registry=...,
        )

    In which the `ConcentrationModel` object should have the following structure:

        concentration_model_infected=ConcentrationModel(
            data_registry=...,
            room=...,
            ventilation=...,
            infected=InfectedPopulation(
                data_registry=...,
                number=IntPiecewiseConstant(
                    transition_times=(9.0, 10.0, 11.0, 12.0, 13.0, 17.0),
                    values=(2, 7, 2, 0, 2),
                ),
                presence=None,
                virus=...,
                mask=...,
                activity=...,
                expiration=...,
                host_immunity=...,
            ),
            evaporation_factor=...,
        )

    In line with the example above, we see:
    
    - 2 `ExposureModel`: one for each occupancy group
    - 3 `ShortRangeModel`: two for `group_1` and one for `group_2`
    - In the `exposed` population (`Population`):
        - the `number` is calculated from `total_people` - `infected`
        - the `presence` interval is taken from the `occupancy` group object
        - the `mask`, `activity`, etc. can be different for each group
    - In  the `infected` population (`InfectedPopulation`):
        - the `number` interval is calculated from the `occupancy` group
        object as a total sum of the infected from all groups at each `presence` interval
        - the `activity' describes all the physical activities performed by the 
        infected population throughout their presence. The type of physical activity is 
        treated as a constant mixture of all the physical activities performed.
        - the `expiration' describes all the expiratory activities performed by 
        the infected population throughout their presence. The type of expiratory activity is 
        treated as a constant mixture of all the expiratory activities performed.
    - In  the `ShortRangeModel`:
        - the `short_range_activity' describes the physical activities performed by the 
        infected population during the short-range interaction only. 
        - the `short_range_expiration' describes the expiratory activities performed by 
        the infected population during the short-range interaction only. 
    - The `ConcentrationModel` shall be the same in each `ExposureModel`

    !!!note
        As previously described, each occupancy group (`group_1` and `group_2`)
        leads to the creation of one `ExposureModel`, and the `ConcentrationModel`,
        originated from the combination of the `presence` and number of
        `infected`, should be the same for all `ExposureModel` groups.
       
        Note that the `InfectedPopulation` object is shared across all groups,
        meaning the infected population contributes equally to the concentration
        in each model. To ensure consistency, the algorithm verifies that the
        `number` and `presence` parameters of `InfectedPopulation` remain
        identical across all `ExposureModel` instances.

        Also, note that the types of physical and expiratory activities of the infected 
        performed during short-range interactions must also cotribute to the overall 
        combination of physical and expiratory activities performed by that infected 
        throughout their total presence. That is, the type(s) of physical/expiratory activity(ies) 
        in `ShortRangeModel.short_range_activity`/`ShortRangeModel.short_range_expiration` must 
        be in the physical/expiratory activity(ies) of 
        `ShortRangeModel.infected.activity`/`ShortRangeModel.infected.expiration`. For example, 
        if the type of `short_range_expiration' is "Shouting", then the type of
        `infected.expiration' may be 1/2 "Shouting" and 1/2 "Speaking".

    ??? tip "How to interpret one `IntPiecewiseConstant` instance?"

        The `IntPiecewiseConstant` inherits from the `PiecewiseConstant`
        (see [here](../models/#intpiecewiseconstant-class)), and expects
        the `transition_times` and `values` as arguments (`values` should be integers).
                
        In the provided example, the infected population has `transition_times`
        of `(9.0, 10.0, 11.0, 12.0, 13.0, 17.0)` with corresponding values
        `(2, 7, 2, 0, 2)`. This data can be interpreted as follows:

        - Between `9.0 (09:00)` and `10.0 (10:00)`, `2` infected were present
        - Between `10.0 (10:00)` and `11.0 (11:00)`, `7` infected were present
        - Between `11.0 (11:00)` and `12.0 (12:00)`, `2` infected were present 
        - Between `12.0 (12:00)` and `13.0 (13:00)`, `0` infected were present 
        - Between `13.0 (13:00)` and `17.0 (17:00)`, `2` infected were present 

### Results structure (model output)

After defining the simulation and when making a request to the API, the
response (in `src/caimira/api/routes/report_routes.py`) is structured as
a JSON object that consists of a `status` field indicating success or failure,
along with a `message` providing additional details. If successful, the
`report_data` object (from `src/caimira/calculator/report/virus_report_data.py`)
contains the computed exposure results per group and model configuration.

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

    - Top-level Fields:

        - `status` (string) – Indicates whether the request was successful
        (`"success"`) or if an error occurred (`"error"`).
        - `message` (string) – Provides a brief description of the response outcome.

    - `report_data` Object:

        - `model` (object) – Representation of the exposure model used.
        - `times` (array) – Full simulation timestamps.
        - `CO2_concentrations` (array) – CO<sub>2</sub> concentration levels over time.
        - `groups` (object) – Contains the exposure results for each group.

    - `groups` Object:

        Each key inside groups corresponds to a specific group (e.g., `"group_1"`,
        `"group_2"`) and contains the following fields:

        - `prob_inf` (float) – Mean probability of infection. For occupant
        groups **with** short-range interactions, this includes both
        short- and long-range exposures.
        - `prob_inf_sd` (float) – Standard deviation of the probability of infection.
        - `prob_dist` (array) – Probability distribution values.
        - `prob_hist_count` (array) – Histogram counts for probability distribution.
        - `prob_hist_bins` (array) – Histogram bin edges for probability distribution.
        - `expected_new_cases` (float) – Expected number of new cases within the group.
        - `exposed_presence_intervals` (array) – Time intervals when group members were exposed.
        - `concentrations` (array) – Viral concentration levels over time.
        - `cumulative_doses` (array) – Accumulated viral doses over time.

        If short-range interactions are considered, additional fields will be included:

        - `long_range_prob` (float) – Mean probability of infection of
        occupant groups **without** short-range interactions.
        - `long_range_expected_new_cases` (float) – Expected number of
        new cases of occupant groups **without** short-range interactions.
        - `short_range_interactions` (object) – Contains expiration times
        and short-range exposure data.
        - `concentrations_zoomed` (array) – Higher-resolution long-range
        concentration data.
        - `long_range_cumulative_doses` (array) – Accumulated viral doses
        from long-range interactions.

    !!!note
        Regardless of whether the `occupancy` is defined or not, the output
        format will always follow the described structure.
        When using the *legacy* structure, a group object with a predefined
        identifier is created (`group_1`).

## Conclusion

The dynamic occupancy feature enhances CAiMIRA's flexibility by allowing to
define different occupancy groups in a certain event, leading to a more
detailed and accurate risk assessment in heterogenous environments.

For examples on how to extend and use the REST API, see [REST API](rest_api.md).
