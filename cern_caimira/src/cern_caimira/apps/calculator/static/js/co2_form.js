// Input data for CO2 fitting algorithm 
const CO2_data_form = [
  "CO2_data",
  "dynamic_exposed_occupancy",
  "dynamic_infected_occupancy",
  "exposed_coffee_break_option",
  "exposed_coffee_duration",
  "exposed_finish",
  "exposed_lunch_finish",
  "exposed_lunch_option",
  "exposed_lunch_start",
  "exposed_start",
  "fitting_ventilation_states",
  "infected_coffee_break_option",
  "infected_coffee_duration",
  "infected_dont_have_breaks_with_exposed",
  "infected_finish",
  "infected_lunch_finish",
  "infected_lunch_option",
  "infected_lunch_start",
  "infected_people",
  "infected_start",
  "occupancy_format",
  "room_capacity",
  "room_volume",
  "specific_breaks",
  "total_people"
];

// Method to upload a valid data file (accepted formats: .xls and .xlsx)
function uploadFile(endpoint) {
  clearFittingResultComponent();
  const files = $("#file_upload")[0].files;
  if (files.length === 0) {
    $("#upload-error")
      .text('Please choose a file.')
      .show();
    return;
  }
  const file = files[0];
  const extension = file.name
    .substring(file.name.lastIndexOf("."))
    .toUpperCase();
  if (extension !== ".XLS" && extension !== ".XLSX") {
    $("#upload-error")
      .text("Please select a valid data file (.XLS or .XLSX).")
      .show();
    return;
  }

  // FileReader API to read the data file
  const reader = new FileReader();
  reader.onload = function (event) {
    const fileContent = event.target.result;
    const workbook = XLSX.read(fileContent, { type: "binary" });

    // Assuming the first sheet is the one we want to validate
    const firstSheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[firstSheetName];

    // Check if the headers match the expected format
    const headerCoordinates = {
      Times: "A1",
      CO2: "B1",
    };
    for (const header in headerCoordinates) {
      const cellValue = worksheet[headerCoordinates[header]]?.v;
      if (
        !cellValue ||
        $.type(cellValue) !== "string" ||
        cellValue.trim().toLowerCase() !== header.toLowerCase()
      ) {
        $("#upload-error")
          .text(`The file does not have the expected header "${header}".`)
          .show();
        return;
      }
    }

    const data = XLSX.utils.sheet_to_json(worksheet, { header: 1, raw: true });
    // Check if there is any data below the header row
    if (data.length <= 1) {
      $("#upload-error")
        .text(
          "The data file is empty. Please make sure it contains data below the header row."
        )
        .show();
      return;
    }

    // Validate data in the columns
    const timesColumnIndex = 0;
    const CO2ColumnIndex = 1;
    for (let i = 1; i < data.length; i++) {
      try {
        const timesCellValue = parseFloat(data[i][timesColumnIndex]);
        const CO2CellValue = parseFloat(data[i][CO2ColumnIndex]);

        if (isNaN(timesCellValue) || isNaN(CO2CellValue)) {
          throw new Error("Invalid data in the Times or CO2 columns.");
        }
      } catch (error) {
        $("#upload-error")
          .text(
            "Invalid data in the Times or CO2 columns. Please make sure they contain only float values."
          )
          .show();
        return;
      }
    }

    // Validate times data encompass simulation time
    const firstTimeInData = parseFloat((data[1][timesColumnIndex] * 60).toFixed(2))
    const lastTimeInData = parseFloat((data[data.length - 1][timesColumnIndex] * 60).toFixed(2))
    // Validate start time
    const infected_start = $(`[name=infected_start]`).first().val();
    const exposed_start = $(`[name=exposed_start]`).first().val();

    let [hours_infected, minutes_infected] = infected_start.split(":").map(Number);
    let elapsed_time_infected =  hours_infected * 60 + minutes_infected;

    let [hours_exposed, minutes_exposed] = exposed_start.split(":").map(Number);
    let elapsed_time_exposed =  hours_exposed * 60 + minutes_exposed;
    
    const min_presence_time = parseFloat((Math.min(elapsed_time_infected, elapsed_time_exposed)).toFixed(2));
    
    // Validate finish time
    const infected_finish = $(`[name=infected_finish]`).first().val();
    const exposed_finish = $(`[name=exposed_finish]`).first().val();

    [hours_infected, minutes_infected] = infected_finish.split(":").map(Number);
    elapsed_time_infected =  hours_infected * 60 + minutes_infected;

    [hours_exposed, minutes_exposed] = exposed_finish.split(":").map(Number);
    elapsed_time_exposed =  hours_exposed * 60 + minutes_exposed;
    
    const max_presence_time = parseFloat((Math.max(elapsed_time_infected, elapsed_time_exposed)).toFixed(2));
    if (firstTimeInData > min_presence_time || lastTimeInData < max_presence_time) {
      $("#upload-error")
        .text(`The times of the data file should encompass the entire simulation time (from ${min_presence_time/60} to ${max_presence_time/60}). 
        Got times from ${firstTimeInData/60} to ${lastTimeInData/60}. Either adapt the simulation presence times, or the times of the data file.`).show();
      return;
    }
    
    // Convert data file to JSON and further processing
    try {
      generateJSONStructure(endpoint, data);
      // If all validations pass, process the file here or display a success message
      $("#upload-file-extention-error").hide();
    } catch (error) {
      console.log(error);
    }
  };
  reader.readAsBinaryString(file); // Read the file as a binary string
}

