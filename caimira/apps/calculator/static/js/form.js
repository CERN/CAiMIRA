/* -------HTML structure------- */
function getChildElement(elem) {
  // Get the element named in the given element's data-enables attribute.
  return $(elem.data("enables"));
}

function insertErrorFor(referenceNode, text) {
  var element = document.createElement("span");
  element.setAttribute("class", "error_text");
  element.classList.add("red_text");
  element.innerHTML = "&nbsp;&nbsp;" + text;
  referenceNode.parentNode.insertBefore(element, referenceNode.nextSibling);
}

function removeErrorFor(referenceNode) {
  $(referenceNode).next('span.error_text').remove();
}

/* -------Required fields------- */
function require_fields(obj) {
  switch ($(obj).attr('id')) {
    case "room_data_volume":
      require_room_volume(true);
      require_room_dimensions(false);
      break;
    case "room_data_dimensions":
      require_room_volume(false);
      require_room_dimensions(true);
      break;
    case "mechanical_ventilation":
      require_mechanical_ventilation(true);
      require_natural_ventilation(false);
      break;
    case "natural_ventilation":
      require_mechanical_ventilation(false);
      require_natural_ventilation(true);
      break;
    case "window_sliding":
      require_window_width(false);
      break;
    case "window_hinged":
      require_window_width(true);
      break;
    case "mech_type_air_changes":
      require_air_changes(true);
      require_air_supply(false);
      break;
    case "mech_type_air_supply":
      require_air_changes(false);
      require_air_supply(true);
      break;
    case "windows_open_periodically":
      require_venting(true);
      break;
    case "windows_open_permanently":
      require_venting(false);
      break;
    case "hepa_yes":
      require_hepa(true);
      break;
    case "hepa_no":
      require_hepa(false);
      break;
    case "p_probabilistic_exposure":
      require_population(true);
      require_infected(false);
      break;
    case "p_deterministic_exposure":
      require_population(false);
      require_infected(true);
      break;
    case "mask_on":
      require_mask(true);
      break;
    case "mask_off":
      require_mask(false);
      break;
    case "exposed_lunch_option_no":
    case "infected_lunch_option_no":
      require_lunch($(obj).attr('id'), false);
      break;
    case "exposed_lunch_option_yes":
    case "infected_lunch_option_yes":
      require_lunch($(obj).attr('id'), true);
      break;
    default:
      break;
  }
}

function unrequire_fields(obj) {
  switch (obj.id) {
    case "mechanical_ventilation":
      require_mechanical_ventilation(false);
      break;
    case "natural_ventilation":
      require_natural_ventilation(false);
      break;
    default:
      break;
  }
}

function require_room_volume(option) {
  require_input_field("#room_volume", option);
  set_disabled_status("#room_volume", !option);
}

function require_room_dimensions(option) {
  require_input_field("#floor_area", option);
  require_input_field("#ceiling_height", option);
  set_disabled_status("#floor_area", !option);
  set_disabled_status("#ceiling_height", !option);
}

function require_mechanical_ventilation(option) {
  $("#mech_type_air_changes").prop('required', option);
  $("#mech_type_air_supply").prop('required', option);
  if (!option) {
    require_input_field("#air_changes", option);
    require_input_field("#air_supply", option);
  }
}

function require_natural_ventilation(option) {
  require_input_field("#windows_number", option);
  require_input_field("#window_height", option);
  require_input_field("#opening_distance", option);
  $("#window_sliding").prop('required', option);
  $("#window_hinged").prop('required', option);
  $("#windows_open_permanently").prop('required', option);
  $("#windows_open_periodically").prop('required', option);
  if (!option) {
    require_input_field("#window_width", option);
    require_input_field("#windows_duration", option);
    require_input_field("#windows_frequency", option);
  }
}

function require_window_width(option) {
  require_input_field("#window_width", option);
  set_disabled_status("#window_width", !option);
}

function require_air_changes(option) {
  require_input_field("#air_changes", option);
  set_disabled_status("#air_changes", !option);
}

function require_air_supply(option) {
  require_input_field("#air_supply", option);
  set_disabled_status("#air_supply", !option);
}

function require_venting(option) {
  require_input_field("#windows_duration", option);
  require_input_field("#windows_frequency", option);
}

function require_lunch(id, option) {
  var activity = $(document.getElementById(id)).data('lunch-select');
  var startObj = $(".start_time[data-lunch-for='"+activity+"']")[0];
  var startID = '#'+$(startObj).attr('id');
  var finishObj = $(".finish_time[data-lunch-for='"+activity+"']")[0];
  var finishID = '#'+$(finishObj).attr('id');

  require_input_field(startID, option);
  require_input_field(finishID, option);

  if (!option) {
    $(finishID).removeClass("red_border finish_time_error lunch_break_error");
    removeErrorFor(finishObj);
  }
  else {
    if (startObj.value === "" && finishObj.value === "") {
      startObj.value = "12:30";
      finishObj.value = "13:30";
    }
    validateLunchBreak($(startObj).data('time-group'));
  }
}

function require_population(option) {
  require_input_field("#geographic_population", option);
  require_input_field("#geographic_cases", option);
  require_input_field("#ascertainment_bias", option);
}

function require_infected(option) {
  require_input_field("#infected_people", option);
}

function require_mask(option) {
  $("#mask_type_1").prop('required', option);
  $("#mask_type_ffp2").prop('required', option);
}

function require_hepa(option) {
  require_input_field("#hepa_amount", option);
}

function require_input_field(id, option) {
  $(id).prop('required', option);
  if (!option) {
    removeInvalid(id);
  }
}

function set_disabled_status(id, option) {
  if (option)
    $(id).addClass("disabled");
  else
    $(id).removeClass("disabled");
}

function validateMaxInfectedPeople() {
  let infected_people = document.getElementById("infected_people");
  removeErrorFor(infected_people);
  $(infected_people).removeClass("red_border");
  
  let infected = infected_people.valueAsNumber;
  let max = document.getElementById("total_people").valueAsNumber;

  if ($("#activity_type").val() === "training" && infected > 1) {
    insertErrorFor(infected_people, "Conference/Training activities limited to 1 infected person.");
    $(infected_people).addClass("red_border");
    return false;
  }
  else if (infected >= max) {
    insertErrorFor(infected_people, "Value is equal or higher than the total number of occupants.");
    $(infected_people).addClass("red_border");
    return false;
  }

  return true;
}

