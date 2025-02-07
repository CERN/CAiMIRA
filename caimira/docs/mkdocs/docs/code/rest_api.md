# CAiMIRA REST API

The API enables third-party applications to interact with the CAiMIRA [backend](https://gitlab.cern.ch/caimira/caimira), making integration easier and more flexible. This page covers the CAiMIRA [package structure](#directory-layout-key-components) and [API usage](#rest-api-overview).

## Package Overview

With the implementation of the REST API, the CAiMIRA repository now consists of two distinct Python packages:

* `caimira`: The core package containing all backend logic. This package will be published to [PyPi](https://pypi.org/) and it is the central engine to process the input data and generate the results. It was designed to be flexible, supporting a wide range of external integrations without being tied to any particular User Interface (UI).

* `cern_caimira`: A package that extends `caimira` and provides CERN-specific UI implementation. External users typically won't need this.

By separating the backend logic from the UI, the CAiMIRA project achieves better modularity and flexibility, allowing external users to work with the core functionality without depending on CERN-specific configuration or UI.

The `app-config` directory at the root of the project is specific to the CERN environment and includes the components necessary for deploying the backend and UI on the [OKD](https://paas.cern.ch/) platform.

## Directory Layout // Key Components

* `src/caimira/api`: Contains the REST API implementation, defining the endpoints, request handling, and input/output formats.
    * `/app.py` : Entry point for the CAiMIRA backend, powered by the [Tornado](https://www.tornadoweb.org/en/stable/) framework. It sets up the server, defines the routes for handling reports, and starts the Tornado I/O loop.
    * `/controller`: Contains the core logic for handling incoming API requests. It interprets user input, interact with models, and send responses back to the client. 
    * `/routes`: Defines the API endpoints and associate them with the corresponding controller functions.
* `src/caimira/calculator`: contains the core models used in CAiMIRA for processing inputs and generating outputs.
    * `/models`: Contains the classes reponsible to define the whole object oriented hierarchical model.
    * `/report`: Manages the generation of report data based on the processed input.
    * `/store`: Contains the data store and registry.
    * `/validators`: Contains validation logic to ensure that input data conforms to expected formats and constraints before processing.

* `tests/`: Contains unit tests and integration tests for the `caimira` package to ensure it functions correctly.

## REST API Overview

The newly implemented REST API allows external applications to interact with CAiMIRA backend programmatically, making it easier to submit data, process it within CAiMIRA's model engine, and retrieve the results.

### API Structure

The API is served by the **Tornado** web framework, which provides asynchronous handling for client requests. The API serves requests on a specific port (by default, `8081`), and support standard HTTP methods, such as `POST` for data submission.

#### Key Features

* **Input Data Handling**: Accepts well-defined JSON input formats.
* **Report Generation**: Processes input data through CAiMIRA's model and generates detailed reports.
* **Status Codes**: Provides standard HTTP status codes for succes, failure, and validation errors.

#### Running the API

To run the API, follow these steps from the root directory of the project:

1. Install dependencies (two options available):
    - From previously cloned [GitLab Repository](https://gitlab.cern.ch/caimira/caimira):

            cd caimira
            pip install -e .
    
    - From [PyPI](https://pypi.org/project/caimira/):

            pip install caimira
    
2. Run the backend:

        python -m caimira.api.app

    The web server will be accessible at [http://localhost:8081/](http://localhost:8081/).
    
### API Endpoints

Currently, the REST API contains two routing categories that provide the generation of results for the main CAiMIRA outputs:

- [Virus results](#virus-results)
- [CO₂ results](#co2-results)

!!! note
    As the project is growing, more routes targeted to specific tasks will be developed.

#### Virus Results

??? Abstract "POST **/virus/report** (virus report data generation):"
    
    * **Description**: Core endpoint that allows users to submit data for the virus report generation. Data is processed by the CAiMIRA engine, and the results are returned in the response.
    * **Input**: The body of the request must include the necessary input data in JSON format. Examples of the required input can be found [here](https://gitlab.cern.ch/caimira/caimira/-/blob/master/caimira/src/caimira/calculator/validators/defaults.py?ref_type=heads).
    * **Response**: On success (status code `200`), the response will contain the following structure:

            {
                "status": "success",
                "message": "Results generated successfully",
                "results": {
                ...
                }
            }
            
    * **Error Handling**: In case of errors, the API will return appropriate error messages and HTTP status codes, such as `400` for bad requests, `404` for not found, or `500` for internal server errors.

    ??? note "Example body"        
            {
                "activity_type": "office",
                "calculator_version": "N/A",
                "event_month": "January",
                "exposed_finish": "18:00",
                "exposed_lunch_finish": "13:30",
                "exposed_lunch_start": "12:30",
                "exposed_start": "09:00",
                "infected_finish": "18:00",
                "infected_lunch_finish": "13:30",
                "infected_lunch_start": "12:30",
                "infected_people": "1",
                "infected_start": "09:00",
                "inside_temp": "293.",
                "location_latitude": 46.20833,
                "location_longitude": 6.14275,
                "location_name": "Geneva",
                "opening_distance": "0.2",
                "room_number": "123",
                "room_volume": "75",
                "simulation_name": "Test",
                "total_people": "10",
                "ventilation_type": "natural_ventilation",
                "virus_type": "SARS_CoV_2_OMICRON",
                "volume_type": "room_volume_explicit",
                "window_height": "2",
                "window_opening_regime": "windows_open_permanently",
                "window_type": "window_sliding",
                "window_width": "2",
                "windows_duration": "10",
                "windows_frequency": "60",
                "windows_number": "1"
            }

    For the full list of accepted inputs and respective values please refer to CAiMIRA's official defaults in GitLab repository [here](https://gitlab.cern.ch/caimira/caimira/-/blob/master/caimira/src/caimira/calculator/validators/co2/co2_validator.py?ref_type=heads#L29).

    ??? note "Example cURL (with the above body)"
        
            curl -X POST "http://localhost:8081/virus/report" \
            -H "Content-Type: application/json" \
            -d '{
                "activity_type": "office",
                "calculator_version": "N/A",
                "event_month": "January",
                "exposed_finish": "18:00",
                "exposed_lunch_finish": "13:30",
                "exposed_lunch_start": "12:30",
                "exposed_start": "09:00",
                "infected_finish": "18:00",
                "infected_lunch_finish": "13:30",
                "infected_lunch_start": "12:30",
                "infected_people": "1",
                "infected_start": "09:00",
                "inside_temp": "293.",
                "location_latitude": 46.20833,
                "location_longitude": 6.14275,
                "location_name": "Geneva",
                "opening_distance": "0.2",
                "room_number": "123",
                "room_volume": "75",
                "simulation_name": "Test",
                "total_people": "10",
                "ventilation_type": "natural_ventilation",
                "virus_type": "SARS_CoV_2_OMICRON",
                "volume_type": "room_volume_explicit",
                "window_height": "2",
                "window_opening_regime": "windows_open_permanently",
                "window_type": "window_sliding",
                "window_width": "2",
                "windows_duration": "10",
                "windows_frequency": "60",
                "windows_number": "1"
            }'

    **Note**: The `report_generation_parallelism` can be passed as an argument with integer values. If omitted, `None` will be considered by default.

#### CO₂ Results

??? Abstract "POST **/co2/transition_times** (suggested ventilation transition times)"
    
    * **Description**: Endpoint that allows users to retrieve the suggested ventilation times based on the CO₂ input data. Data is processed by the CAiMIRA engine, and the results are returned in the response.

    ??? note "Example body"

            {    
                "CO2_data": "{\"times\":[8.000,8.033,8.067,8.100,8.133,8.167,8.200,8.233,8.267,8.300,8.333,8.367,8.400,8.433,8.467,8.500,8.533,8.567,8.600,8.633,8.667,8.700,8.733,8.767,8.800,8.833,8.867,8.900,8.933,8.967,9.000,9.033,9.067,9.100,9.133,9.167,9.200,9.233,9.267,9.300,9.333,9.367,9.400,9.433,9.467,9.500,9.533,9.567,9.600,9.633,9.667,9.700,9.733,9.767,9.800,9.833,9.867,9.900,9.933,9.967,10.000,10.033,10.067,10.100,10.133,10.167,10.200,10.233,10.267,10.300,10.333,10.367,10.400,10.433,10.467,10.500,10.533,10.567,10.600,10.633,10.667,10.700,10.733,10.767,10.800,10.833,10.867,10.900,10.933,10.967,11.000,11.033,11.067,11.100,11.133,11.167,11.200,11.233,11.267,11.300,11.333,11.367,11.400,11.433,11.467,11.500,11.533,11.567,11.600,11.633,11.667,11.700,11.733,11.767,11.800,11.833,11.867,11.900,11.933,11.967,12.000,12.033,12.067,12.100,12.133,12.167,12.200,12.233,12.267,12.300,12.333,12.367,12.400,12.433,12.467,12.500,12.533,12.567,12.600,12.633,12.667,12.700,12.733,12.767,12.800,12.833,12.867,12.900,12.933,12.967,13.001],\"CO2\":[445.189,443.284,440.908,443.431,442.366,444.094,445.152,445.656,447.968,447.998,443.950,442.547,439.313,438.225,441.433,441.190,443.804,445.173,446.494,445.278,452.073,458.844,470.828,478.147,488.338,502.126,522.057,545.519,579.881,616.245,641.154,676.288,701.938,720.464,746.933,765.830,779.098,794.173,810.624,825.967,838.340,854.355,876.382,886.208,898.408,921.718,942.848,953.812,978.956,990.321,1002.931,1017.361,1029.379,1041.028,1051.883,1067.220,1073.530,1079.738,1093.733,1104.814,1125.798,1141.115,1151.046,1160.053,1176.367,1193.665,1180.104,1015.334,864.746,802.681,774.455,728.268,697.326,676.063,657.555,640.564,606.534,595.925,577.753,553.605,530.213,524.968,523.153,521.534,512.944,505.297,502.056,502.463,505.248,507.477,509.171,511.313,513.780,520.393,529.137,532.798,530.111,523.964,521.574,519.052,510.294,509.982,514.349,518.396,524.603,521.003,519.448,523.313,527.460,528.326,526.355,527.008,529.968,534.019,535.616,533.514,530.552,522.348,524.243,532.021,539.127,538.836,526.186,517.509,507.993,493.703,485.632,479.527,471.584,472.226,468.206,463.099,461.038,458.980,456.354,458.615,459.162,462.963,465.558,468.448,475.207,480.323,488.962,527.992,579.613,606.594,611.218,617.023,635.927,651.079,676.647]}",
                "total_people":"2",
                "exposed_start":"08:30",
                "exposed_finish":"13:00",
                "infected_start":"08:30",
                "infected_finish":"13:00",
                "infected_people":"1",
                "room_volume":"60",
                "room_capacity": 10
            }

        In case of success (`200`), the response will contain the following structure:

            {
                "status": "success",
                "message": "Results generated successfully",
                "results": [
                    8.5,
                    10.167,
                    12.467,
                    13.0
                ]
            }

    For the full list of accepted inputs and respective values please refer to CAiMIRA's official defaults in GitLab repository [here](https://gitlab.cern.ch/caimira/caimira/-/blob/master/caimira/src/caimira/calculator/validators/defaults.py?ref_type=heads).

    ??? "**Example cURL** (with the above body)"
        
            curl -X POST "http://localhost:8081/co2/transition_times" \
            -H "Content-Type: application/json" \
            -d '{    
                "CO2_data": "{\"times\":[8.000,8.033,8.067,8.100,8.133,8.167,8.200,8.233,8.267,8.300,8.333,8.367,8.400,8.433,8.467,8.500,8.533,8.567,8.600,8.633,8.667,8.700,8.733,8.767,8.800,8.833,8.867,8.900,8.933,8.967,9.000,9.033,9.067,9.100,9.133,9.167,9.200,9.233,9.267,9.300,9.333,9.367,9.400,9.433,9.467,9.500,9.533,9.567,9.600,9.633,9.667,9.700,9.733,9.767,9.800,9.833,9.867,9.900,9.933,9.967,10.000,10.033,10.067,10.100,10.133,10.167,10.200,10.233,10.267,10.300,10.333,10.367,10.400,10.433,10.467,10.500,10.533,10.567,10.600,10.633,10.667,10.700,10.733,10.767,10.800,10.833,10.867,10.900,10.933,10.967,11.000,11.033,11.067,11.100,11.133,11.167,11.200,11.233,11.267,11.300,11.333,11.367,11.400,11.433,11.467,11.500,11.533,11.567,11.600,11.633,11.667,11.700,11.733,11.767,11.800,11.833,11.867,11.900,11.933,11.967,12.000,12.033,12.067,12.100,12.133,12.167,12.200,12.233,12.267,12.300,12.333,12.367,12.400,12.433,12.467,12.500,12.533,12.567,12.600,12.633,12.667,12.700,12.733,12.767,12.800,12.833,12.867,12.900,12.933,12.967,13.001],\"CO2\":[445.189,443.284,440.908,443.431,442.366,444.094,445.152,445.656,447.968,447.998,443.950,442.547,439.313,438.225,441.433,441.190,443.804,445.173,446.494,445.278,452.073,458.844,470.828,478.147,488.338,502.126,522.057,545.519,579.881,616.245,641.154,676.288,701.938,720.464,746.933,765.830,779.098,794.173,810.624,825.967,838.340,854.355,876.382,886.208,898.408,921.718,942.848,953.812,978.956,990.321,1002.931,1017.361,1029.379,1041.028,1051.883,1067.220,1073.530,1079.738,1093.733,1104.814,1125.798,1141.115,1151.046,1160.053,1176.367,1193.665,1180.104,1015.334,864.746,802.681,774.455,728.268,697.326,676.063,657.555,640.564,606.534,595.925,577.753,553.605,530.213,524.968,523.153,521.534,512.944,505.297,502.056,502.463,505.248,507.477,509.171,511.313,513.780,520.393,529.137,532.798,530.111,523.964,521.574,519.052,510.294,509.982,514.349,518.396,524.603,521.003,519.448,523.313,527.460,528.326,526.355,527.008,529.968,534.019,535.616,533.514,530.552,522.348,524.243,532.021,539.127,538.836,526.186,517.509,507.993,493.703,485.632,479.527,471.584,472.226,468.206,463.099,461.038,458.980,456.354,458.615,459.162,462.963,465.558,468.448,475.207,480.323,488.962,527.992,579.613,606.594,611.218,617.023,635.927,651.079,676.647]}",
                "total_people":"2",
                "exposed_start":"08:30",
                "exposed_finish":"13:00",
                "infected_start":"08:30",
                "infected_finish":"13:00",
                "infected_people":"1",
                "room_volume":"60",
                "room_capacity": 10,
            }'

??? Abstract "POST **/co2/report** (CO₂ report data generation)"
    
    * **Description**: Core endpoint that allows users to submit data for the CO₂ report generation. Data is processed by the CAiMIRA engine, and the results are returned in the response.
    * The input, response and error handling topics are similar to the previously described `virus/report` section.

    ??? note "Example body"

            {    
                "CO2_data": "{\"times\":[8.000,8.033,8.067,8.100,8.133,8.167,8.200,8.233,8.267,8.300,8.333,8.367,8.400,8.433,8.467,8.500,8.533,8.567,8.600,8.633,8.667,8.700,8.733,8.767,8.800,8.833,8.867,8.900,8.933,8.967,9.000,9.033,9.067,9.100,9.133,9.167,9.200,9.233,9.267,9.300,9.333,9.367,9.400,9.433,9.467,9.500,9.533,9.567,9.600,9.633,9.667,9.700,9.733,9.767,9.800,9.833,9.867,9.900,9.933,9.967,10.000,10.033,10.067,10.100,10.133,10.167,10.200,10.233,10.267,10.300,10.333,10.367,10.400,10.433,10.467,10.500,10.533,10.567,10.600,10.633,10.667,10.700,10.733,10.767,10.800,10.833,10.867,10.900,10.933,10.967,11.000,11.033,11.067,11.100,11.133,11.167,11.200,11.233,11.267,11.300,11.333,11.367,11.400,11.433,11.467,11.500,11.533,11.567,11.600,11.633,11.667,11.700,11.733,11.767,11.800,11.833,11.867,11.900,11.933,11.967,12.000,12.033,12.067,12.100,12.133,12.167,12.200,12.233,12.267,12.300,12.333,12.367,12.400,12.433,12.467,12.500,12.533,12.567,12.600,12.633,12.667,12.700,12.733,12.767,12.800,12.833,12.867,12.900,12.933,12.967,13.001],\"CO2\":[445.189,443.284,440.908,443.431,442.366,444.094,445.152,445.656,447.968,447.998,443.950,442.547,439.313,438.225,441.433,441.190,443.804,445.173,446.494,445.278,452.073,458.844,470.828,478.147,488.338,502.126,522.057,545.519,579.881,616.245,641.154,676.288,701.938,720.464,746.933,765.830,779.098,794.173,810.624,825.967,838.340,854.355,876.382,886.208,898.408,921.718,942.848,953.812,978.956,990.321,1002.931,1017.361,1029.379,1041.028,1051.883,1067.220,1073.530,1079.738,1093.733,1104.814,1125.798,1141.115,1151.046,1160.053,1176.367,1193.665,1180.104,1015.334,864.746,802.681,774.455,728.268,697.326,676.063,657.555,640.564,606.534,595.925,577.753,553.605,530.213,524.968,523.153,521.534,512.944,505.297,502.056,502.463,505.248,507.477,509.171,511.313,513.780,520.393,529.137,532.798,530.111,523.964,521.574,519.052,510.294,509.982,514.349,518.396,524.603,521.003,519.448,523.313,527.460,528.326,526.355,527.008,529.968,534.019,535.616,533.514,530.552,522.348,524.243,532.021,539.127,538.836,526.186,517.509,507.993,493.703,485.632,479.527,471.584,472.226,468.206,463.099,461.038,458.980,456.354,458.615,459.162,462.963,465.558,468.448,475.207,480.323,488.962,527.992,579.613,606.594,611.218,617.023,635.927,651.079,676.647]}",
                "total_people":"2",
                "exposed_start":"08:30",
                "exposed_finish":"13:00",
                "infected_start":"08:30",
                "infected_finish":"13:00",
                "infected_people":"1",
                "room_volume":"60",
                "room_capacity": 10,
                "fitting_ventilation_states":"[8.5,10.167,12.467,13.0]"
            }

        !!! note
            Given the same input values as in the previous example, note that the `fitting_ventilation_states` are those retrieved by the previous route.

    For the full list of accepted inputs and respective values please refer to CAiMIRA's official defaults in GitLab repository [here](https://gitlab.cern.ch/caimira/caimira/-/blob/master/caimira/src/caimira/calculator/validators/defaults.py?ref_type=heads).

    ??? "**Example cURL** (with the above body)"
        
            curl -X POST "http://localhost:8081/co2/report" \
            -H "Content-Type: application/json" \
            -d '{    
                "CO2_data": "{\"times\":[8.000,8.033,8.067,8.100,8.133,8.167,8.200,8.233,8.267,8.300,8.333,8.367,8.400,8.433,8.467,8.500,8.533,8.567,8.600,8.633,8.667,8.700,8.733,8.767,8.800,8.833,8.867,8.900,8.933,8.967,9.000,9.033,9.067,9.100,9.133,9.167,9.200,9.233,9.267,9.300,9.333,9.367,9.400,9.433,9.467,9.500,9.533,9.567,9.600,9.633,9.667,9.700,9.733,9.767,9.800,9.833,9.867,9.900,9.933,9.967,10.000,10.033,10.067,10.100,10.133,10.167,10.200,10.233,10.267,10.300,10.333,10.367,10.400,10.433,10.467,10.500,10.533,10.567,10.600,10.633,10.667,10.700,10.733,10.767,10.800,10.833,10.867,10.900,10.933,10.967,11.000,11.033,11.067,11.100,11.133,11.167,11.200,11.233,11.267,11.300,11.333,11.367,11.400,11.433,11.467,11.500,11.533,11.567,11.600,11.633,11.667,11.700,11.733,11.767,11.800,11.833,11.867,11.900,11.933,11.967,12.000,12.033,12.067,12.100,12.133,12.167,12.200,12.233,12.267,12.300,12.333,12.367,12.400,12.433,12.467,12.500,12.533,12.567,12.600,12.633,12.667,12.700,12.733,12.767,12.800,12.833,12.867,12.900,12.933,12.967,13.001],\"CO2\":[445.189,443.284,440.908,443.431,442.366,444.094,445.152,445.656,447.968,447.998,443.950,442.547,439.313,438.225,441.433,441.190,443.804,445.173,446.494,445.278,452.073,458.844,470.828,478.147,488.338,502.126,522.057,545.519,579.881,616.245,641.154,676.288,701.938,720.464,746.933,765.830,779.098,794.173,810.624,825.967,838.340,854.355,876.382,886.208,898.408,921.718,942.848,953.812,978.956,990.321,1002.931,1017.361,1029.379,1041.028,1051.883,1067.220,1073.530,1079.738,1093.733,1104.814,1125.798,1141.115,1151.046,1160.053,1176.367,1193.665,1180.104,1015.334,864.746,802.681,774.455,728.268,697.326,676.063,657.555,640.564,606.534,595.925,577.753,553.605,530.213,524.968,523.153,521.534,512.944,505.297,502.056,502.463,505.248,507.477,509.171,511.313,513.780,520.393,529.137,532.798,530.111,523.964,521.574,519.052,510.294,509.982,514.349,518.396,524.603,521.003,519.448,523.313,527.460,528.326,526.355,527.008,529.968,534.019,535.616,533.514,530.552,522.348,524.243,532.021,539.127,538.836,526.186,517.509,507.993,493.703,485.632,479.527,471.584,472.226,468.206,463.099,461.038,458.980,456.354,458.615,459.162,462.963,465.558,468.448,475.207,480.323,488.962,527.992,579.613,606.594,611.218,617.023,635.927,651.079,676.647]}",
                "total_people":"2",
                "exposed_start":"08:30",
                "exposed_finish":"13:00",
                "infected_start":"08:30",
                "infected_finish":"13:00",
                "infected_people":"1",
                "room_volume":"60",
                "room_capacity": 10,
                "fitting_ventilation_states":"[8.5,10.167,12.467,13.0]"
            }'

### Development

For testing new releases, use the PyPI Test instance by running the following command (directory independent):
    
    pip install --index-url https://test.pypi.org/simple --extra-index-url https://pypi.org/simple caimira
    
!!! info
    `--extra-index-url` is necessary to resolve dependencies from PyPI.