// Method to generate the JSON structure
function generateJSONStructure(endpoint, jsonData) {
  const inputToPopulate = $("#CO2_data");

  // Initialize the final structure
  const finalStructure = { times: [], CO2: [] };

  if (jsonData.length > 0) {
    // Loop through the input dataArray and extract the values starting from the second array (index 1)
    for (let i = 1; i < jsonData.length; i++) {
      const arr = jsonData[i];
      // Assuming arr contains two float values
      finalStructure.times.push(parseFloat(arr[0]));
      finalStructure.CO2.push(parseFloat(arr[1]));
    }
    inputToPopulate.val(JSON.stringify(finalStructure));
    $("#generate_fitting_data").prop("disabled", false);
    $("#fitting_ventilation_states").prop("disabled", false);
    $("#room_capacity").prop("disabled", false);
    plotCO2Data(endpoint);
  }
}

function insertErrorFor(referenceNode, text) {
  $(`<span class='error_text text-danger'>${text}</span>`).insertAfter(referenceNode)
}

function validateFormInputs(obj) {
  $("#ventilation_data").find("span.error_text").remove(); // Remove all error spans
  
  let submit = true;
  const $referenceNode = $("#DIVCO2_data_dialog");
  for (let i = 0; i < CO2_data_form.length; i++) {
    const $requiredElement = $(`[name=${CO2_data_form[i]}]`).first();
    if ($requiredElement.attr('name') !== "fitting_ventilation_states" &&
        $requiredElement.attr('name') !== "room_capacity" &&
        $requiredElement.val() === "") {
      insertErrorFor(
        $referenceNode,
        `'${$requiredElement.attr('name')}' must be defined.<br />`
      );
      submit = false;
    }
  }
  if (submit) {
    $($(obj).data("target")).modal("show");
    $("#upload-error").hide();
    $("#upload-file-extention-error").hide();
  }
  return submit;
}