function removeInvalid(id) {
  if ($(id).hasClass("red_border")) {
    $(id).val("");
    $(id).removeClass("red_border");
    removeErrorFor(id);
  }
}

function on_ventilation_type_change() {
  ventilation_types = $('input[type=radio][name=ventilation_type]');
  ventilation_types.each(function (index) {
    if (this.checked) {
      getChildElement($(this)).show();
      require_fields(this);
    } else {
      getChildElement($(this)).hide();
      unrequire_fields(this);

      //Clear invalid inputs for this newly hidden child element
      removeInvalid("#"+getChildElement($(this)).find('input').not('input[type=radio]').attr('id'));
    }
  });
}

function on_window_opening_change() {
  opening_regime = $('input[type=radio][name=window_opening_regime]')
  opening_regime.each(function (index) {
    if (this.checked) {
      getChildElement($(this)).show();
      require_fields(this);
    }
    else {
      getChildElement($(this)).hide();
      require_fields(this);
    }
  })
}

function on_hepa_option_change() {
  hepa_option = $('input[type=radio][name=hepa_option]')
  hepa_option.each(function (index) {
    if (this.checked) {
      getChildElement($(this)).show();
      require_fields(this);
    }
    else {
      getChildElement($(this)).hide();
      require_fields(this);
    }
  })
}

function on_exposure_change() {
  p_recurrent = $('input[type=radio][name=exposure_option]')
  p_recurrent.each(function (index) {
    if (this.checked) {
      getChildElement($(this)).show();
      require_fields(this);
    }
    else {
      getChildElement($(this)).hide();
      unrequire_fields(this);

      //Clear invalid inputs for this newly hidden child element
      removeInvalid("#"+getChildElement($(this)).find('input').not('input[type=radio]').attr('id'));
    }
  })
}

function on_wearing_mask_change() {
  wearing_mask = $('input[type=radio][name=mask_wearing_option]')
  wearing_mask.each(function (index) {
    if (this.checked) {
      getChildElement($(this)).show();
      require_fields(this);
      if (this.id == "mask_on") {
        $('#short_range_no').click();
        $('input[name="short_range_option"]').attr('disabled', true);
        $("#short_range_warning").show();
      }
      else {
        $('input[name="short_range_option"]').attr('disabled', false);
        $("#short_range_warning").hide();
      }

    }
    else {
      getChildElement($(this)).hide();
      require_fields(this);
    }
  })
}

function update_booster_warning() {
  // Check if "Other" is selected
  $("#vaccine_booster_type").find(":selected").val() == "Other" ? $("#booster_warning").show() : $("#booster_warning").hide();
}

function update_booster_dropdown(url) {
  let primary_vaccine_option = $("#vaccine_type").find(":selected").val();
  $("#vaccine_booster_type option").remove();
  vaccine_booster_host_immunity.forEach(booster => {
    if (booster['primary series vaccine'] == primary_vaccine_option) 
      $("#vaccine_booster_type").append(`<option data-primary-vaccine=${primary_vaccine_option} value=${booster['booster vaccine']}>${booster['booster vaccine'].replaceAll('_', ' ')}</option>`);
  });
  $("#vaccine_booster_type").append(`<option value='Other'>Other</option>`);

  let booster_vaccine = url.searchParams.has('vaccine_booster_type') ? url.searchParams.get('vaccine_booster_type') : null;
  $(`#vaccine_booster_type > option[value="${booster_vaccine}"`).attr('selected', true);

  update_booster_warning();
}

function on_vaccination_change(url) {
  vaccination_option = $('input[type=radio][name=vaccine_option]');
  vaccination_option.each(function (index) {
    if (this.checked) {
      getChildElement($(this)).show();
      require_fields(this);
    }
    else {
      getChildElement($(this)).hide();
      require_fields(this);
    }
  });
  update_booster_dropdown(url);
}

function on_vaccination_booster_change() {
  vaccination_booster_option = $('input[type=radio][name=vaccine_booster_option]');
  vaccination_booster_option.each(function (index) {
    if (this.checked) getChildElement($(this)).show();
    else getChildElement($(this)).hide();
  });
}

function populate_temp_hum_values(data, index) {
  $("#sensor_temperature").text(Math.round(data[index].Details.T) + '°C');
  $("#sensor_humidity").text(Math.round(data[index].Details.RH) + '%');
  $("[name='inside_temp']").val(data[index].Details.T + 273.15);
  $("[name='humidity']").val(data[index].Details.RH/100);
};

//Data from ARVE sensors
var DATA_FROM_SENSORS;
function show_sensors_data(url) {

  const HOTEL_ID = "CERN"
  const FLOOR_ID = "1"

  if ($('#sensors  > option').length == 0) {
    $.ajax({
      url: `${$('#url_prefix').data().calculator_prefix}/api/arve/v1/${HOTEL_ID}/${FLOOR_ID}`,
      type: 'GET',
      success: function (result) {
        DATA_FROM_SENSORS = result;
        result.map(room => {
          if (room['Details']['Online'] == false) return; // If the sensor is offline, it should not be added to the list.
          $("#sensors").append(`<option id=${room.RoomId} value=${room.RoomId}>Sensor ${room.RoomId}</option>`);
        });
        if ($('#sensors > option').length == 0) {
          $('#offline_sensors').show();
          $('#DIVsensors_data').hide();
          $('#arve_sensor_yes').prop('disabled', true)
          return; // All sensors are offline
        }
        populate_temp_hum_values(result, 0);
        if (url.searchParams.has('sensor_in_use')) {
          $("#sensors").val(url.searchParams.get('sensor_in_use'));
          populate_temp_hum_values(result, result.findIndex(function(sensor) {
            return sensor.RoomId == url.searchParams.get('sensor_in_use');
          }));
        }
      },
      error: function(_, _, errorThrown) {
        $("#arve_api_error_message").val(errorThrown).show();
        $('#DIVsensors_data').hide();
        $('#arve_sensor_yes').prop('disabled', true)
      }
    });
  }
};

