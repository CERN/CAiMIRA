const CO2_data = [
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
	'windows_duration',
	'windows_frequency',
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
			var result = {};
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
		for (var i = 0; i < jsonData.length; i++) {
			var row = jsonData[i];
			htmlData +=
				"<tr><td>" +
				Math.round(row["Times"] * 10) / 10 +
				"</td><td>" +
				Math.round(row["CO2"] * 10) / 10 +
				"</td></tr>";
			structure["times"].push(row["Times"]);
			structure["CO2"].push(row["CO2"]);
		}
		table.innerHTML = htmlData;
		console.log(structure);
		format.value = JSON.stringify(structure);
	} else {
		table.innerHTML = "There is no data in Excel";
	}
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
	for (var i = 0; i < CO2_data.length; i++) {
		let element = $(`[name=${CO2_data[i]}]`);
		if (element[0].value === '') {
			insertErrorFor($('#CO2_input_data_div'), `'${element[0].name}' must be defined.`); // raise error for total number and room volume.
			submit = false;
		};
	}
	return submit;
}

function submit_fitting_algorithm(url) {
	if (validate()) {
		let CO2_mapping = {};
		CO2_data.map(el => {
			let element = $(`[name=${el}]`);
			// Validate radio buttons
			if (element.length != 1) CO2_mapping[element[0].name] = $(`[name=${element[0].name}]:checked`)[0].value
			else CO2_mapping[element[0].name] = element[0].value;
		})
		$('#CO2_input_data_div').show();
		$("#generate_fitting_data").html(
			`<span id="loading_spinner" class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Loading...`
		  );
		$('#CO2_input_data').html(JSON.stringify(CO2_mapping, null, "\t"))
		fetch(url, {
			method: "POST",
			body: JSON.stringify(CO2_mapping),
		})
			.then((response) => response.json())
			.then((json_response) => {
				console.log(json_response)
				$("#DIV_CO2_fitting_result").show();
				$("#CO2_fitting_result").val(JSON.stringify(json_response));
				$("#exhalation_rate_fit").html(String(json_response['exhalation_rate']));
				// $("#ventilation_rate_fit").html(json_response['ventilation_values']);
				$("#CO2_data_plot").attr("src", json_response['CO2_plot']);
				$("#generate_fitting_data").html('Fit data');
				$("#save_and_dismiss_dialog").show();
			});
	}
}

function clear_fitting_algorithm() {
	$("#display_excel_data tbody").remove();
	$('#CO2_fitting_result').val('');
	$('#formatted_data').val('');
	$('span.' + "error_text").remove();
	$('#DIV_CO2_fitting_result').hide();
	$('#CO2_input_data_div').hide();
	$('#CO2_data_no').click();
}

function dismiss_co2_dialog() {
	$('#CO2_data_no').click();
}