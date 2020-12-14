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
    case "room_type_volume":
      require_room_volume(true);
      require_room_dimensions(false);
      break;
    case "room_type_dimensions":
      require_room_volume(false);
      require_room_dimensions(true);
      break;
    case "mechanical":
      require_mechanical_ventilation(true);
      require_natural_ventilation(false);
      break;
    case "natural":
      require_mechanical_ventilation(false);
      require_natural_ventilation(true);
      break;
    case "window_sliding":
      require_window_width(false);
      break;
    case "window_hinged":
      require_window_width(true);
      break;
    case "air_type_changes":
      require_air_changes(true);
      require_air_supply(false);
      break;
    case "air_type_supply":
      require_air_changes(false);
      require_air_supply(true);
      break;
    case "interval":
      require_venting(true);
      break;
    case "always":
      require_venting(false);
      break;
    case "hepa_yes":
      require_hepa(true);
      break;
    case "hepa_no":
      require_hepa(false);
      break;
    case "mask_on":
      require_mask(true);
      break;
    case "mask_off":
      require_mask(false);
      break;
    case "event_type_single":
      require_single_event(true);
      require_recurrent_event(false);
      break;
    case "event_type_recurrent":
      require_recurrent_event(true);
      require_single_event(false);
      break;
    case "lunch_option_no":
      require_lunch(false);
      break;
    case "lunch_option_yes":
      require_lunch(true);
      break;
    default:
      break;
  }
}

function unrequire_fields(obj) {
  switch (obj.id) {
    case "mechanical":
      require_mechanical_ventilation(false);
      break;
    case "natural":
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
  $("#air_type_changes").prop('required', option);
  $("#air_type_supply").prop('required', option);
  if (!option) {
    removeInvalid("#air_changes");
    removeInvalid("#air_supply");
  }
}

function require_natural_ventilation(option) {
  require_input_field("#windows_number", option);
  require_input_field("#window_height", option);
  require_input_field("#opening_distance", option);
  $("#window_sliding").prop('required', option);
  $("#window_hinged").prop('required', option);
  $("#always").prop('required', option);
  $("#interval").prop('required', option);
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
  set_disabled_status("#windows_duration", !option);
  set_disabled_status("#windows_frequency", !option);
}

function require_single_event(option) {
  require_input_field("#single_event_date", option);
  set_disabled_status("#single_event_date", !option);
}

function require_recurrent_event(option) {
  $("#recurrent_event_month").prop('required', option);
  set_disabled_status("#recurrent_event_month", !option);
}

function require_lunch(option) {
  $("#lunch_start").prop('required', option);
  $("#lunch_finish").prop('required', option);

  var lunchStartObj = document.getElementById("lunch_start");
  var lunchFinishObj = document.getElementById("lunch_finish");
  if (option) {
    if (lunchStartObj.value === "") {
      lunchStartObj.value = "12:30";
    }
    if (lunchFinishObj.value === "") {
      lunchFinishObj.value = "13:30";
    }
  } 
  else {
    lunchStartObj.value = "";
    lunchFinishObj.value = "";
    $("#lunch_finish").removeClass("red_border finish_time_error lunch_break_error");
    $("#lunch_finish").removeClass("red_border finish_time_error lunch_break_error");
    removeErrorFor(lunchFinishObj);
  }
}

function require_mask(option) {
  $("#mask_type1").prop('required', option);
  $("#mask_ffp2").prop('required', option);
}

function require_hepa(option) {
  require_input_field("#hepa_amount", option);
  set_disabled_status("#hepa_amount", !option);
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

function setMaxInfectedPeople() {
  $("#training_limit_error").hide();
  var max = $("#total_people").val()

  if ($("#activity_type").val() === "training") {
    max = 1;
    $("#training_limit_error").show();
  }

  $("#infected_people").attr("max", max);
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

      // Clear inputs for this newly hidden child element.
      getChildElement($(this)).find('input').not('input[type=radio]').val('');
    }
  });
}

/* -------UI------- */
$(function () {
  $(".datepicker").datepicker({
    dateFormat: 'dd/mm/yy'
  });
});

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