function geographic_cases(location_country_name) {
  $.ajax({
    url: `${$('#url_prefix').data().calculator_prefix}/cases/${location_country_name}`,
    type: 'GET',
    success: function (result) {
      $('#geographic_cases').val(result);
      result != '' ? $('#source_geographic_cases').show() : $('#source_geographic_cases').hide();
    },
    error: function(_, _, errorThrown) {
      console.log(errorThrown);
    }
  });
}

$("#sensors").change(function (el) {
  sensor_id = DATA_FROM_SENSORS.findIndex(function(sensor) {
    return sensor.RoomId == el.target.value
  });
  populate_temp_hum_values(DATA_FROM_SENSORS, sensor_id);
});

function on_use_sensors_data_change(url) {
  sensor_data = $('input[type=radio][name=arve_sensors_option]')
  sensor_data.each(function (index) {
    if (this.checked) {
      getChildElement($(this)).show();
      show_sensors_data(url);
    }
    else {
      getChildElement($(this)).hide();
    }
  })
}

function on_short_range_option_change() {
  short_range = $('input[type=radio][name=short_range_option]')
  short_range.each(function (index){
    if (this.checked) {
      getChildElement($(this)).show();
      require_fields(this);
    } 
    else {
      getChildElement($(this)).hide();
      require_fields(this);
    }
  })
}

function on_lunch_break_option_change() {
  all_lunch_breaks = [$('input[type=radio][name=exposed_lunch_option]'), $('input[type=radio][name=infected_lunch_option]')];
  for (lunch_break of all_lunch_breaks) {
    lunch_break.each(function() {
      children = getChildElement($(this));
      this.checked ? children.show() : children.hide();
      require_fields(this);
    })
  }
}

function on_coffee_break_option_change() {
  all_coffee_breaks = [$('input[type=radio][name=exposed_coffee_break_option]'), $('input[type=radio][name=infected_coffee_break_option]')];
  for (coffee_breaks of all_coffee_breaks) {
    coffee_breaks.each(function() {
      children = getChildElement($(this));
      if (this.checked && children.length) {
        children.show();
        return false;
      }
      else {
        children.hide();
      }
    })
  }
}

function on_CO2_fitting_ventilation_change() {
  ventilation_options = $('input[type=radio][name=fitting_ventilation_type]');
  ventilation_options.each(function (index) {
    if (this.checked) {
      getChildElement($(this)).show();
      require_fields(this);
    }
    else {
      getChildElement($(this)).hide();
      require_fields(this);
    }
  })
}

/* -------UI------- */

function show_disclaimer() {
  var dots = document.getElementById("dots");
  var moreText = document.getElementById("more");
  var btnText = document.getElementById("myBtn");

  if (dots.style.display === "none") {
    dots.style.display = "inline";
    btnText.innerHTML = "Read more";
    moreText.style.display = "none";
  } else {
    dots.style.display = "none";
    btnText.innerHTML = "Read less";
    moreText.style.display = "inline";
  }
}

$("[data-has-radio]").on('click', function(event){
  $($(this).data("has-radio")).click();
});

$("[data-has-radio]").on('change', function(event){
  $($(this).data("has-radio")).click();
});

function toggle_split_breaks() {
  $("#DIVinfected_breaks").toggle(this.checked);
  $("#exposed_break_title").toggle(this.checked);
  require_lunch("infected_lunch_option_yes", document.getElementById("infected_dont_have_breaks_with_exposed").checked);
}

/* -------Form validation------- */
function validate_form(form) {
  var submit = true;

  // Activity times and lunch break times are co-dependent
  // -> So if 1 fails it doesn't make sense to check the rest

  //Validate all finish times
  $("input[required].finish_time").each(function() {
    var activity = $(this).data('lunch-for');
    if (document.getElementById("infected_dont_have_breaks_with_exposed").checked || activity!="infected") {
      if (!validateFinishTime(this)) {
        submit = false;
      }
    }
  });

  //Validate all lunch breaks
  if (submit) {
    $("input[required].start_time[data-lunch-for]").each(function() {
      var activity = $(this).data('lunch-for');
      if (document.getElementById("infected_dont_have_breaks_with_exposed").checked || activity!="infected") {
        if (!validateLunchBreak($(this).data('time-group'))) {
          submit = false;
        }
      }
    });
  }

  //Check if breaks length >= activity length
  if (submit) {
    $("[data-lunch-for]").each(function() {
      var activity = $(this).data('lunch-for');
      if (document.getElementById("infected_dont_have_breaks_with_exposed").checked || activity!="infected") {
        var activityBreaksObj= document.getElementById("activity_breaks");
        removeErrorFor(activityBreaksObj);

        var lunch_mins = 0;
        if (document.getElementById(activity+"_lunch_option_yes").checked) {
          var lunch_start = document.getElementById(activity+"_lunch_start");
          var lunch_finish = document.getElementById(activity+"_lunch_finish");
          lunch_mins = parseTimeToMins(lunch_finish.value) - parseTimeToMins(lunch_start.value);
        }

        var coffee_breaks = parseInt(document.querySelector('input[name="'+activity+'_coffee_break_option"]:checked').value);
        var coffee_duration = parseInt(document.getElementById(activity+"_coffee_duration").value);
        var coffee_mins = coffee_breaks * coffee_duration;
        
        var activity_start = document.getElementById(activity+"_start");
        var activity_finish = document.getElementById(activity+"_finish");
        var activity_mins = parseTimeToMins(activity_finish.value) - parseTimeToMins(activity_start.value);

        if ((lunch_mins + coffee_mins) >= activity_mins) {
          insertErrorFor(activityBreaksObj, "Length of breaks >= Length of "+activity+" presence");
          submit = false;
        }
      }
    });
  }

  // Logic for the API requests. Always set humity input as the empty string so that we can profit from the "room_heating_option default" values for humidity.
  if ($("#arve_sensor_no").prop('checked')) {
    $("[name='humidity']").val('');
  }

  // Validate location input.
  if (submit) {
      // We make the non-visible location inputs mandatory, without marking them as "required" inputs.
      // See https://stackoverflow.com/q/22148080/741316 for motivation.
      var locationSelectObj= document.getElementById("location_select");
      removeErrorFor(locationSelectObj);
      $("input[name*='location']").each(function() {
        el = $(this);
        if ($.trim(el.val()) == ''){
          submit = false;
        }
      });

      if (!submit) {
        insertErrorFor(locationSelectObj, "Please select a location");
      }
  }

  //Validate number of infected people
  if (!validateMaxInfectedPeople()) submit = false;

  //Validate all non zero values
  $("input[required].non_zero").each(function() {
    if (!validateValue(this)) {
      submit = false;
    }
  });

  //Validate window venting duration < venting frequency
  if ($("#windows_open_periodically").prop('checked')) {
    var windowsDurationObj = document.getElementById("windows_duration");
    var windowsFrequencyObj = document.getElementById("windows_frequency");
    removeErrorFor(windowsFrequencyObj);

    if (parseInt(windowsDurationObj.value) >= parseInt(windowsFrequencyObj.value)) {
      insertErrorFor(windowsFrequencyObj, "Duration >= Frequency");
      submit = false;
    }
  }

  // Validate cases < population
  if ($("#p_probabilistic_exposure").prop('checked')) {
    // Set number of infected people as 1
    $("#infected_people").val(1);
    var geographicPopulationObj = document.getElementById("geographic_population");
    var geographicCasesObj = document.getElementById("geographic_cases");
    removeErrorFor(geographicCasesObj);

    if (parseInt(geographicPopulationObj.value) < parseInt(geographicCasesObj.value)) {
      insertErrorFor(geographicCasesObj, "Cases > Population");
      submit = false;
    }
  }

  // Generate the short-range interactions list
  var short_range_interactions = [];
  $(".form_field_outer_row").each(function (index, element){
      let obj = {};
      const $element = $(element);
      obj.expiration = $element.find("[name='short_range_expiration']").val();
      obj.start_time = $element.find("[name='short_range_start_time']").val();
      obj.duration = $element.find("[name='short_range_duration']").val();
      short_range_interactions.push(JSON.stringify(obj));
  });

  // Sort list by time
  short_range_interactions.sort(function (a, b) {
    return JSON.parse(a).start_time.localeCompare(JSON.parse(b).start_time);
  });
  $("input[type=text][name=short_range_interactions]").val('[' + short_range_interactions + ']');
  if (short_range_interactions.length == 0) {
    $("input[type=radio][id=short_range_no]").prop("checked", true);
    on_short_range_option_change();
  }

  // Check if fitting is selected
  if ($('input[type=radio][id=from_fitting]').prop('checked')) {
    if ($('#CO2_fitting_result').val() == '')
      $("input[type=radio][id=no_ventilation]").prop("checked", true);
      $("span.error_text").remove();
    on_ventilation_type_change();
  }

  if (submit) {
    $("#generate_report").prop("disabled", true);
    //Add spinner to button
    $("#generate_report").html(
      `<span id="loading_spinner" class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Loading...`
    );
  }

  if ($("#CO2_fitting_result").val() == "") $("#CO2_data_no").click();

  return submit;
}

