const CO2_data_form = [
	'CO2_data',
	'exposed_coffee_break_option',
	'exposed_coffee_duration',
	'exposed_finish',
	'exposed_lunch_finish',
	'exposed_lunch_option',
	'exposed_lunch_start',
	'exposed_start',
	'fitting_ventilation_states',
	'fitting_ventilation_type',
	'infected_coffee_break_option',
	'infected_coffee_duration',
	'infected_dont_have_breaks_with_exposed',
	'infected_finish',
	'infected_lunch_finish',
	'infected_lunch_option',
	'infected_lunch_start',
	'infected_people',
	'infected_start',
	'room_volume',
	'total_people',
	'ventilation_type',
  ];
  
  // Method to upload a valid excel file
  function uploadFile(endpoint) {
	clearFittingResultComponent();
	const files = document.getElementById("file_upload").files;
	if (files.length === 0) {
	  alert("Please choose any file...");
	  return;
	}
	const file = files[0];
	const extension = file.name.substring(file.name.lastIndexOf(".")).toUpperCase();
	extension === ".XLS" || extension === ".XLSX"
	  ? excelFileToJSON(endpoint, file)
	  : alert("Please select a valid excel file.");
  }
  
  // Method to read excel file and convert it into JSON
  function excelFileToJSON(endpoint, file) {
	try {
	  const reader = new FileReader();
	  reader.readAsBinaryString(file);
	  reader.onload = function (e) {
		const data = e.target.result;
		const workbook = XLSX.read(data, { type: "binary" });
		const firstSheetName = workbook.SheetNames[0];
		const jsonData = XLSX.utils.sheet_to_json(workbook.Sheets[firstSheetName]);
		displayJsonToHtmlTable(endpoint, jsonData);
	  };
	} catch (e) {
	  console.error(e);
	}
  }
  
  // Method to display the data in HTML Table
  function displayJsonToHtmlTable(endpoint, jsonData) {
	const table = document.getElementById("display_excel_data");
	const format = document.getElementById("CO2_data");
	const structure = { times: [], CO2: [] };
	if (jsonData.length > 0) {
	  let htmlData = "<tr><th>Time</th><th>CO2 Value</th></tr>";
	  const jsonLength = jsonData.length;
	  for (let i = 0; i < jsonLength; i++) {
		const row = jsonData[i];
		if (i < 5) {
		  htmlData += `
			<tr>
			  <td>${row["Times"].toFixed(2)}</td>
			  <td>${row["CO2"].toFixed(2)}</td>
			</tr>`;
		}
		structure.times.push(row["Times"]);
		structure.CO2.push(row["CO2"]);
	  }
  
	  if (jsonLength >= 5) {
		htmlData += "<tr><td> ... </td><td> ... </td></tr>";
	  }
	  format.value = JSON.stringify(structure);
	  $('#generate_fitting_data').prop("disabled", false);
	  $('#fitting_ventilation_states').prop('disabled', false);
	  $('[name=fitting_ventilation_type]').prop('disabled', false);
	  plotCO2Data(endpoint);
	} else {
	  table.innerHTML = "There is no data in the spreadsheet file";
	}
  }
  
  // Method to download Excel template available on CERNBox
  function downloadTemplate(uri = 'https://caimira-resources.web.cern.ch/CO2_template.xlsx', filename = 'CO2_template.xlsx') {
	const link = document.createElement("a");
	link.download = filename;
	link.href = uri;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	delete link;
  }
  
  function insertErrorFor(referenceNode, text) {
	const element = document.createElement("span");
	element.setAttribute("class", "error_text");
	element.classList.add("red_text");
	element.innerHTML = "&nbsp;&nbsp;" + text;
	$(referenceNode).before(element);
  }
  
  function validateFormInputs(obj) {
	$('span.' + "error_text").remove();
	let submit = true;
	for (let i = 0; i < CO2_data_form.length; i++) {
	  const element = $(`[name=${CO2_data_form[i]}]`)[0];
	  if (element.name !== 'fitting_ventilation_states' && element.value === '') {
		insertErrorFor($('#DIVCO2_data_dialog'), `'${element.name}' must be defined.<br />`);
		submit = false;
	  }
	}
	if (submit) {
	  $($(obj).data('target')).modal('show');
	}
	return submit;
  }  

function validateCO2Form() {
	let submit = true;
	if (validateFormInputs($('#button_fit_data'))) submit = true;
	
	// Check if natural ventilation is selected
	if ($('input[name="fitting_ventilation_type"]:checked')[0].value == 'fitting_natural_ventilation') {
		// Validate ventilation scheme
		const element = $('[name=fitting_ventilation_states')[0]
		if (element.value !== '') {
			// validate input format
			try {
				const parsedValue = JSON.parse(element.value);
          		if (!Array.isArray(parsedValue)) {
					insertErrorFor($('#DIVCO2_fitting_result'), `'${element.name}' must be a list.</br>`);
					submit = false;
				};
			} catch {
				insertErrorFor($('#DIVCO2_fitting_result'), `'${element.name}' must be a list of numbers.</br>`);
				submit = false;
			};
		} else {
			insertErrorFor($('#DIVCO2_fitting_result'), `'${element.name}' must be defined.</br>`);
			submit = false;
		};
	};

	return submit;
}

