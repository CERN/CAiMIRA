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

1. Install dependencies:
    ```
    cd caimira
    pip install -e .
    ```
    
2. Run the backend:
    ```
    python -m caimira.api.app
    ```
    The web server will be accessible on port `8081`.
    
#### API Endpoints

As the project is growing, more endpoints targeted to specific tasks will be developed.

??? "POST **/virus_report** (virus report data generation)"

    * **Description**: Core endpoint that allows users to submit data for the virus report generation. Data is processed by the CAiMIRA engine, and the results are returned in the response.
    * **Input**: The body of the request must include the necessary input data in JSON format. Examples of the required input can be found [here](https://gitlab.cern.ch/caimira/caimira/-/blob/master/caimira/src/caimira/calculator/validators/defaults.py?ref_type=heads).
    * **Response**: On success (status code `200`), the response will contain the following structure:

            {
                "status": "success",
                "message": "Results generated successfully",
                "report_data": {
                ...
                }
            }
            
    * **Error Handling**: In case of errors, the API will return appropriate error messages and HTTP status codes, such as `400` for bad requests, `404` for not found, or `500` for internal server errors.

    **Example body**:
    
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
        
            curl -X POST "http://localhost:8081/virus_report" \
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

??? "POST **/co2_report** (CO2 report data generation)"
    
    * **Description**: Core endpoint that allows users to submit data for the CO2 report generation. Data is processed by the CAiMIRA engine, and the results are returned in the response.
    * The input, response and error handling topics are similar to the previously described `virus_report` section.

    **Example body:**

        {    
            "CO2_data": "{\"times\":[8,8,8.1,8.1,8.1,8.2,8.2,8.2,8.3,8.3,8.3,8.4,8.4,8.4,8.5,8.5,8.5,8.6,8.6,8.6,8.7,8.7,8.7,8.8,8.8,8.8,8.9,8.9,8.9,9,9,9,9.1,9.1,9.1,9.2,9.2,9.2,9.3,9.3,9.3,9.4,9.4,9.4,9.5,9.5,9.5,9.6,9.6,9.6,9.7,9.7,9.7,9.8,9.8,9.8,9.9,9.9,9.9,10,10,10,10.1,10.1,10.1,10.2,10.2,10.2,10.3,10.3,10.3,10.4,10.4,10.4,10.5,10.5,10.5,10.6,10.6,10.6,10.7,10.7,10.7,10.8,10.8,10.8,10.9,10.9,10.9,11,11,11,11.1,11.1,11.1,11.2,11.2,11.2,11.3,11.3,11.3,11.4,11.4,11.4,11.5,11.5,11.5,11.6,11.6,11.6,11.7,11.7,11.7,11.8,11.8,11.8,11.9,11.9,11.9,12,12,12,12.1,12.1,12.1,12.2,12.2,12.2,12.3,12.3,12.3,12.4,12.4,12.4,12.5,12.5,12.5,12.6,12.6,12.6,12.7,12.7,12.7,12.8,12.8,12.8,12.9,12.9,12.9,13,13,13,13.1,13.1,13.1,13.2,13.2,13.2,13.3,13.3,13.3,13.4,13.4,13.4,13.5,13.5,13.5,13.6,13.6,13.6,13.7,13.7,13.7,13.8,13.8,13.8,13.9,13.9,13.9,14,14,14,14.1,14.1,14.1,14.2,14.2,14.2,14.3,14.3,14.3,14.4,14.4,14.4,14.5,14.5,14.5,14.6,14.6,14.6,14.7,14.7,14.7,14.8,14.8,14.8,14.9,14.9,14.9,15,15,15,15.1,15.1,15.1,15.2,15.2,15.2,15.3,15.3,15.3,15.4,15.4,15.4,15.5,15.5,15.5,15.6,15.6,15.6,15.7,15.7,15.7,15.8,15.8,15.8,15.9,15.9,15.9,16,16,16,16.1,16.1,16.1,16.2,16.2,16.2,16.3,16.3,16.3,16.4,16.4,16.4,16.5,16.5,16.5,16.6,16.6,16.6,16.7,16.7,16.7,16.8,16.8,16.8,16.9,16.9,16.9,17,17,17,17.1,17.1,17.1,17.2,17.2,17.2,17.3,17.3,17.3,17.4,17.4,17.4,17.5,17.5,17.5,17.6,17.6,17.6,17.7,17.7,17.7,17.8,17.8,17.8,17.9,17.9,17.9,18,18,18,18.1,18.1,18.1,18.2,18.2,18.2,18.3,18.3,18.3,18.4,18.4,18.4,18.5,18.5,18.5,18.6,18.6,18.6,18.7,18.7,18.7,18.8,18.8,18.8,18.9,18.9,18.9,19,19,19,19.1,19.1,19.1,19.2,19.2,19.2,19.3,19.3,19.3,19.4,19.4,19.4,19.5,19.5,19.5,19.6,19.6,19.6,19.7,19.7,19.7,19.8,19.8,19.8,19.9,19.9,19.9,20],\"CO2\":[445.2,443.3,440.9,443.4,442.4,444.1,445.2,445.7,448,448,444,442.5,439.3,438.2,441.4,441.2,443.8,445.2,446.5,445.3,452.1,458.8,470.8,478.1,488.3,502.1,522.1,545.5,579.9,616.2,641.2,676.3,701.9,720.5,746.9,765.8,779.1,794.2,810.6,826,838.3,854.4,876.4,886.2,898.4,921.7,942.8,953.8,979,990.3,1002.9,1017.4,1029.4,1041,1051.9,1067.2,1073.5,1079.7,1093.7,1104.8,1125.8,1141.1,1151,1160.1,1176.4,1193.7,1180.1,1015.3,864.7,802.7,774.5,728.3,697.3,676.1,657.6,640.6,606.5,595.9,577.8,553.6,530.2,525,523.2,521.5,512.9,505.3,502.1,502.5,505.2,507.5,509.2,511.3,513.8,520.4,529.1,532.8,530.1,524,521.6,519.1,510.3,510,514.3,518.4,524.6,521,519.4,523.3,527.5,528.3,526.4,527,530,534,535.6,533.5,530.6,522.3,524.2,532,539.1,538.8,526.2,517.5,508,493.7,485.6,479.5,471.6,472.2,468.2,463.1,461,459,456.4,458.6,459.2,463,465.6,468.4,475.2,480.3,489,528,579.6,606.6,611.2,617,635.9,651.1,676.6,696.6,714.6,729.9,744.7,766,788.5,812.1,832.8,854.7,883.9,895.6,910,924.4,944.5,956.8,971.4,981.3,993.6,1004.4,1021.6,1035.2,1043.8,1063.7,1071,1065.6,1065.9,1073.7,1086.4,1093.5,1120.1,1189.3,1202.9,1218.6,1238.5,1250.1,1263.5,1265,1270.1,1281.6,1294.9,1304.2,1315.5,1338.4,1351.5,1353.4,1364,1361.7,1343.3,1329.7,1320.4,1310.5,1313.6,1305.5,1313.4,1307.5,1290,1286.9,1289.3,1276.8,1268.9,1266.1,1264,1271.8,1268.5,1244.5,1206.4,1173.6,1145,1157.2,1194.4,1198.3,1196.1,1182.5,1167.9,1150.4,1132.8,1108.1,1097.4,1099.8,1093.4,1086.8,1086.9,1083.8,1075.5,1059.9,1048.4,1047.4,1042.6,1036.1,1026.9,1022.7,1017.6,1023.5,1021,1017.3,1004.6,908.3,906.5,979.2,955.8,928.9,915.3,914.1,930.1,923.3,921,865.9,860.2,867,869.7,871.4,861.5,862.9,850.4,843.9,839.7,838.1,839.8,849.7,841.6,820.8,825,838.5,853.8,855.6,838.7,818.1,811.7,804.3,794.5,790.6,782,788.6,779.6,804.2,836.9,852.4,856.9,858.1,857.9,856.5,856.7,851.7,849.6,849.2,846,846.8,844.8,842,839,836,833.2,832.6,830.9,825.9,823.6,823.7,818.2,812.4,810.2,808.4,806.7,803,800.2,794.3,790.5,790.4,787.7,783.3,780.5,784,780.9,780.8,777.2,775,768.7,763.6,761.5,757.8,760,762.1,761.6,761.2,761.5,757.5,754.5,752.6,752.1,751.7,748.6,744.3,742.1,737.6,731,732.6,726.8,726.2,726.9,727.1,726.8,728.9,729.9,726.5,724.8,723.9,723,721.1,720.2,721.1]}",
            "exposed_lunch_finish": "13:30",
            "exposed_lunch_start": "12:30",
            "exposed_start": "08:30",
            "fitting_ventilation_states": "[8.5, 17.5]",
            "infected_finish": "17:30",
            "infected_lunch_finish": "13:30",
            "infected_lunch_start": "12:30",
            "infected_people": "1",
            "infected_start": "08:30",
            "room_capacity": "10",
            "room_volume": "60",
            "total_people": "2"
        }

    For the full list of accepted inputs and respective values please refer to CAiMIRA's official defaults in GitLab repository [here](https://gitlab.cern.ch/caimira/caimira/-/blob/master/caimira/src/caimira/calculator/validators/defaults.py?ref_type=heads).

    ??? "**Example cURL** (with the above body)"
        
            curl -X POST "http://localhost:8081/co2_report" \
            -H "Content-Type: application/json" \
            -d '{    
                "CO2_data": "{\"times\":[8,8,8.1,8.1,8.1,8.2,8.2,8.2,8.3,8.3,8.3,8.4,8.4,8.4,8.5,8.5,8.5,8.6,8.6,8.6,8.7,8.7,8.7,8.8,8.8,8.8,8.9,8.9,8.9,9,9,9,9.1,9.1,9.1,9.2,9.2,9.2,9.3,9.3,9.3,9.4,9.4,9.4,9.5,9.5,9.5,9.6,9.6,9.6,9.7,9.7,9.7,9.8,9.8,9.8,9.9,9.9,9.9,10,10,10,10.1,10.1,10.1,10.2,10.2,10.2,10.3,10.3,10.3,10.4,10.4,10.4,10.5,10.5,10.5,10.6,10.6,10.6,10.7,10.7,10.7,10.8,10.8,10.8,10.9,10.9,10.9,11,11,11,11.1,11.1,11.1,11.2,11.2,11.2,11.3,11.3,11.3,11.4,11.4,11.4,11.5,11.5,11.5,11.6,11.6,11.6,11.7,11.7,11.7,11.8,11.8,11.8,11.9,11.9,11.9,12,12,12,12.1,12.1,12.1,12.2,12.2,12.2,12.3,12.3,12.3,12.4,12.4,12.4,12.5,12.5,12.5,12.6,12.6,12.6,12.7,12.7,12.7,12.8,12.8,12.8,12.9,12.9,12.9,13,13,13,13.1,13.1,13.1,13.2,13.2,13.2,13.3,13.3,13.3,13.4,13.4,13.4,13.5,13.5,13.5,13.6,13.6,13.6,13.7,13.7,13.7,13.8,13.8,13.8,13.9,13.9,13.9,14,14,14,14.1,14.1,14.1,14.2,14.2,14.2,14.3,14.3,14.3,14.4,14.4,14.4,14.5,14.5,14.5,14.6,14.6,14.6,14.7,14.7,14.7,14.8,14.8,14.8,14.9,14.9,14.9,15,15,15,15.1,15.1,15.1,15.2,15.2,15.2,15.3,15.3,15.3,15.4,15.4,15.4,15.5,15.5,15.5,15.6,15.6,15.6,15.7,15.7,15.7,15.8,15.8,15.8,15.9,15.9,15.9,16,16,16,16.1,16.1,16.1,16.2,16.2,16.2,16.3,16.3,16.3,16.4,16.4,16.4,16.5,16.5,16.5,16.6,16.6,16.6,16.7,16.7,16.7,16.8,16.8,16.8,16.9,16.9,16.9,17,17,17,17.1,17.1,17.1,17.2,17.2,17.2,17.3,17.3,17.3,17.4,17.4,17.4,17.5,17.5,17.5,17.6,17.6,17.6,17.7,17.7,17.7,17.8,17.8,17.8,17.9,17.9,17.9,18,18,18,18.1,18.1,18.1,18.2,18.2,18.2,18.3,18.3,18.3,18.4,18.4,18.4,18.5,18.5,18.5,18.6,18.6,18.6,18.7,18.7,18.7,18.8,18.8,18.8,18.9,18.9,18.9,19,19,19,19.1,19.1,19.1,19.2,19.2,19.2,19.3,19.3,19.3,19.4,19.4,19.4,19.5,19.5,19.5,19.6,19.6,19.6,19.7,19.7,19.7,19.8,19.8,19.8,19.9,19.9,19.9,20],\"CO2\":[445.2,443.3,440.9,443.4,442.4,444.1,445.2,445.7,448,448,444,442.5,439.3,438.2,441.4,441.2,443.8,445.2,446.5,445.3,452.1,458.8,470.8,478.1,488.3,502.1,522.1,545.5,579.9,616.2,641.2,676.3,701.9,720.5,746.9,765.8,779.1,794.2,810.6,826,838.3,854.4,876.4,886.2,898.4,921.7,942.8,953.8,979,990.3,1002.9,1017.4,1029.4,1041,1051.9,1067.2,1073.5,1079.7,1093.7,1104.8,1125.8,1141.1,1151,1160.1,1176.4,1193.7,1180.1,1015.3,864.7,802.7,774.5,728.3,697.3,676.1,657.6,640.6,606.5,595.9,577.8,553.6,530.2,525,523.2,521.5,512.9,505.3,502.1,502.5,505.2,507.5,509.2,511.3,513.8,520.4,529.1,532.8,530.1,524,521.6,519.1,510.3,510,514.3,518.4,524.6,521,519.4,523.3,527.5,528.3,526.4,527,530,534,535.6,533.5,530.6,522.3,524.2,532,539.1,538.8,526.2,517.5,508,493.7,485.6,479.5,471.6,472.2,468.2,463.1,461,459,456.4,458.6,459.2,463,465.6,468.4,475.2,480.3,489,528,579.6,606.6,611.2,617,635.9,651.1,676.6,696.6,714.6,729.9,744.7,766,788.5,812.1,832.8,854.7,883.9,895.6,910,924.4,944.5,956.8,971.4,981.3,993.6,1004.4,1021.6,1035.2,1043.8,1063.7,1071,1065.6,1065.9,1073.7,1086.4,1093.5,1120.1,1189.3,1202.9,1218.6,1238.5,1250.1,1263.5,1265,1270.1,1281.6,1294.9,1304.2,1315.5,1338.4,1351.5,1353.4,1364,1361.7,1343.3,1329.7,1320.4,1310.5,1313.6,1305.5,1313.4,1307.5,1290,1286.9,1289.3,1276.8,1268.9,1266.1,1264,1271.8,1268.5,1244.5,1206.4,1173.6,1145,1157.2,1194.4,1198.3,1196.1,1182.5,1167.9,1150.4,1132.8,1108.1,1097.4,1099.8,1093.4,1086.8,1086.9,1083.8,1075.5,1059.9,1048.4,1047.4,1042.6,1036.1,1026.9,1022.7,1017.6,1023.5,1021,1017.3,1004.6,908.3,906.5,979.2,955.8,928.9,915.3,914.1,930.1,923.3,921,865.9,860.2,867,869.7,871.4,861.5,862.9,850.4,843.9,839.7,838.1,839.8,849.7,841.6,820.8,825,838.5,853.8,855.6,838.7,818.1,811.7,804.3,794.5,790.6,782,788.6,779.6,804.2,836.9,852.4,856.9,858.1,857.9,856.5,856.7,851.7,849.6,849.2,846,846.8,844.8,842,839,836,833.2,832.6,830.9,825.9,823.6,823.7,818.2,812.4,810.2,808.4,806.7,803,800.2,794.3,790.5,790.4,787.7,783.3,780.5,784,780.9,780.8,777.2,775,768.7,763.6,761.5,757.8,760,762.1,761.6,761.2,761.5,757.5,754.5,752.6,752.1,751.7,748.6,744.3,742.1,737.6,731,732.6,726.8,726.2,726.9,727.1,726.8,728.9,729.9,726.5,724.8,723.9,723,721.1,720.2,721.1]}",
                "exposed_lunch_finish": "13:30",
                "exposed_lunch_start": "12:30",
                "exposed_start": "08:30",
                "fitting_ventilation_states": "[8.5, 17.5]",
                "infected_finish": "17:30",
                "infected_lunch_finish": "13:30",
                "infected_lunch_start": "12:30",
                "infected_people": "1",
                "infected_start": "08:30",
                "room_capacity": "10",
                "room_volume": "60",
                "total_people": "2"
            }'