function validateValue(obj) {
  $(obj).removeClass("red_border");
  removeErrorFor(obj);

  if (!isLessThanZeroOrEmpty($(obj).val())) {
    $(obj).addClass("red_border");
    insertErrorFor(obj, "Value must be > 0");
    return false;
  }
  return true;
}

function isLessThanZeroOrEmpty(value) {
  if (value === "") return true;
  if (value <= 0)
    return false;
  return true;
}

function validateDate(obj) {
  $(obj).removeClass("red_border");
  removeErrorFor(obj);

  if (!isValidDateOrEmpty($(obj).val())) {
    $(obj).addClass("red_border");
    insertErrorFor(obj, "Incorrect date format");
    return false;
  }
  return true;
}

function isValidDateOrEmpty(date) {
  if (date === "") return true;
  var matches = /^(\d+)[-\/](\d+)[-\/](\d+)$/.exec(date);
  if (matches == null) return false;
  var d = matches[1];
  var m = matches[2];
  var y = matches[3];
  if (y > 2100 || y < 1900) return false;
  var composedDate = new Date(y + '/' + m + '/' + d);
  return composedDate.getDate() == d && composedDate.getMonth() + 1 == m && composedDate.getFullYear() == y;
}

function validateFinishTime(obj) {
  var groupID = $(obj).data('time-group');
  var startObj = $(".start_time[data-time-group='"+groupID+"']")[0];
  var finishObj = $(".finish_time[data-time-group='"+groupID+"']")[0];

  if ($(finishObj).hasClass("finish_time_error")) {
    $(finishObj).removeClass("red_border finish_time_error");
    removeErrorFor(finishObj);
  }

  //Check if finish time error (takes precedence over lunch break error)
  var startTime = parseValToNumber(startObj.value);
  var finishTime = parseValToNumber(finishObj.value);
  if (startTime >= finishTime) {
    $(finishObj).addClass("red_border finish_time_error");
    removeErrorFor(finishObj);
    insertErrorFor(finishObj, "Finish time must be after start");
    return false;
  }
  return true;
}

function validateLunchBreak(lunchGroup) {
  //Valid if lunch break not selected
  if(document.getElementById(lunchGroup+"_option_no").checked)
    return true;

  var lunchStartObj = $(".start_time[data-time-group='"+lunchGroup+"']")[0];
  var lunchFinishObj = $(".finish_time[data-time-group='"+lunchGroup+"']")[0];

  //Skip if finish time error present (it takes precedence over lunch break error)
  if ($(lunchStartObj).hasClass("finish_time_error") || $(lunchFinishObj).hasClass("finish_time_error"))
    return false;

  removeErrorFor(lunchFinishObj);
  var valid = validateLunchTime(lunchStartObj) & validateLunchTime(lunchFinishObj);
  if (!valid) {
    insertErrorFor(lunchFinishObj, "Lunch break must be within presence times");
  }

  return valid;
}

//Check if exposed/infected lunch time within exposed/infected presence times
function validateLunchTime(obj) {
  var activityGroup = $(obj).data('lunch-for');
  var activityStart = parseValToNumber($(".start_time[data-time-group='"+activityGroup+"']")[0].value);
  var activityFinish = parseValToNumber($(".finish_time[data-time-group='"+activityGroup+"']")[0].value);

  var time = parseValToNumber(obj.value);
  $(obj).removeClass("red_border lunch_break_error");
  if ((time < activityStart) || (time > activityFinish)) {
    $(obj).addClass("red_border lunch_break_error");
    return false;
  }

  return true;
}

