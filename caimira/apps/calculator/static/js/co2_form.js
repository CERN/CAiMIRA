const CO2_data_form = [
  "CO2_data",
  "exposed_coffee_break_option",
  "exposed_coffee_duration",
  "exposed_finish",
  "exposed_lunch_finish",
  "exposed_lunch_option",
  "exposed_lunch_start",
  "exposed_start",
  "fitting_ventilation_states",
  "fitting_ventilation_type",
  "infected_coffee_break_option",
  "infected_coffee_duration",
  "infected_dont_have_breaks_with_exposed",
  "infected_finish",
  "infected_lunch_finish",
  "infected_lunch_option",
  "infected_lunch_start",
  "infected_people",
  "infected_start",
  "room_volume",
  "total_people",
  "ventilation_type",
];

// Method to upload a valid excel file
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
      .text("Please select a valid excel file (.XLS or .XLSX).")
      .show();
    return;
  }

  // FileReader API to read the Excel file
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
        cellValue.trim().toLowerCase() !== header.toLowerCase()
      ) {
        $("#upload-error")
          .text(`The file does not have the expected header "${header}".`)
          .show();
        return;
      }
    }

    const data = XLSX.utils.sheet_to_json(worksheet, { header: 1, raw: false });
    // Check if there is any data below the header row
    if (data.length <= 1) {
      $("#upload-error")
        .text(
          "The Excel file is empty. Please make sure it contains data below the header row."
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

    // Call function to convert Excel file to JSON and further processing
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
    $("[name=fitting_ventilation_type]").prop("disabled", false);
    plotCO2Data(endpoint);
  }
}

// Method to download Excel template available on CERNBox
function downloadTemplate(
  uri = "https://caimira-resources.web.cern.ch/CO2_template.xlsx",
  filename = "CO2_template.xlsx"
) {
  const link = document.createElement("a");
  link.download = filename;
  link.href = uri;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  delete link;
}

function insertErrorFor(referenceNode, text) {
  const element = $("<span></span>")
    .addClass("error_text text-danger")
    .html("&nbsp;&nbsp;" + text);
  $(referenceNode).before(element);
}

function validateFormInputs(obj) {
  $("span.error_text").remove();
  let submit = true;
  for (let i = 0; i < CO2_data_form.length; i++) {
    const element = $(`[name=${CO2_data_form[i]}]`).first();
    if (element.attr('name') !== "fitting_ventilation_states" && element.val() === "") {
      insertErrorFor(
        $("#DIVCO2_data_dialog"),
        `'${element.attr('name')}' must be defined.<br />`
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

  // Check if natural ventilation is selected
  if (
    $('input[name="fitting_ventilation_type"]:checked').first().val() ==
    "fitting_natural_ventilation"
  ) {
    // Validate ventilation scheme
    const element = $("[name=fitting_ventilation_states").first();
    if (element.val() !== "") {
      // validate input format
      try {
        const parsedValue = JSON.parse(element.val());
        if (Array.isArray(parsedValue)) {
          if (parsedValue.length <= 1) {
            insertErrorFor(
              $("#DIVCO2_fitting_result"),
              `'${element.attr('name')}' must have more than one element.<br />`
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
                $("#DIVCO2_fitting_result"),
                `The last transition time (${parsedValue[parsedValue.length - 1]}) should be before the last presence time (${max_presence_time / 60}).<br />`
              );
              submit = false;
            }
          }
        }
        else {
          insertErrorFor(
            $("#DIVCO2_fitting_result"),
            `'${element.attr('name')}' must be a list.</br>`
          );
          submit = false;
        }
      } catch {
        insertErrorFor(
          $("#DIVCO2_fitting_result"),
          `'${element.attr('name')}' must be a list of numbers.</br>`
        );
        submit = false;
      }
    } else {
      insertErrorFor(
        $("#DIVCO2_fitting_result"),
        `'${element.attr('name')}' must be defined.</br>`
      );
      submit = false;
    }
  }

  return submit;
}

function displayTransitionTimesHourFormat(start, stop) {
  var minutes_start = ((start % 1) * 60).toPrecision(2);
  var minutes_stop = ((stop % 1) * 60).toPrecision(2);
  return (
    Math.floor(start) +
    ":" +
    (minutes_start != "0.0" ? minutes_start : "00") +
    " - " +
    Math.floor(stop) +
    ":" +
    (minutes_stop != "0.0" ? minutes_stop : "00")
  );
}

function displayFittingData(json_response) {
  $("#DIVCO2_fitting_result").show();
  $("#CO2_data_plot").attr("src", json_response["CO2_plot"]);
  // Not needed for the form submission
  delete json_response["CO2_plot"];
  delete json_response["predictive_CO2"];
  $("#CO2_fitting_result").val(JSON.stringify(json_response));
  $("#exhalation_rate_fit").html(
    "Exhalation rate: " +
      String(json_response["exhalation_rate"].toFixed(2)) +
      " m³/h"
  );
  let ventilation_table =
    "<tr><th>Time (HH:MM)</th><th>ACH value (h⁻¹)</th></tr>";
  json_response["ventilation_values"].forEach((val, index) => {
    let transition_times = displayTransitionTimesHourFormat(
      json_response["transition_times"][index],
      json_response["transition_times"][index + 1]
    );
    ventilation_table += `<tr><td>${transition_times}</td><td>${val.toPrecision(
      2
    )}</td></tr>`;
  });
  $("#disable_fitting_algorithm").prop("disabled", false);
  $("#ventilation_rate_fit").html(ventilation_table);
  $("#generate_fitting_data").html("Fit data");
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
    }).then((response) =>
      response
        .json()
        .then((json_response) => {
          $("#CO2_data_plot").attr("src", json_response["CO2_plot"])
          $("#fitting_ventilation_states").val(`[${json_response["transition_times"]}]`)
        })
        .then($("#DIVCO2_fitting_to_submit").show())
        .catch((error) => console.log(error))
    );
  }
}

function submitFittingAlgorithm(url) {
  if (validateCO2Form()) {
    // Disable all the ventilation inputs
    $("#fitting_ventilation_states, [name=fitting_ventilation_type]").prop(
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
  // Add the warning suggestion line
  $("#suggestion_lines_txt").show();
  // Remove all the previously generated fitting elements
  $("#generate_fitting_data").prop("disabled", true);
  $("#CO2_fitting_result").val("");
  $("#CO2_data").val("{}");
  $("#fitting_ventilation_states").val("");
  $("span.error_text").remove();
  $("#DIVCO2_fitting_result, #CO2_input_data_div").hide();
  $("#DIVCO2_fitting_to_submit").hide();
  $("#CO2_data_plot").attr("src", "");

  // Update the ventilation scheme components
  $("#fitting_ventilation_states, [name=fitting_ventilation_type]").prop(
    "disabled",
    false
  );

  // Update the bottom right buttons
  $("#generate_fitting_data").show();
  $("#save_and_dismiss_dialog").hide();
}

function disableFittingAlgorithm() {
  clearFittingResultComponent();
  $("#CO2_data_no").click();
}
