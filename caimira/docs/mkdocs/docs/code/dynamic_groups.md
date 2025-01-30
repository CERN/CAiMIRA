# Dynamic Occupancy Model

The dynamic occupancy model introduces the capability to handle multiple **exposure** groups within a single simulation, facilitating more accurate risk assessments, including the viral dose, probability of infection and expected new cases results. It can also be used to define groups and use the [CO<sub>2</sub> fitting algorithm](fitting_algorithm.md).

This page covers the [description](#feature-description), [input structure](#input-structure), and [output structure](#output-structure) of this feature.

## Feature Description

The feature revolves around the concept of `ExposureModelGroup`, which encapsulates a set of `ExposureModel` instances. Each `ExposureModelGroup` represents a distinct group of individuals exposed to environmental conditions, allowing separate evaluation of infection risks and new case expectations.

### Input Structure

The dynamic groups modeling is controlled by the `occupancy_format` input, set as `static` by default. To enable the dynamic modelling, the corresponding value should be set to `dynamic`:

```
occupancy_format = "dynamic"
```

#### Dynamic Exposed Occupants

The `dynamic_exposed_occupancy` object defines the presence of exposed population groups over time. Each group should be identified by a unique key (`group_1`, `group_2`, etc.), mapping to an object that specifies:

- `total_people`: The total number of **exposed** individuals in the group.
- `presence`: A list of time intervals (`start_time` and `finish_time`) during which the group was present, formatted as `HH:MM`.

##### Example Structure:

```
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
```

**Explanation:**

- `group_1` consists of **5 individuals** present in two time intervals:
    - `09:00` to `12:00`.
    - `13:00` to `17:00`.
- `group_2` consists of **10 individuals**, present from:
    - `10:00` to `11:00`.

#### Dynamic Infected Occupants

Unlike the `dynamic_exposed_occupancy`, the `dynamic_infected_occupancy` represents a single group of infected occupants that contributes to all exposure groups. It should be defined as a list where each entry defines a time interval during which infected individuals were present. Each entry includes:

- `total_people`: the total number of **infected** individuals in the group,
- `start_time` and `finish_time`: the time boundaries at which the occupants were present, formatted as `HH:MM`.

##### Example Structure

```
dynamic_infected_occupancy = [
    {"total_people": 2, "start_time": "10:00", "finish_time": "12:00"},
    {"total_people": 3, "start_time": "13:00", "finish_time": "17:00"}
]
```

**Explanation:**

The **infected** group consists of:

- `2` present from `10:00` to `12:00`,
- `3` people present from `13:00` to `17:00`.

#### Short-range interactions

Similar to `dynamic_exposed_occupancy`, the `short_range_interactions` object defines short-range interactions per **exposure** group over time. Each group should be identified by its corresponding exposure group key (`group_1`, `group_2`, etc.), mapping to an object that specifies:

- `expiration`: expiration type of that short-range interaction (`Breathing`, `Speaking`, or `Shouting`).
- `start_time`: when the interaction starts, formatted as `HH:MM`.
- `duration`: duration of the interaction (in minutes). 

##### Example Structure

```
short_range_interactions = {
    "group_1": [
        {"expiration": "Shouting", "start_time": "10:00", "duration": 30},
        {"expiration": "Shouting", "start_time": "11:10", "duration": 15}
    ],
    "group_2": [
        {"expiration": "Shouting", "start_time": "10:10", "duration": 30}
    ]
}
```

**Explanation:**

- `group_1` has **2 interactions** in two time intervals:
    - `Shouting`, from `10:00` for `30` minutes,
    - `Shouting`, from `11:10` for `15` minutes.
- `group_2` has **1 interaction**, in a single time interval:
    - `Shouting` from `10:10` for `30` minutes.

!!! info
    Note that extensive validation is conducted in the algorithm to guarantee that the interactions are related to an existing exposure group, and that the times are within the exposure group simulation time. 

!!! warning 
    Within the same group, short-range interactions cannot overlap each other.

### Output Structure

When making a request to the API, the response is structured as a JSON object that consists of a `status` field indicating success or failure, along with a `message` providing additional details. If successful, the `report_data` object contains the computed exposure results per group and model configuration.

##### Example Response

```
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
```

**Explanation:**

The output response is structured as follows:

###### Top-Level Fields:

- `status` (string) – Indicates whether the request was successful (`"success"`) or if an error occurred (`"error"`).
- `message` (string) – Provides a brief description of the response outcome.

###### `report_data` Object:

- `model` (object) – Representation of the exposure model used.
- `times` (array) – Full simulation timestamps.
- `CO2_concentrations` (array) – CO<sub>2</sub> concentration levels over time.
- `groups` (object) – Contains the exposure results for each group.

###### `groups` Object:

Each key inside groups corresponds to a specific group (e.g., `"group_1"`, `"group_2"`) and contains the following fields:

- `prob_inf` (float) – Mean probability of infection.
- `prob_inf_sd` (float) – Standard deviation of the probability of infection.
- `prob_dist` (array) – Probability distribution values.
- `prob_hist_count` (array) – Histogram counts for probability distribution.
- `prob_hist_bins` (array) – Histogram bin edges for probability distribution.
- `expected_new_cases` (float) – Expected number of new cases within the group.
- `exposed_presence_intervals` (array) – Time intervals when group members were exposed.
- `concentrations` (array) – Viral concentration levels over time.
- `cumulative_doses` (array) – Accumulated viral doses over time.

###### If short-range interactions are considered, additional fields will be included:

- `long_range_prob` (float) – Mean probability of infection from long-range transmission.
- `long_range_R0` (float) – Expected number of new cases from long-range transmission.
- `short_range_interactions` (object) – Contains expiration times and short-range exposure data.
- `concentrations_zoomed` (array) – Higher-resolution long-range concentration data.
- `long_range_cumulative_doses` (array) – Accumulated viral doses from long-range interactions.

!!! note
    Regardless of whether the structure is `static` or `dynamic`, the output format will always follow the described structure.
    When using a `static` structure, a group object with a predefined identifier is created.

## Conclusion

The dynamic occupancy model feature enhances CAiMIRA's capabilities by allowing detailed assessment of exposure groups' impacts on infection dynamics.

On examples on how to extend and use the REST API please refer to the [REST API]('./rest_api') page. Recall that `occupancy_format` must be set to `dynamic` and `dynamic_exposed_occupancy`, `dynamic_infected_occupancy`, and `short_range_interactions` correctly defined.