function overlapped_times(obj, start_time, finish_time) {
  removeErrorFor($(obj));
  $(obj).removeClass("red_border");

  let parameter = document.getElementById($(obj).attr('id'));

  if ($(obj).attr('name') == "short_range_duration" && parseFloat($(obj).val()) < 15.0) {
    if (!$(obj).hasClass("red_border")) $(parameter).addClass("red_border"); //Adds the red border and error message.
        insertErrorFor(parameter, "Must be ≥ 15 min.")
    return false;
  }
  
  let simulation_start = parseTimeToMins($("#exposed_start").val())
  let simulation_finish = parseTimeToMins($("#exposed_finish").val())
  var simulation_lunch_start, simulation_lunch_finish;
  if ($('input[name=exposed_lunch_option]:checked').val() == 1) {
    simulation_lunch_start = parseTimeToMins($("#exposed_lunch_start").val())
    simulation_lunch_finish = parseTimeToMins($("#exposed_lunch_finish").val())
  } else {
    simulation_lunch_start = 0
    simulation_lunch_finish = 0
  }
  if (start_time < simulation_start || start_time > simulation_finish  ||
    finish_time < simulation_start || finish_time > simulation_finish ||
    start_time >= simulation_lunch_start && start_time <= simulation_lunch_finish ||
    finish_time >= simulation_lunch_start && finish_time <= simulation_lunch_finish ) {//If start and finish inputs are out of the simulation period
      //Adds the red border and error message.
      if (!$(obj).hasClass("red_border")) $(parameter).addClass("red_border");
      insertErrorFor(parameter, "Out of event time.");
      return false;
  } 
  let current_interaction = $(obj).closest(".form_field_outer_row");
  var toReturn = true;
  $(".form_field_outer_row.row_validated").not(current_interaction).each(function(index, el) {
    let current_start_el = $(el).find("input[name='short_range_start_time']");
    let current_duration_el = $(el).find("input[name='short_range_duration']")
    start_time_2 = parseTimeToMins(current_start_el.val())
    finish_time_2 = parseTimeToMins(current_start_el.val()) + parseInt(current_duration_el.val());
    if ((start_time > start_time_2 && start_time < finish_time_2) || ( //If hour input is within other time range
      finish_time > start_time_2 && finish_time < finish_time_2) || //If finish time input is within other time range
        (start_time <= start_time_2 && finish_time >= finish_time_2) || //If start and finish inputs encompass other time range 
        start_time == start_time_2) {
        if (!$(obj).hasClass("red_border")) $(parameter).addClass("red_border"); //Adds the red border and error message.
        insertErrorFor(parameter, "Time overlap.")
        toReturn = false;
        return false;
    }
  });
  return toReturn;
}

function validate_sr_time(obj) {
    let obj_id = $(obj).attr('id').split('_').slice(-1)[0];
    var start_time, finish_time;
    if ($(obj).val() != "") {
      if ($('#sr_start_no_' + String(obj_id)).val()) start_time = parseTimeToMins($('#sr_start_no_' + String(obj_id)).val());
      else start = 0.
      finish_time = start_time + parseInt($('#sr_duration_no_' + String(obj_id)).val());
    }
    return overlapped_times(obj, start_time, finish_time);
};

// Check if short-range durations are filled, and if there is no repetitions
function validate_sr_parameter(obj, error_message) {
  if ($(obj).val() == "" || $(obj).val() == null) {
    if (!$(obj).hasClass("red_border") && !$(obj).prop("disabled")) {
      var parameter = document.getElementById($(obj).attr('id'));
      insertErrorFor(parameter, error_message);
      $(parameter).addClass("red_border");
    }
    return false;
  } else {
    removeErrorFor($(obj));
    $(obj).removeClass("red_border");
    return true;
  }
}

function validate_sr_people(obj) {
  let sr_total_people = document.getElementById($(obj).attr('id'));
  let max = document.getElementById("total_people").valueAsNumber - document.getElementById("infected_people").valueAsNumber;
  if ($(obj).val() == "" || $(obj).val() == null || sr_total_people.valueAsNumber > max) {
    if (!$(obj).hasClass("red_border")) {
      insertErrorFor(sr_total_people, "Value must be less or equal than the number of exposed people.");
      $(sr_total_people).addClass("red_border");
    }
    return false;
  } else {
    removeErrorFor($(obj));
    $(obj).removeClass("red_border");
    return true;
  }
}

function parseValToNumber(val) {
  return parseInt(val.replace(':',''), 10);
}

function parseTimeToMins(cTime) {
  var time = cTime.match(/(\d+):(\d+)/);
  return parseInt(time[1]*60) + parseInt(time[2]);
}

// Prevent spinner when clicking on back button
window.onpagehide = function(){
  $('loading_spinner').remove();
  $("#generate_report").prop("disabled", false).html(`Generate report`);
};