/* -------Form validation------- */
function validate_form(form) {
  var submit = true;

  // Activity times and lunch break times are co-dependent
  // -> So if 1 fails it doesn't make sense to check the rest

  //Validate all finish times
  $("input[required].finish_time").each(function() {
    if (!validateFinishTime(this)) {
      submit = false;
    }
  });

  //Validate all lunch breaks
  if (submit) {
    $("input[required].start_time[data-lunch-for]").each(function() {
      if (!validateLunchBreak($(this).data('time-group'))) {
        submit = false;
      }
    });
  }

  //Validate breaks length < activity length
  if (submit) {
    var activityBreaksObj= document.getElementById("activity_breaks");
    removeErrorFor(activityBreaksObj);

    var lunch_mins = 0;
    if (document.getElementById('lunch_option_yes').checked) {
      var lunch_start = document.getElementById("lunch_start");
      var lunch_finish = document.getElementById("lunch_finish");
      lunch_mins = parseTimeToMins(lunch_finish.value) - parseTimeToMins(lunch_start.value);
    }
    
    var coffee_breaks = parseInt(document.querySelector('input[name="coffee_breaks"]:checked').value);
    var coffee_duration = parseInt(document.getElementById("break_duration").value);
    var coffee_mins = coffee_breaks * coffee_duration;
    
    var activity_start = document.getElementById("activity_start");
    var activity_finish = document.getElementById("activity_finish");
    var activity_mins = parseTimeToMins(activity_finish.value) - parseTimeToMins(activity_start.value);

    if ((lunch_mins + coffee_mins) >= activity_mins) {
      insertErrorFor(activityBreaksObj, "Length of breaks >= Length of activity");
      submit = false;
    }
  }

  //Validate all non zero values
  $("input[required].non_zero").each(function() {
    if (!validateValue(this)) {
      submit = false;
    }
  });

  //Validate all dates
  $("input[required].datepicker").each(function() {
    if (!validateDate(this)) {
      submit = false;
    }
  });

  //Validate window venting duration < venting frequency
  if (!$("#windows_duration").hasClass("disabled")) {
    var windowsDurationObj = document.getElementById("windows_duration");
    var windowsFrequencyObj = document.getElementById("windows_frequency");
    removeErrorFor(windowsFrequencyObj);

    if (parseInt(windowsDurationObj.value) >= parseInt(windowsFrequencyObj.value)) {
      insertErrorFor(windowsFrequencyObj, "Duration >= Frequency");
      submit = false;
    }
  }

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
  var lunchStartObj = $(".start_time[data-time-group='"+lunchGroup+"']")[0];
  var lunchFinishObj = $(".finish_time[data-time-group='"+lunchGroup+"']")[0];

  //Skip if finish time error present (it takes precedence over lunch break error)
  if ($(lunchStartObj).hasClass("finish_time_error") || $(lunchFinishObj).hasClass("finish_time_error"))
    return false;

  removeErrorFor(lunchFinishObj);
  var valid = validateLunchTime(lunchStartObj) & validateLunchTime(lunchFinishObj);
  if (!valid) {
    insertErrorFor(lunchFinishObj, "Lunch break must be within activity times");
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

function parseValToNumber(val) {
  return parseInt(val.replace(':',''), 10);
}

function parseTimeToMins(cTime) {
  var time = cTime.match(/(\d+):(\d+)/);
  return parseInt(time[1]*60) + parseInt(time[2]);
}

/* -------On Load------- */
$(document).ready(function () {
  // When the document is ready, deal with the fact that we may be here
  // as a result of a forward/back browser action. If that is the case, update
  // the visibility of some of our inputs.

  // When the ventilation_type changes we want to make its respective
  // children show/hide.
  $("input[type=radio][name=ventilation_type]").change(on_ventilation_type_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_ventilation_type_change();

  //Check all radio buttons previously selected
  $("input[type=radio]:checked").each(function() {require_fields(this)});

  // Setup the maximum number of people at page load (to handle back/forward),
  // and update it when total people is changed.
  setMaxInfectedPeople();
  $("#total_people").change(setMaxInfectedPeople);
  $("#activity_type").change(setMaxInfectedPeople);

  //Validate all non zero values
  $("input[required].non_zero").each(function() {validateValue(this)});
  $(".non_zero").change(function() {validateValue(this)});

  //Validate all dates
  $("input[required].datepicker").each(function() {validateDate(this)});
  $(".datepicker").change(function() {validateDate(this)});

  //Validate all finish times
  $("input[required].finish_time").each(function() {validateFinishTime(this)});
  $(".finish_time").change(function() {validateFinishTime(this)});
  $(".start_time").change(function() {validateFinishTime(this)});

  //Validate lunch times
  $(".start_time[data-lunch-for]").each(function() {validateLunchBreak($(this).data('time-group'))});
  $("[data-lunch-for]").change(function() {validateLunchBreak($(this).data('time-group'))});
  $("[data-lunch-break]").change(function() {validateLunchBreak($(this).data('lunch-break'))});
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