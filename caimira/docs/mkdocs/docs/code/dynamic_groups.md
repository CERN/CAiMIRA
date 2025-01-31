# Dynamic Occupancy Groups

The dynamic occupancy introduces the capability to handle multiple **exposure** groups within an event. Instead of having one single set of parameters for all the exposed (susceptible) occupants, this feature enables the model to have *n* groups, each with a specific occupancy profile and set of short-range interactions. This will facilitate more accurate risk assessments in a more heterogenous environment. This can also be used to define dynamic groups for the [CO<sub>2</sub> fitting algorithm](fitting_algorithm.md).

!!!note
    When in development mode, this feature enables the model to have *n* groups, each with their specific characteristics, e.g. masks, physical activity or host immunities.

This page covers the [description](#feature-description), [input structure](#input-structure), and [results structure](#output-structure) of this feature.

## Feature Description

The feature revolves around the concept of a new `ExposureModelGroup` class, which encapsulates a set of `ExposureModel` instances. Each `ExposureModel` represents a distinct group of exposed occupants.

### Input Structure

The modelling of dynamic groups is controlled by the `occupancy_format` input, set as `static` by default. To enable it, the corresponding value should be set to `dynamic`:

```
occupancy_format = "dynamic"
```

#### Definition: Exposed occupants

The `dynamic_exposed_occupancy` object defines the presence of exposed population groups over time. Each group should be identified by a unique key (`group_1`, `group_2`, etc.), mapping to an object that specifies:

- `total_people`: The total number of **exposed** individuals in the group.
- `presence`: A list of time intervals (`start_time` and `finish_time`) during which the group was present, formatted as `HH:MM`.

!!!example

        dynamic_exposed_occupancy = {
            "group_1": {
                "total_people": 5,
                "presence": [
                    {"start_time": "09:00", "finish_time": "12:00"},
                    {"start_time": "13:00", "finish_time": "17:00"}
                ]
            },
            "group_2": {
                "total_people": 10,
                "presence": [
                    {"start_time": "10:00", "finish_time": "11:00"}
                ]
            }
        }

    - `group_1` consists of **5 individuals** present in two time intervals:
        - `09:00` to `12:00`.
        - `13:00` to `17:00`.
    - `group_2` consists of **10 individuals**, present from:
        - `10:00` to `11:00`.

#### Definition: Infected occupants

Unlike the `dynamic_exposed_occupancy`, the `dynamic_infected_occupancy` represents a single group of infected occupants that contributes to all exposure groups. It should be defined as a list where each entry defines a time interval during which infected individuals were present. Each entry includes:

- `total_people`: the total number of **infected** individuals in the group,
- `start_time` and `finish_time`: the time boundaries at which the occupants were present, formatted as `HH:MM`.

!!!example

        dynamic_infected_occupancy = [
            {"total_people": 2, "start_time": "10:00", "finish_time": "12:00"},
            {"total_people": 3, "start_time": "13:00", "finish_time": "17:00"}
        ]

    The **infected** group consists of:

    - `2` present from `10:00` to `12:00`,
    - `3` people present from `13:00` to `17:00`.

!!!info
    While the `dynamic_exposed_occupancy` results in the creation of multiple `ExposureModel` objects, the `dynamic_infected_occupancy` leads to a single `InfectedPopulation` object that is replicated across all `ExposureModel`. 
    
    This means that the infected population contributes uniformly to the concentration in each exposure model.

#### Short-range interactions

The `short_range_interactions` object defines the number of short-range interactions per **exposure** group. Each set of interactions is identified by its corresponding exposure group key (`group_1`, `group_2`, etc.), mapping to an object that specifies:

- `expiration`: expiration type of that short-range interaction (`Breathing`, `Speaking`, or `Shouting`).
- `start_time`: when the interaction starts, formatted as `HH:MM`.
- `duration`: duration of the interaction (in minutes). 

!!!example

        short_range_interactions = {
            "group_1": [
                {"expiration": "Shouting", "start_time": "10:00", "duration": 30},
                {"expiration": "Speaking", "start_time": "11:10", "duration": 15}
            ],
            "group_2": [
                {"expiration": "Shouting", "start_time": "10:10", "duration": 30}
            ]
        }

    - `group_1` has **2 interactions** in two time intervals:
        - `Shouting`, from `10:00` for `30` minutes,
        - `Speaking`, from `11:10` for `15` minutes.
    - `group_2` has **1 interaction**, in a single time interval:
        - `Shouting` from `10:10` for `30` minutes.

!!! note
    Extensive validation is conducted in the algorithm to guarantee that the interactions are related to an existing **exposure** group, and that the times are within the concerned exposure group simulation time.

!!! warning 
    Short-range interactions cannot overlap within the same group, i.e. only one short-range interaction per group is allowed for any given time.

### Results structure (model output)

After the defining the simulation and when making a request to the API, the response is structured as a JSON object that consists of a `status` field indicating success or failure, along with a `message` providing additional details. If successful, the `report_data` object contains the computed exposure results per group and model configuration.

!!!example

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
                        "long_range_R0": ..., 
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
        Regardless of whether the `occupancy_format` is `static` or `dynamic`, the output format will always follow the described structure.
        When using a `static` structure, a group object with a predefined identifier is created.

## Conclusion

The dynamic occupancy feature enhances CAiMIRA's flexibility to apply different groups to the occupants in the event, allowing for a more detailed and accurate assessment of risk.

The `occupancy_format` entry must be set to `dynamic` and the `dynamic_exposed_occupancy`, `dynamic_infected_occupancy`, and `short_range_interactions` correctly defined, as detailed above, for the feature to work properly.

For examples on how to extend and use the REST API, see [REST API](rest_api.md).