/* -------On Load------- */
$(document).ready(function () {
  var url = new URL(decodeURIComponent(window.location.href));
  //Pre-fill form with known values

  url.searchParams.forEach((value, name) => {
    //If element exists
    if(document.getElementsByName(name).length > 0) {
      var elemObj = document.getElementsByName(name)[0];

      //Pre-select checked radios
      if (elemObj.type === 'radio') {
        // Calculator <= 1.5.0 used to send not-applicable in the URL for radios that
        // weren't set. Now those are not sent at all, but we keep the behaviour for compatibility.
        if (value !== 'not-applicable') {
          $('[name="'+name+'"][value="'+value+'"]').prop('checked',true);
        }
      }
      //Pre-select checkboxes
      else if (elemObj.type === 'checkbox') {
        elemObj.checked = (value==1);
      }

      // Read short-range from URL
      else if (name == 'short_range_interactions') {
        let index = 1;
        for (const interaction of JSON.parse(value)) {
          $("#dialog_sr").append(inject_sr_interaction(index, value = interaction, is_validated="row_validated"))
          $('#sr_expiration_no_' + String(index)).val(interaction.expiration).change();
          document.getElementById('sr_expiration_no_' + String(index)).disabled = true;
          document.getElementById('sr_start_no_' + String(index)).disabled = true;
          document.getElementById('sr_duration_no_' + String(index)).disabled = true;
          document.getElementById('edit_row_no_' + String(index)).style.cssText = 'display:inline !important';
          document.getElementById('validate_row_no_' + String(index)).style.cssText = 'display: none !important';
          index++;
        }
        $("#sr_interactions").text(index - 1);
      }

      else if (name == 'sensor_in_use' || name == 'vaccine_type' || name == 'vaccine_booster_type') {
        // Validation after
      }


      // Read CO2 Fitting Algorithms result
      else if (name == 'CO2_fitting_result' || name == 'CO2_data') {
        // Validation after
      }

      //Ignore 0 (default) values from server side
      else if (!(elemObj.classList.contains("non_zero") || elemObj.classList.contains("remove_zero")) || (value != "0.0" && value != "0")) {
        elemObj.value = value;
        validateValue(elemObj);
      }
    }
  });

  // Handle default URL values if they are not explicitly defined.

  // Populate CO2 Fitting Algorithm Dialog
  let CO2_data = url.searchParams.has('CO2_fitting_result') ? url.searchParams.get('CO2_fitting_result') : null;
  if (CO2_data) displayFittingData(JSON.parse(CO2_data));

  // Populate primary vaccine dropdown
  $("#vaccine_type option").remove();
  let primary_vaccine = url.searchParams.has('vaccine_type') ? url.searchParams.get('vaccine_type') : null;
  vaccine_primary_host_immunity.forEach(vaccine => $("#vaccine_type").append(`<option value=${vaccine}>${vaccine.replaceAll('_', ' ')}</option>`));
  $(`#vaccine_type > option[value="${primary_vaccine}"]`).attr('selected', true);

  // Handle geographic location input
  if (Array.from(url.searchParams).length > 0) {
    if (!url.searchParams.has('location_name')) {
      $('[name="location_name"]').val('Geneva')
      $('[name="location_select"]').val('Geneva')
    }
    if (!url.searchParams.has('location_latitude')) {
      $('[name="location_latitude"]').val('46.20833')
    }
    if (!url.searchParams.has('location_longitude')) {
      $('[name="location_longitude"]').val('6.14275')
    }
  }

  // Update geographic_cases
  geographic_cases('CHE');

  // Handle WHO source message if geographic_cases pre-defined value is modified by user
  $('#geographic_cases').change(() => $('#source_geographic_cases').hide());
  
  // When the document is ready, deal with the fact that we may be here
  // as a result of a forward/back browser action. If that is the case, update
  // the visibility of some of our inputs.

  // Chrome fix - on back button infected break DIV not shown
  if (document.getElementById("infected_dont_have_breaks_with_exposed").checked) {
    $("#DIVinfected_breaks").show();
    $("#exposed_break_title").show();
    require_lunch("infected_lunch_option_yes", true);
  }

  //Check all radio buttons previously selected
  $("input[type=radio]:checked").each(function() {require_fields(this)});

  // TEMPORARILY DISABLED
  // On CERN theme, when the arve_sensors_option changes we want to make its respective
  // children show/hide.
  // if ($("input[type=radio][name=arve_sensors_option]").length > 0) {
  //   $("input[type=radio][name=arve_sensors_option]").change(on_use_sensors_data_change);
  //   // Call the function now to handle forward/back button presses in the browser.
  //   on_use_sensors_data_change(url);
  // }

  // When the ventilation_type changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=ventilation_type]").change(on_ventilation_type_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_ventilation_type_change();

  // When the window_opening_regime changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=window_opening_regime]").change(on_window_opening_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_window_opening_change();

  // When the hepa filtration option changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=hepa_option]").change(on_hepa_option_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_hepa_option_change();

  // When the exposure_option changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=exposure_option]").change(on_exposure_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_exposure_change();

  // When the mask_wearing_option changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=mask_wearing_option]").change(on_wearing_mask_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_wearing_mask_change();

  // When the vaccinated_option_option changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=vaccine_option]").change(() => on_vaccination_change(url));
  // Call the function now to handle forward/back button presses in the browser.
  on_vaccination_change(url);

  // When the vaccine_type dropdown selected option changes we want to update
  // the booster vaccine dropdown.
  $("#vaccine_type").change(() => update_booster_dropdown(url));
  $("#vaccine_booster_type").change(update_booster_warning);

  // When the vaccinated_booster_option changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=vaccine_booster_option]").change(on_vaccination_booster_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_vaccination_booster_change();

  // When the short_range_option changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=short_range_option]").change(on_short_range_option_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_short_range_option_change();

  // When a lunch_option changes we want to make its respective children
  // to show/hide
  $("input[type=radio][name=exposed_lunch_option]").change(on_lunch_break_option_change);
  $("input[type=radio][name=infected_lunch_option]").change(on_lunch_break_option_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_lunch_break_option_change();

  // When the coffee_break_option changes we want to make its respective
  // children show/hide
  $("input[type=radio][name=exposed_coffee_break_option]").change(on_coffee_break_option_change);
  $("input[type=radio][name=infected_coffee_break_option]").change(on_coffee_break_option_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_coffee_break_option_change();

  // When the ventilation on the fitting changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=fitting_ventilation_type]").change(on_CO2_fitting_ventilation_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_CO2_fitting_ventilation_change();

  // Setup the maximum number of people at page load (to handle back/forward),
  // and update it when total people is changed.
  validateMaxInfectedPeople();
  $("#total_people").change(validateMaxInfectedPeople);
  $("#activity_type").change(validateMaxInfectedPeople);
  $("#infected_people").change(validateMaxInfectedPeople);

  //Validate all non zero values
  $("input[required].non_zero").each(function() {validateValue(this)});
  $(".non_zero").change(function() {validateValue(this)});

  //Validate all finish times
  $("input[required].finish_time").each(function() {validateFinishTime(this)});
  $(".finish_time").change(function() {validateFinishTime(this)});
  $(".start_time").change(function() {validateFinishTime(this)});

  //Validate lunch times
  $(".start_time[data-lunch-for]").each(function() {validateLunchBreak($(this).data('time-group'))});
  $("[data-lunch-for]").change(function() {validateLunchBreak($(this).data('time-group'))});
  $("[data-lunch-break]").change(function() {validateLunchBreak($(this).data('lunch-break'))});

  $("#location_select").select2({
    ajax: {
      // Docs for the geocoding service at:
      // https://developers.arcgis.com/rest/geocode/api-reference/geocoding-service-output.htm
      url: "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/suggest",
      dataType: 'json',
      delay: 250,
      data: function(params) {
        return {
          text: params.term, // search term
          f: 'json',
          page: params.page,
          maxSuggestions: 20,
        };
      },
      processResults: function(data, params) {
        // Enable infinite scrolling
        params.page = params.page || 1;
        return {
          results: data.suggestions.map(function(suggestion) {
            return {
                id: suggestion.magicKey,  // The unique reference to this result.
                text: suggestion.text,
                magicKey: suggestion.magicKey
            }
          }),
          pagination: {
            more: (params.page * 10) < data.suggestions.length
          }
        };
      },
      cache: true
    },
    placeholder: 'Geneva, CHE',
    minimumInputLength: 1,
    templateResult: formatlocation,
    templateSelection: formatLocationSelection
  });

  function formatlocation(suggestedLocation) {
    // Function is called for each location from the geocoding API.

    if (suggestedLocation.loading) {
      // Update the first message in the search results to show the
      // "Searching..." message.
      return suggestedLocation.text;
    }

    // Create a container for this location (to be added to the DOM by the select2
    // library when returned).
    // This will become one of many search results in the dropdown.
    var $container = $(
      "<div class='select2-result-location clearfix'>" +
      "<div class='select2-result-location__meta'>" +
      "<div class='select2-result-location__title'>" + suggestedLocation.text + "</div>" +
      "</div>" +
      "</div>"
    );
    return $container;
  }

  function formatLocationSelection(selectedSuggestion) {
    // Function is called when a selection is made in the search result dropdown.

    // ID may be empty, for example when the page is refreshed or back button pressed.
    if (selectedSuggestion.id != "") {

        // Turn the suggestion into a proper location (so that we can get its latitude & longitude).
        $.ajax({
          dataType: "json",
          url: 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates',
          data: {
            magicKey: selectedSuggestion.magicKey,
            outFields: 'country, location',
            f: "json"
          },
          success: function (locations) {
            // If there isn't precisely one result something is very wrong.
            geocoded_loc = locations.candidates[0];
            
            $('input[name="location_name"]').val(selectedSuggestion.text);
            $('input[name="location_latitude"]').val(geocoded_loc.location.y.toPrecision(7));
            $('input[name="location_longitude"]').val(geocoded_loc.location.x.toPrecision(7));
            // Update geographic_cases
            geographic_cases(geocoded_loc.attributes['country']);
          }
        });

    } else if ($('input[name="location_name"]').val() != "") {
        // If we have no selection AND the location_name is available, use that in the search bar.
        // This means that we preserve the location through refresh/back button.
        return $('input[name="location_name"]').val();
    }
    return selectedSuggestion.text;
  }

  function inject_sr_interaction(index, value, is_validated) {
    return `<div class="col-md-12 form_field_outer p-0">
      <div class="form_field_outer_row ${is_validated} split">

          <div class='form-group row'>
            <div class="col-sm-4"><label class="col-form-label col-form-label-sm"> Expiration: </label><br></div>
            <div class="col-sm-8"><select id="sr_expiration_no_${index}" name="short_range_expiration" class="form-control form-control-sm" onchange="validate_sr_parameter(this)" form="not-submitted">
              <option value="" selected disabled>Select type</option>
              <option value="Breathing">Breathing</option>
              <option value="Speaking">Speaking</option>
              <option value="Shouting">Shouting/Singing</option>
            </select><br>
            </div>
          </div>
            
          <div class='form-group row'>
            <div class="col-sm-4"><label class="col-form-label col-form-label-sm"> Start: </label></div>
            <div class="col-sm-8"><input type="time" class="form-control form-control-sm short_range_option" name="short_range_start_time" id="sr_start_no_${index}" value="${value.start_time}" onchange="validate_sr_time(this)" form="not-submitted"><br></div>
          </div>
        
          <div class='form-group row'>
            <div class="col-sm-6"><label class="col-form-label col-form-label-sm"> Duration (min):</label></div>
            <div class="col-sm-6"><input type="number" id="sr_duration_no_${index}" value="${value.duration}" class="form-control form-control-sm short_range_option" name="short_range_duration" min=1 placeholder="Minutes" onchange="validate_sr_time(this)" form="not-submitted"><br></div>
          </div>

          <div class="form-group" style="max-width: 8rem">
            <button type="button" id="edit_row_no_${index}" class="edit_node_btn_frm_field btn btn-success btn-sm d-none">Edit</button>
            <button type="button" id="validate_row_no_${index}" class="validate_node_btn_frm_field btn btn-success btn-sm">Save</button>
            <button type="button" class="remove_node_btn_frm_field btn btn-danger btn-sm">Delete</button>
          </div>
        </div>
    </div>`
  }

  // Add one empty row if none.
  $("#set_interactions_button").on("click", e => {
    if ($(".form_field_outer").find(".form_field_outer_row").length == 0) $(".add_node_btn_frm_field").click();
  });

  // When short_range_yes option is selected, we want to inject rows for each expiractory activity, start_time and duration.
  $("body").on("click", ".add_node_btn_frm_field", function(e) {
    let last_row = $(".form_field_outer").find(".form_field_outer_row");
    if (last_row.length == 0) $("#dialog_sr").append(inject_sr_interaction(1, value = { activity: "", start_time: "", duration: "15" }));
    else {
        last_index = last_row.last().find(".short_range_option").prop("id").split("_").slice(-1)[0];
        index = parseInt(last_index) + 1;
        $("#dialog_sr").append(inject_sr_interaction(index, value = { activity: "", start_time: "", duration: "15" }));
    }
  });

  // Validate row button (Save button)
  $("body").on("click", ".validate_node_btn_frm_field", function() {
    var index = $(this).attr('id').split('_').slice(-1)[0];
    let activity = validate_sr_parameter('#sr_expiration_no_' + String(index)[0], "Required input.");
    let start = validate_sr_parameter('#sr_start_no_' + String(index)[0], "Required input.");
    let duration = validate_sr_parameter('#sr_duration_no_' + String(index)[0], "Required input.");
    let total_people = validate_sr_people('#short_range_occupants');
    if (activity && start && duration && total_people) {
      if (validate_sr_time('#sr_start_no_' + String(index)) && validate_sr_time('#sr_duration_no_' + String(index))) {
        document.getElementById('sr_expiration_no_' + String(index)).disabled = true;
        document.getElementById('sr_start_no_' + String(index)).disabled = true;
        document.getElementById('sr_duration_no_' + String(index)).disabled = true;
        document.getElementById('edit_row_no_' + String(index)).style.cssText = 'display:inline !important';
        $(this).closest(".form_field_outer_row").addClass("row_validated");
        $(this).hide();
        index = index + 1;
      }
    }
    // On save, check open/unvalidated rows.
    $(".validate_node_btn_frm_field").not(".row_validated").not(this).each(function( index ) {
      index = $(this).attr('id').split('_').slice(-1)[0];
      if ($('#sr_start_no_' + String(index)[0]).val() != "") {
        validate_sr_parameter('#sr_start_no_' + String(index)[0], "Required input.")
        validate_sr_time('#sr_start_no_' + String(index));
      };
      if ($('#sr_duration_no_' + String(index)[0]).val() != "") {
        validate_sr_parameter('#sr_duration_no_' + String(index)[0], "Required input.");
        validate_sr_time('#sr_duration_no_' + String(index));
      }
    });
  });

  //Edit short-range activity type
  $("body").on("click", ".edit_node_btn_frm_field", function() {
    $(this).closest(".form_field_outer_row").removeClass("row_validated");
    $(this).hide();
    let id = $(this).attr('id').split('_').slice(-1)[0];
    document.getElementById('sr_expiration_no_' + String(id)).disabled = false;
    document.getElementById('sr_start_no_' + String(id)).disabled = false;
    document.getElementById('sr_duration_no_' + String(id)).disabled = false;
    document.getElementById('validate_row_no_' + String(id)).style.cssText = 'display:inline !important';
  })

  //Remove short-range interaction (modal field row).
  $("body").on("click", ".remove_node_btn_frm_field", function() {
    $(this).closest(".form_field_outer_row").remove();
    // On delete, check open/unvalidated rows.
    $(".validate_node_btn_frm_field").not(".row_validated").not(this).each(function( index ) {
      index = $(this).attr('id').split('_').slice(-1)[0];
      if ($('#sr_start_no_' + String(index)[0]).val() != "") {
        validate_sr_parameter('#sr_start_no_' + String(index)[0], "Required input.")
        validate_sr_time('#sr_start_no_' + String(index));
      };
      if ($('#sr_duration_no_' + String(index)[0]).val() != "") {
        validate_sr_parameter('#sr_duration_no_' + String(index)[0], "Required input.");
        validate_sr_time('#sr_duration_no_' + String(index));
      }
    });
  });

  //Short-range modal - close and save button
  $("body").on("click", ".close_btn_frm_field", function() {
    $(".validate_node_btn_frm_field").click();
    if ($(".form_field_outer").find(".form_field_outer_row.row_validated").length == $(".form_field_outer").find(".form_field_outer_row").length) {
      $("#sr_interactions").text($(".form_field_outer").find(".form_field_outer_row.row_validated").length);
      $(".form_field_outer_row").not(".row_validated").remove();
      $('#short_range_dialog').modal('hide');
    }
  });

  //Short-range modal - reset button
  $("body").on("click", ".dismiss_btn_frm_field", function() {
    $(".form_field_outer_row").remove();
    $("#sr_interactions").text(0);
    $('input[type=radio][id=short_range_no]').prop("checked", true);
    on_short_range_option_change();
  });

});


/* -------Debugging------- */
function debug_submit(form) {

  //Prevent default posting of form - put here to work in case of errors
  event.preventDefault();

  //Serialize the data in the form
  var serializedData = objectifyForm($(form).serializeArray());

  console.log(serializedData);

  return false; //don't submit
}

function objectifyForm(formArray) {
  var returnArray = {};
  for (var i = 0; i < formArray.length; i++)
    returnArray[formArray[i]['name']] = formArray[i]['value'];
  return returnArray;
}

// ------- VACCINATION DATA -------

// From data available in Results of COVID-19 Vaccine Effectiveness
// Studies: An Ongoing Systematic Review - Updated September 8, 2022.
// https://view-hub.org/resources
vaccine_primary_host_immunity = [
  'AZD1222_(AstraZeneca)',
  'AZD1222_(AstraZeneca)_and_BNT162b2_(Pfizer)',
  'AZD1222_(AstraZeneca)_and_any_mRNA_-_heterologous',
  'Ad26.COV2.S_(Janssen)',
  'Any_mRNA_-_heterologous',
  'BBIBP-CorV_(Beijing_CNBG)',
  'BNT162b2_(Pfizer)',
  'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)',
  'CoronaVac_(Sinovac)',
  'CoronaVac_(Sinovac)_and_AZD1222_(AstraZeneca)',
  'CoronaVac_(Sinovac)_and_AZD1222_(AstraZeneca)_-_heterologous',
  'CoronaVac_(Sinovac)_and_BNT162b2_(Pfizer)',
  'Covishield',
  'Sputnik_V_(Gamaleya)',
  'mRNA-1273_(Moderna)',
]

vaccine_booster_host_immunity = [
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'AZD1222_(AstraZeneca)',},
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'BNT162b2_(Pfizer)',},
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)',},
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'mRNA-1273_(Moderna)',},
  {'primary series vaccine': 'Ad26.COV2.S_(Janssen)', 'booster vaccine': 'Ad26.COV2.S_(Janssen)',},
  {'primary series vaccine': 'Ad26.COV2.S_(Janssen)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)',},
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'AZD1222_(AstraZeneca)',},
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'BNT162b2_(Pfizer)',},
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)',},
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'mRNA-1273_(Moderna)',},
  {'primary series vaccine': 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)',},
  {'primary series vaccine': 'BNT162b2_(Pfizer)_(3_doses)', 'booster vaccine': 'BNT162b2_(Pfizer)_(4th_dose)',},
  {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'AZD1222_(AstraZeneca)',},
  {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'BNT162b2_(Pfizer)',},
  {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'CoronaVac_(Sinovac)',},
  {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)',},
  {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)',},
  {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'mRNA-1273_(Moderna)',}
]