function displayTransitionTimesHourFormat(start, stop) {
	var minutes_start = (start % 1 * 60).toPrecision(2);
	var minutes_stop = (stop % 1 * 60).toPrecision(2);
	return Math.floor(start) + ':' + ((minutes_start != '0.0') ? minutes_start : '00') + ' - ' + Math.floor(stop) + ':' + ((minutes_stop != '0.0') ? minutes_stop : '00');
}

function displayFittingData(json_response) {
	$("#DIVCO2_fitting_result").show();
	$("#CO2_data_plot").attr("src", json_response['CO2_plot']);
	// Not needed for the form submit
	delete json_response['CO2_plot']; 
	$("#CO2_fitting_result").val(JSON.stringify(json_response));
	$("#exhalation_rate_fit").html('Exhalation rate: ' + String(json_response['exhalation_rate'].toFixed(2)) + ' m³/h');
	let ventilation_table = "<tr><th>Time (HH:MM)</th><th>ACH value (h⁻¹)</th></tr>";
	json_response['ventilation_values'].forEach((val, index) => {
		let transition_times = displayTransitionTimesHourFormat(json_response['transition_times'][index], json_response['transition_times'][index + 1]);
		ventilation_table += `<tr><td>${transition_times}</td><td>${val.toPrecision(2)}</td></tr>`;
	});
	$('#disable_fitting_algorithm').prop('disabled', false);
	$("#ventilation_rate_fit").html(ventilation_table);
	$("#generate_fitting_data").html('Fit data');
	$("#generate_fitting_data").hide();
	$("#save_and_dismiss_dialog").show();
}

function formatCO2DataForm(CO2_data_form) {
	let CO2_mapping = {};
	CO2_data_form.map(el => {
		let element = $(`[name=${el}]`);
		// Validate checkboxes
		if (element[0].type == 'checkbox') {
			CO2_mapping[element[0].name] = String(+element[0].checked);
		}
		// Validate radio buttons
		else if (element[0].type == 'radio') CO2_mapping[element[0].name] = $(`[name=${element[0].name}]:checked`)[0].value;
		else CO2_mapping[element[0].name] = element[0].value;
	});
	return CO2_mapping;
}

function plotCO2Data(url) {
	if (validateFormInputs()) {
		let CO2_mapping = formatCO2DataForm(CO2_data_form);
		fetch(url, {
			method: "POST",
			body: JSON.stringify(CO2_mapping),
		})
			.then((response) => 
				response.json()
					.then(json_response => $("#CO2_data_plot").attr("src", json_response['CO2_plot']))
					.then($('#DIVCO2_fitting_to_submit').show())
					.catch(error => console.log(error))
			);
	}
}

function submitFittingAlgorithm(url) {
	if (validateCO2Form()) {
	  // Disable all the ventilation inputs
	  $('#fitting_ventilation_states, [name=fitting_ventilation_type]').prop('disabled', true);
  
	  // Prepare data for submission
	  const CO2_mapping = formatCO2DataForm(CO2_data_form);
	  $('#CO2_input_data_div').show();
	  $('#disable_fitting_algorithm').prop('disabled', true);
	  $('#generate_fitting_data')
		.html('<span id="loading_spinner" class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Loading...')
		.prop('disabled', true);
	  $('#CO2_input_data').html(JSON.stringify(CO2_mapping, null, '\t'));
  
	  fetch(url, {
		method: 'POST',
		body: JSON.stringify(CO2_mapping),
	  })
		.then((response) => response.json())
		.then((json_response) => {
		  displayFittingData(json_response);
		});
	}
  }
  
  function clearFittingResultComponent() {
	// Remove all the previously generated fitting elements
	$('#generate_fitting_data').prop('disabled', true);
	$('#CO2_fitting_result').val('');
	$('#CO2_data').val('{}');
	$('#fitting_ventilation_states').val('');
	$('span.error_text').remove();
	$('#DIVCO2_fitting_result, #CO2_input_data_div').hide();
	$('#CO2_data_plot').attr('src', '');
  
	// Update the ventilation scheme components
	$('#fitting_ventilation_states, [name=fitting_ventilation_type]').prop('disabled', false);
  
	// Update the bottom right buttons
	$('#generate_fitting_data').show();
	$('#save_and_dismiss_dialog').hide();
  }
  
  function disableFittingAlgorithm() {
	clearFittingResultComponent();
	$('#CO2_data_no').click();
  }
  
