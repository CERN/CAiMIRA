function clear_form(){
    document.covid_calculator.reset();
}

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
  
  if (show.style.display === "none") {
    show.style.display = "block";
    hide.style.display = "none";
  }// else {
   // show.style.display = "none";
  //}

  require_fields(obj);

}

/*$(document).on("click", "input[name='ventilation_type']", function(){
      thisRadio = $(this);
      if (thisRadio.hasClass("imChecked")) {
          thisRadio.removeClass("imChecked");
          thisRadio.prop('checked', false);
      } else { 
          thisRadio.prop('checked', true);
          thisRadio.addClass("imChecked");
      };
  })*/

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
      break;
    case "event_type_recurrent":
      require_single_event(false);
      break;
    case "BUTTON_lunch":
      var button = document.getElementById("lunch_option");
      if (button.value == 0)
        require_lunch(false);
      else if (button.value == 1)
        require_lunch(true);
      break;
    case "BUTTON_coffee":
      var button = document.getElementById("coffee_option");
      if (button.value == 0)
        require_coffee(false);
      else if (button.value == 1)
        require_coffee(true);
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
}

function require_air_changes(option) {
    $("#air_changes").prop('required',option);
}

function require_air_supply(option) {
    $("#air_supply").prop('required',option);
}

function require_single_event(option) {
  $("#datepicker").prop('required',option);
}

function require_lunch(option) {
  $("#lunch_start").prop('required',option);
  $("#lunch_finish").prop('required',option);
}

function require_coffee(option) {
  $("#coffee_breaks").prop('required',option);
}

/* -------UI------- */
$(function() {
  $("#datepicker").datepicker();
});  