function validateCO2Form() {
  let submit = true;
  if (validateFormInputs($("#button_fit_data"))) submit = true;

  const $fittingToSubmit = $('#DIVCO2_fitting_to_submit');
  // Validate ventilation scheme
  const $ventilationStates = $fittingToSubmit.find("input[name=fitting_ventilation_states]");
  const $referenceNode = $("#DIVCO2_fitting_result");
  if ($ventilationStates.val() !== "") {
    // validate input format
    try {
      const parsedValue = JSON.parse($ventilationStates.val());
      if (Array.isArray(parsedValue)) {
        if (parsedValue.length <= 1) {
          insertErrorFor(
            $referenceNode,
            `'${$ventilationStates.attr('name')}' must have more than one ventilation transition time (at least the beginning and end of simulation time).<br />`
          );
          submit = false;
        }
        else {
          const infected_finish = $(`[name=infected_finish]`).first().val();
          const exposed_finish = $(`[name=exposed_finish]`).first().val();

          const [hours_infected, minutes_infected] = infected_finish.split(":").map(Number);
          const elapsed_time_infected =  hours_infected * 60 + minutes_infected;

          const [hours_exposed, minutes_exposed] = exposed_finish.split(":").map(Number);
          const elapsed_time_exposed =  hours_exposed * 60 + minutes_exposed;
          
          const max_presence_time = Math.max(elapsed_time_infected, elapsed_time_exposed);
          const max_transition_time = parsedValue[parsedValue.length - 1] * 60;

          if (max_transition_time > max_presence_time) {
            insertErrorFor(
              $referenceNode,
              `The last transition time (${parsedValue[parsedValue.length - 1]}) should be before the last presence time (${max_presence_time / 60}).<br />`
            );
            submit = false;
          }
        }
      }
      else {
        insertErrorFor(
          $referenceNode,
          `'${$ventilationStates.attr('name')}' must be a list.</br>`
        );
        submit = false;
      }
    } catch {
      insertErrorFor(
        $referenceNode,
        `'${$ventilationStates.attr('name')}' must be a list of numbers.</br>`
      );
      submit = false;
    }
    // Validate room capacity
    const roomCapacity = $fittingToSubmit.find("input[name=room_capacity]");
    const roomCapacityVal = roomCapacity.val();
    if (roomCapacityVal !== "") {
      const roomCapacityNumber = Number(roomCapacityVal);
      if (!Number.isInteger(roomCapacityNumber) || roomCapacityNumber <= 0) {
        insertErrorFor(
          $referenceNode,
          `'${roomCapacity.attr('name')}' must be a valid integer (> 0).</br>`
        );
        submit = false;
      }
    }
  } else {
    insertErrorFor(
      $referenceNode,
      `'${$ventilationStates.attr('name')}' must be defined.</br>`
    );
    submit = false;
  }
  return submit;
}

function displayTransitionTimesHourFormat(start, stop) {
  const formatTime = (time) => {
    const hours = Math.floor(time);
    const minutes = Math.round((time % 1) * 60);
    return `${hours}:${minutes.toString().padStart(2, '0')}`;
  };

  return `${formatTime(start)} - ${formatTime(stop)}`;
}

function displayFittingData(json_response) {
  $("#DIVCO2_fitting_result").show();
  $("#CO2_data_plot").attr("src", json_response["CO2_plot_img"]);
  // Not needed for the form submission
  delete json_response["CO2_plot_img"];
  delete json_response["predictive_CO2"];
  delete json_response["CO2_plot_data"];
  // Convert nulls to empty strings in the JSON response
  if (json_response["room_capacity"] === null) json_response["room_capacity"] = '';
  if (json_response["ventilation_lsp_values"] === null) json_response["ventilation_lsp_values"] = '';
  // Populate the hidden input
  $("#CO2_fitting_result").val(JSON.stringify(json_response));
  $("#exhalation_rate_fit").html(
    "Exhalation rate: " +
      String(json_response["exhalation_rate"].toFixed(2)) +
      " m³/h"
  );
  let ventilation_table = `<tr>
                            <th>Time (HH:MM)</th>
                            <th>ACH value (h⁻¹)</th>
                            <th>Flow rate (L/s)</th>`;
    // Check if ventilation_lsp_values is not empty
    let hasLspValues = json_response['ventilation_lsp_values'] !== '';
    if (hasLspValues) {
      ventilation_table += `<th>Flow rate (L/s/person)</th>`;
    }
    ventilation_table += `</tr>`;
    json_response["ventilation_values"].forEach((CO2_val, index) => {
    let transition_times = displayTransitionTimesHourFormat(
      json_response["transition_times"][index],
      json_response["transition_times"][index + 1]
    );

    ventilation_table += `<tr>
                            <td>${transition_times}</td>
                            <td>${CO2_val.toPrecision(2)}</td>
                            <td>${json_response['ventilation_ls_values'][index].toPrecision(2)}</td>`;
    // Add the L/s/person value if available
    if (hasLspValues) {
      ventilation_table += `<td>${json_response['ventilation_lsp_values'][index].toPrecision(2)}</td>`;
    }
    ventilation_table += `</tr>`;
  });

  $("#disable_fitting_algorithm").prop("disabled", false);
  $("#ventilation_rate_fit").html(ventilation_table);
  $("#generate_fitting_data").html("Confirm and Fit data");
  $("#generate_fitting_data").hide();
  $("#save_and_dismiss_dialog").show();
}

