var socket = io.connect('http://' + document.domain + ':' + location.port);

function init(){
  $('.weather-days').html('');
  $('#current_date').html('<div class="day">'+ dateInfo('dayS')+'</div> <div class="date">'+ dateInfo('dayN')+'/'+dateInfo('monthS')+'</div>')
}
init();


//---------------------------------------------------- back backInfo
socket.emit( 'back_message_info_order', { msg: 'msg: ' })

socket.on('back_message_info', function(msg){
  $('#back_message_info').html(msg)
})


/////////////////////////////////////////////////////////////////

// ---------------------------------------------------- Default Get the Weather for this Machine
// get the IP address for the current Machine
$.get('https://ipapi.co/json/', function(data) {
  //call weather_current_location function
  console.log(data)
  socket.emit( 'weather_current_location', { postal: data.postal, country: data.country })
})
socket.on( 'back_weather_current_location', function( msg ) {
  //create the current weather block
  setCurrentWeather(msg);
});
socket.on( 'back_weather_current_location_5', function( msg ) {
  //create the 5 weather days blocks
  set5daysWeather(msg);
});
/////////////////////////////////////////////////////////////////

// --------------------------------------------------- Search about a Weather City
// form to find city's wether
var form = $( '#form_find_weather' ).on( 'submit', function( e ) {
    init() // to remove the weather-days html
    e.preventDefault()// stop default form executed
    let cityname = $( '.cityname' ).val() // get the input text
    socket.emit( 'geCitytweather', { city: cityname }) // pass the text value to server
    $( 'input.cityname' ).val( '' ).focus()// set the cruiser on the city input
})
// get the get current weather response
// this get the response from app.py, get an object
socket.on( 'back_currentCityWeather', function( msg ) {
  console.log(msg)
  //create the current weather block
  setCurrentWeather(msg);
})
// get the weather for the next 5 days
socket.on( 'back_currentCity5DaysWeather', function( msg ) {
    //console.log(msg.list[0]);
    set5daysWeather(msg);
});
////////////////////////////////////////////////////////////////////

//*************************************************************
// Global Function
// ******************

// rebuilding the Current weather day
function setCurrentWeather(msg){
  console.log(msg);
  $('#current_tempr').html(''+
    '<div id="city_name" class="location"> '+msg.name+'</div>'+
    '<div id="current_tempr" class="degree">'+
      '<div  class="num">'+Math.round(msg.temp)+'<sup>o</sup>C</div>'+
      '<div class="forecast-icon">'+
        '<img src="../static/images/icons/'+msg.icon+'.svg" alt="" width=90>'+
      '</div>'+
    '</div>'+
    '<span><img src="../static/images/icon-umberella.png" alt="">'+msg.humidity+'%</span>'+
    '<span><img src="../static/images/icon-wind.png" alt="">'+msg.speed+'km/h</span>'+
    '<span><img src="../static/images/icon-compass.png" alt="">'+toTextualDescription(msg.deg)+'</span>'
    );
}

// insert html weather 5 days in .weather-days div by insertAdjacentHTML function
function set5daysWeather(msg){
    // the wether card
    console.log(msg);
    var w_cart ='<div class="forecast" style="width: 194px;">'+
                  '<div class="forecast-header">'+
                    '<div class="day">%day%</div>'+
                  '</div> '+
                  '<div class="forecast-content">'+
                    '<div class="forecast-icon">'+
                      '<img src="../static/images/icons/%icon%.svg" alt="" width=48>'+
                    '</div>'+
                    '<div class="degree">%tempr%<sup>o</sup>C</div>'+
                  '</div>'+
                '</div>';
    // to insert the w_cart(html) in the div class .weather-days after replace the data
    var day = 1;
    $.each(msg.list, function(i, val) {
      if(val['dt_txt'].includes("12:00:00")){
        var newHtml = w_cart.replace('%day%', dateInfo('dayS',day));
        newHtml = newHtml.replace('%icon%', val['weather'][0]['icon']);
        newHtml = newHtml.replace('%tempr%', Math.round(val['main']['temp']));
        console.log(val['weather'][0]['description'])
        document.querySelector('.weather-days').insertAdjacentHTML('beforeend', newHtml);
        day++;
      }
    });
}

/*
'dayN' = number of the day, 'dayS' = day name
'monthN' = number of the month, 'monthS' = month Name
add: by default is 0, to get date of tomorrow or more
*///return date with names and numbers
function dateInfo(txt, add=0){
  var now = new Date();
  var weekday = now.getDay();

  months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'December'];
  week_days = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag','Montag', 'Dienstag', 'Mittwoch'];
  switch (txt) {
    case 'dayN':
      return now.getDate();
      break;
    case 'dayS':
        //var options = { weekday: 'long'};
        //return new Intl.DateTimeFormat('de-DE', options).format(now); // to get current day's name
        return week_days[weekday+add]
      break;
    case 'monthN':
      return now.getMonth()+add;
      break;
    case 'monthS':
      return months[now.getMonth()+add];
      break;
    default:
  }
}

// to convert the Wind direction from numbers to string
function  toTextualDescription(deg){
  if (deg>337.5) return 'Nördlich';
  if (deg>292.5) return 'Nordwestlich';
  if(deg>247.5) return 'Westlich';
  if(deg>202.5) return 'Südwestlich';
  if(deg>157.5) return 'südlich';
  if(deg>122.5) return 'Südöstlich';
  if(deg>67.5) return 'Ostern';
  if(deg>22.5){return 'Nordöstliches';}
  return 'Nördlich';
}


//*************************************************************








//
