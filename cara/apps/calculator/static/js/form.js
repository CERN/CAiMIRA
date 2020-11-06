/* -------Show/Hide DIVs------- */
function show(show, var_id, obj) {
  var show = document.getElementById(show);
  if (show.style.display === "none") {
    show.style.display = "block";
    document.getElementById(var_id).value = 1;
  } else {
    show.style.display = "none";
    document.getElementById(var_id).value = 0; 
  }
  require_fields(obj);
}

function show_hide(show, hide, obj) {
  var show = document.getElementById(show);
  var hide = document.getElementById(hide);
  var ventilation_type = document.getElementById("ventilation_type");
  var mechanical_ventilation_type = document.getElementById("mechanical_ventilation_type");

  if (show.style.display === "block") {
      show.style.display = "none";
      obj.checked = false;
      ventilation_type.value = "";
      mechanical_ventilation_type.value = "";
      unrequire_fields(obj);
  } else if (show.style.display === "none") {
      show.style.display = "block";
      hide.style.display = "none";
      ventilation_type.value = obj.id;
      require_fields(obj);
} }

function update_windows_open(obj) {
  var windows_open = document.getElementById("windows_open");
  windows_open.value = obj.id;
}

/* -------Required fields------- */
function require_fields(obj){
  switch(obj.id) {
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
} }

function unrequire_fields(obj){
  switch(obj.id) {
    case "mechanical":
      require_mechanical_ventilation(false);
      break;
    case "natural":
      require_natural_ventilation(false);
      break;
    default:
      break;
} }

function require_room_volume(option) {
  $("#room_volume").prop('required',option);
}

function require_room_dimensions(option) {
  $("#floor_area").prop('required',option);
  $("#ceiling_height").prop('required',option);
}

function require_mechanical_ventilation(option) {
  $("#air_type_changes").prop('required',option);
  $("#air_type_supply").prop('required',option);
  }

function require_natural_ventilation(option) {
  $("#windows_number").prop('required',option);
  $("#window_height").prop('required',option);
  $("#window_width").prop('required',option);
  $("#opening_distance").prop('required',option);
  $("#always").prop('required',option);
  $("#interval").prop('required',option);
  $("#event_type_single").prop('required',option);
  $("#event_type_recurrent").prop('required',option);
}

function require_air_changes(option) {
  $("#air_changes").prop('required',option);
  if (option) {
    var mechanical_ventilation_type = document.getElementById("mechanical_ventilation_type");
    mechanical_ventilation_type.value = "air_changes";
} }

function require_air_supply(option) {
  $("#air_supply").prop('required',option);
  if (option) {
    var mechanical_ventilation_type = document.getElementById("mechanical_ventilation_type");
    mechanical_ventilation_type.value = "air_supply";
} }

function require_single_event(option) {
  $("#single_event_date").prop('required',option);
}

function require_recurrent_event(option) {
  $("#recurrent_event_month").prop('required',option);
}

function require_lunch(option) {
  $("#lunch_start").prop('required',option);
  $("#lunch_finish").prop('required',option);
}

function setMaxInfectedPeople(){
  $("#infected_people").attr("max", $("#total_people").val());
}

/* -------UI------- */
$(function() {
  $(".datepicker").datepicker({
    dateFormat: 'mm/dd/yy'});
});

$( function() {
  $(".dialog").dialog({modal:true});
});

function show_disclaimer() {
  var dots = document.getElementById("dots");
  var moreText = document.getElementById("more");
  var btnText = document.getElementById("myBtn");

  if (dots.style.display === "none") {
    dots.style.display = "inline";
    btnText.innerHTML = "Read more";
    moreText.style.display = "none";
    $("#DIALOG_welcome").dialog("option", "height", 185);
  } else {
    dots.style.display = "none";
    btnText.innerHTML = "Read less";
    moreText.style.display = "inline";
    $("#DIALOG_welcome").dialog("option", "height", 600);
} }

/* -------Form validation------- */
function validate_form(form) {

  var submit = true;

  //Validate all dates
  $("input[required].datepicker").each(function() {
    $(this).removeClass("red");

    var fromDate = $(this).val();
    if (!isValidDate(fromDate)) {
      $(this).addClass("red");
      submit = false;
  } }); 

  return submit;
}

function isValidDate(date) {
  var matches = /^(\d+)[-\/](\d+)[-\/](\d+)$/.exec(date);
  if (matches == null) return false;
  var d = matches[2];
  var m = matches[1];
  var y = matches[3];
  if (y > 2100 || y < 1900) return false; 
  var composedDate = new Date(y+'/'+m+'/'+d);
  return composedDate.getDate() == d && composedDate.getMonth()+1 == m && composedDate.getFullYear() == y;
}

/* -------Debugging------- */
function debug_submit(form){

  //Prevent default posting of form - put here to work in case of errors
  event.preventDefault();

  //Serialize the data in the form
  var serializedData = objectifyForm($(form).serializeArray());

  console.log( serializedData );
  return false; //don't submit
}

function objectifyForm(formArray) {
    var returnArray = {};
    for (var i = 0; i < formArray.length; i++)
        returnArray[formArray[i]['name']] = formArray[i]['value'];
    return returnArray;
}

$(document).ready(function() {
  // Setup the maximum number of people at page load (to handle back/forward),
  // and update it when total people is changed.
  setMaxInfectedPeople();
  $("#total_people").change(setMaxInfectedPeople);

  var radioValue = $("input[name='event_type']:checked");
  if(radioValue.val()){
    require_fields(radioValue.get(0));
  }
})
