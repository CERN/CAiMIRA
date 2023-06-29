// JS file to handle manipulation on CO2 Fitting Algorithm Dialog.
const CO2_data_form = [
	'CO2_data',
	'specific_breaks',
	'exposed_coffee_break_option',
	'exposed_coffee_duration',
	'exposed_finish',
	'exposed_lunch_finish',
	'exposed_lunch_option',
	'exposed_lunch_start',
	'exposed_start',
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
	'windows_duration',
	'windows_frequency',
	'window_opening_regime',
]

// Method to upload a valid excel file
function upload_file() {
	var files = document.getElementById("file_upload").files;
	if (files.length == 0) {
		alert("Please choose any file...");
		return;
	}
	var filename = files[0].name;
	var extension = filename.substring(filename.lastIndexOf(".")).toUpperCase();
	if (extension == ".XLS" || extension == ".XLSX") {
		//Here calling another method to read excel file into json
		excelFileToJSON(files[0]);
	} else {
		alert("Please select a valid excel file.");
	}
}

//Method to read excel file and convert it into JSON
function excelFileToJSON(file) {
	try {
		var reader = new FileReader();
		reader.readAsBinaryString(file);
		reader.onload = function (e) {
			var data = e.target.result;
			var workbook = XLSX.read(data, { type: "binary" });
			var firstSheetName = workbook.SheetNames[0];
			//reading only first sheet data
			var jsonData = XLSX.utils.sheet_to_json(workbook.Sheets[firstSheetName]);
			//displaying the json result into HTML table
			displayJsonToHtmlTable(jsonData);
		};
	} catch (e) {
		console.error(e);
	}
}

//Method to display the data in HTML Table
function displayJsonToHtmlTable(jsonData) {
	var table = document.getElementById("display_excel_data");
	var format = document.getElementById("formatted_data");
	let structure = { times: [], CO2: [] };
	if (jsonData.length > 0) {
		var htmlData = "<tr><th>Time</th><th>CO2 Value</th></tr>";
		let jsonLength = jsonData.length;
		for (var i = 0; i < jsonLength; i++) {
			var row = jsonData[i];
			if (i < 5) {
				htmlData +=
					`<tr><td>
					${row["Times"].toFixed(2)}
					</td><td>
					${row["CO2"].toFixed(2)}
					</td></tr>`;
			}
			structure["times"].push(row["Times"]);
			structure["CO2"].push(row["CO2"]);
		}

		if (jsonLength >= 5) htmlData += "<tr><td> ... </td><td> ... </td></tr>";
		table.innerHTML = htmlData;
		format.value = JSON.stringify(structure);
		$('#generate_fitting_data').prop("disabled", false);
	} else {
		table.innerHTML = "There is no data in Excel";
	}
}

// Method to download Excel template available on CERNBox
function downloadTemplate(uri = 'https://caimira-resources.web.cern.ch/CO2_template.xlsx', filename = 'CO2_template.xlsx') {
	var link = document.createElement("a");
	link.download = filename;
	link.href = uri;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	delete link;
}

function insertErrorFor(referenceNode, text) {
	var element = document.createElement("span");
	element.setAttribute("class", "error_text");
	element.classList.add("red_text");
	element.innerHTML = "&nbsp;&nbsp;" + text;
	$(referenceNode).before(element);
}

function validate() {
	$('span.' + "error_text").remove();
	let submit = true;
	for (var i = 0; i < CO2_data_form.length; i++) {
		let element = $(`[name=${CO2_data_form[i]}]`)[0];
		if (element.value === '') {
			insertErrorFor($('#CO2_input_data_div'), `'${element.name}' must be defined.`); // raise error for total number and room volume.
			submit = false;
		};
	}
	return submit;
}

function display_fitting_data(json_response) {
	$("#DIV_CO2_fitting_result").show();
	$("#CO2_data_plot").attr("src", json_response['CO2_plot']);
	// Not needed for the form submit
	delete json_response['CO2_plot']; 
	$("#CO2_fitting_result").val(JSON.stringify(json_response));
	$("#exhalation_rate_fit").html('Exhalation rate: ' + String(json_response['exhalation_rate'].toFixed(2)) + ' m³/h');
	let ventilation_table = "<tr><th>Time</th><th>Ventilation value (ACH)</th></tr>";
	json_response['ventilation_values'].map((val, index) => {
		console.log(json_response['transition_times'])
		let transition_times = `${(json_response['transition_times'][index]).toFixed(2)} - ${(json_response['transition_times'][index + 1]).toFixed(2)}`
		ventilation_table += `<tr><td>${transition_times}</td><td>${val}</td></tr>`;
	});
	$("#ventilation_rate_fit").html(ventilation_table);
	$("#generate_fitting_data").html('Fit data');
	$("#save_and_dismiss_dialog").show();
}

function submit_fitting_algorithm(url) {
	if (validate()) {
		let CO2_mapping = {};
		CO2_data_form.map(el => {
			let element = $(`[name=${el}]`);
			// Validate radio buttons
			if (element.length != 1) CO2_mapping[element[0].name] = $(`[name=${element[0].name}]:checked`)[0].value
			else CO2_mapping[element[0].name] = element[0].value;
		})
		$('#CO2_input_data_div').show();
		$("#generate_fitting_data").html(
			`<span id="loading_spinner" class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true" disabled ></span>Loading...`
		  );
		$('#CO2_input_data').html(JSON.stringify(CO2_mapping, null, "\t"))
		fetch(url, {
			method: "POST",
			body: JSON.stringify(CO2_mapping),
		})
			.then((response) => response.json())
			.then((json_response) => {
				display_fitting_data(json_response);
			});
	}
}

function clear_fitting_algorithm() {
	$('#generate_fitting_data').prop("disabled", true);
	$("#display_excel_data tbody").remove();
	$('#CO2_fitting_result').val('');
	$('#formatted_data').val('');
	$('span.' + "error_text").remove();
	$('#DIV_CO2_fitting_result').hide();
	$('#CO2_input_data_div').hide();
	$('#CO2_data_no').click();
	ventilation_from_fitting(false);
}
