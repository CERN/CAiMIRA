# Dynamic Occupancy Model

## Overview

The dynamic occupancy model introduces the capability to handle multiple exposure groups within the population, facilitating more accurate assessments of the probability of infection and expected new cases results. This page covers the structure, usage, and JSON format of this feature.

## Feature Description

The feature revolves around the concept of `ExposureModelGroup`, which encapsulates a set of `ExposureModel` instances. Each `ExposureModelGroup` represents a distinct group of individuals exposed to environmental conditions, allowing separate evaluation of infection risks and new case expectations.

### Data Structure

The dynamic groups modeling is controlled by the `occupancy_format` input, which is `static` by default. To enable the dynamic modelling, the corresponding value should be set to `dynamic`.

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

Unlike the `dynamic_exposed_occupancy`, the `dynamic_infected_occupancy` represents a single group of infected occupants that affects all exposure groups. It should be a list where each entry defines a time interval during which infected individuals were present. Each entry includes:
- `total_people`: the total number of **infected** individuals in the group,
- `start_time` and `finish_time`: the time at which the occupants were present, formatted as `HH:MM`.

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

Note that extensive validation is conducted in the algorithm to guarantee that the interactions are related to an existing exposure group, and that the times are within the exposure group simulation time. Within the same group, short-range interactions cannot overlap each other.

## Conclusion

The dynamic occupancy model feature enhances CAiMIRA's capabilities by allowing detailed assessment of exposure groups' impacts on infection dynamics.

On examples on how to extend and use the REST API please refer to the [REST API]('./rest_api') page. Recall that `occupancy_format` must be set to `dynamic` and `dynamic_exposed_occupancy`, `dynamic_infected_occupancy`, and `short_range_interactions` correctly defined.