function formatCO2DataForm(CO2_data_form) {
  let CO2_mapping = {};
  CO2_data_form.map((el) => {
    let element = $(`[name=${el}]`).first();

    // Validate checkboxes
    if (element.prop('type') == "checkbox") {
      CO2_mapping[element.attr('name')] = String(+element.prop('checked'));
    }
    // Validate radio buttons
    else if (element.prop('type') == "radio")
      CO2_mapping[element.attr('name')] = $(
        `[name=${element.attr('name')}]:checked`
      ).first().val();
    else {
      CO2_mapping[element.attr('name')] = element.val();
    }
  });
  return CO2_mapping;
}

function plotCO2Data(url) {
  if (validateFormInputs()) {
    let CO2_mapping = formatCO2DataForm(CO2_data_form);
    fetch(url, {
      method: "POST",
      body: JSON.stringify(CO2_mapping),
      headers: {
        "Content-Type": "application/json",
        "X-XSRFToken": document.getElementsByName('_xsrf')[0].value
      },
      credentials: "include",
    }).then((response) =>
      response
        .json()
        .then((json_response) => {
          $("#CO2_data_plot").attr("src", json_response["CO2_plot_img"])
          $("#fitting_ventilation_states").val(`[${json_response["transition_times"]}]`)
        })
        .then($("#DIVCO2_fitting_to_submit").show())
        .catch((error) => console.log(error))
    );
  }
}

function submitFittingAlgorithm(url) {
  if (validateCO2Form()) {
    // Disable room capacity input
    $("#room_capacity").prop(
      "disabled",
      true
    );
    // Prepare data for submission
    const CO2_mapping = formatCO2DataForm(CO2_data_form);
    $("#CO2_input_data_div").show();
    $("#disable_fitting_algorithm").prop("disabled", true);
    $("#generate_fitting_data")
      .html(
        '<span id="loading_spinner" class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Loading...'
      )
      .prop("disabled", true);
    $("#CO2_input_data").html(JSON.stringify(CO2_mapping, null, "\t"));

    fetch(url, {
      method: "POST",
      body: JSON.stringify(CO2_mapping),
      headers: {
        "Content-Type": "application/json",
        "X-XSRFToken": document.getElementsByName('_xsrf')[0].value
      },
      credentials: "include",
    })
      .then((response) => response.json())
      .then((json_response) => {
        displayFittingData(json_response);
        // Hide the suggestion transition lines warning
        $("#suggestion_lines_txt").hide();
      });
  }
}

function clearFittingResultComponent() {
  const $referenceNode = $("#DIVCO2_data_dialog");
  // Add the warning suggestion line
  $referenceNode.find("#suggestion_lines_txt").show();
  // Remove all the previously generated fitting elements
  $referenceNode.find("#generate_fitting_data").prop("disabled", true);
  $referenceNode.find("#CO2_fitting_result").val("");
  $referenceNode.find("#CO2_data").val("{}");
  $referenceNode.find("#fitting_ventilation_states").val("");
  $referenceNode.find("span.error_text").remove();
  $referenceNode.find("#DIVCO2_fitting_result, #CO2_input_data_div").hide();
  $referenceNode.find("#DIVCO2_fitting_to_submit").hide();
  $referenceNode.find("#CO2_data_plot").attr("src", "");

  // Update the bottom right buttons
  $referenceNode.find("#generate_fitting_data").show();
  $referenceNode.find("#save_and_dismiss_dialog").hide();
}

function disableFittingAlgorithm() {
  clearFittingResultComponent();
  $("#CO2_data_no").click();
}
