function on_ventilation_type_change() {
  ventilation_types = $('input[type=radio][name=ventilation_type]');
  ventilation_types.each(function (index) {
    if (this.checked) {
      getChildElement($(this)).show();
      require_fields(this);
    } else {
      getChildElement($(this)).hide();
      unrequire_fields(this);
      // Clear the inputs for this newly hidden child element.
      getChildElement($(this)).find('input').not('input[type=radio]').val('');
      getChildElement($(this)).find('input[type=radio]').prop("checked", false);
      getChildElement($(this)).find('input').prop("required", false);
    }
  });
}


function getChildElement(elem) {
  // Get the element named in the given element's data-enables attribute.
  return $("#" + elem.data("enables"));
}


/* -------Required fields------- */
function require_fields(obj) {
  switch (obj.id) {
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
    case "air_type_changes":
      require_air_changes(true);
      require_air_supply(false);
      break;
    case "air_type_supply":
      require_air_changes(false);
      require_air_supply(true);
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
  $("#room_volume").prop('required', option);
}

function require_room_dimensions(option) {
  $("#floor_area").prop('required', option);
  $("#ceiling_height").prop('required', option);
}

function require_mechanical_ventilation(option) {
  $("#air_type_changes").prop('required', option);
  $("#air_type_supply").prop('required', option);
}

function require_natural_ventilation(option) {
  $("#windows_number").prop('required', option);
  $("#window_height").prop('required', option);
  $("#window_width").prop('required', option);
  $("#opening_distance").prop('required', option);
  $("#always").prop('required', option);
  $("#interval").prop('required', option);
}

function require_air_changes(option) {
  $("#air_changes").prop('required', option);
}

function require_air_supply(option) {
  $("#air_supply").prop('required', option);
}

function require_single_event(option) {
  $("#single_event_date").prop('required', option);
}

function require_recurrent_event(option) {
  $("#recurrent_event_month").prop('required', option);
}

function require_lunch(option) {
  $("#lunch_start").prop('required', option);
  $("#lunch_finish").prop('required', option);
}

function setMaxInfectedPeople() {
  $("#infected_people").attr("max", $("#total_people").val());
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

/* -------Form validation------- */
function validate_form(form) {

  var submit = true;

  //Validate all dates
  $("input[required].datepicker").each(function () {
    $(this).removeClass("red_border");
    $(this).next().hide();

    var fromDate = $(this).val();
    if (!isValidDate(fromDate)) {
      $(this).addClass("red_border");
      submit = false;
      $(this).next().show();
    }
  });

  //Validate all times
  $("input[required].finish_time").each(function () {
    $(this).removeClass("red_border");
    $(this).next().hide();

    var startTime = parseValToNumber($(this).prev());
    var finishTime = parseValToNumber($(this));
    if (startTime > finishTime) {
      $(this).addClass("red_border");
      submit = false;
      $(this).next().show();
    }
  });

  return submit;
}

function isValidDate(date) {
  var matches = /^(\d+)[-\/](\d+)[-\/](\d+)$/.exec(date);
  if (matches == null) return false;
  var d = matches[1];
  var m = matches[2];
  var y = matches[3];
  if (y > 2100 || y < 1900) return false;
  var composedDate = new Date(y + '/' + m + '/' + d);
  return composedDate.getDate() == d && composedDate.getMonth() + 1 == m && composedDate.getFullYear() == y;
}

function parseValToNumber(obj) {
    return parseInt(obj.val().replace(':',''), 10);
}

/* ------ On Load ---------- */

$(document).ready(function () {
  // When the document is ready, deal with the fact that we may be here
  // as a result of a forward/back browser action. If that is the case, update
  // the visibility of some of our inputs.

  // When the ventilation_type changes we want to make its respective
  // children show/hide.
  ventilation_types = $("input[type=radio][name=ventilation_type]");
  ventilation_types.change(on_ventilation_type_change);
  // Call the function now to handle forward/back button presses in the browser.
  on_ventilation_type_change();

  $("input[name=mechanical_ventilation_type]").change(function () {
    console.log('Changed!');
  })

  // Setup the maximum number of people at page load (to handle back/forward),
  // and update it when total people is changed.
  setMaxInfectedPeople();
  $("#total_people").change(setMaxInfectedPeople);

  var radioValue = $("input[name='event_type']:checked");
  if (radioValue.val()) {
    require_fields(radioValue.get(0));
  }

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