var directionsDisplay, directionsService, map;
    var locations = [];

    function initialize() {
        var directionsService = new google.maps.DirectionsService();
        directionsDisplay = new google.maps.DirectionsRenderer();
        var chicago = new google.maps.LatLng(22.851787151520107, 79.1795339339829);
        var mapOptions = { zoom:7, mapTypeId: google.maps.MapTypeId.ROADMAP, center: chicago }
        map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);
        directionsDisplay.setMap(map);
    }
var marker;
var markersArray = [];

function addMarker(locations, contentString) {
    if (marker && marker.setMap) {
        marker.setMap(null);
    }
    var infowindow = new google.maps.InfoWindow();
    var icons = {
        1: {
            icon: '/themes/custom/jiobp/assets/images/icons/map-locator-pin.svg'
        },
        2: {
            icon: '/themes/custom/jiobp/assets/images/icons/map-locator-pin.svg'
        },
        3: {
            icon: '/themes/custom/jiobp/assets/images/icons/map-locator-pin.svg'
        },
        4: {
            icon: '/themes/custom/jiobp/assets/images/icons/map-locator-pin.svg'
        }
    };
    var i;
    for (i = 0; i < locations.length; i++) {

        marker = new google.maps.Marker({
            position: new google.maps.LatLng(locations[i][0], locations[i][1]),
            animation: google.maps.Animation.DROP,
            map: map,
            icon: icons[locations[i][2]].icon,
        });

        markersArray.push(marker);
        map.setCenter(new google.maps.LatLng(locations[i][0], locations[i][1]));
        map.setZoom(9);

        google.maps.event.addListener(marker, 'click', (function (marker, i) {
            return function () {
                //infowindow.setContent('<div class="addrssmap"><h4>' + locations[i][4] + '<p></h4>' + locations[i][3] + '</p></div>');
                  infowindow.setContent('<h5 class="map_pop_title">' + locations[i][4] + '</h5><p class="map_pop_text">' + locations[i][3] + '</p><a href="javascript:getlatlong('+ locations[i][0] + ',' + locations[i][1] + ');" class="btn map_pop_btn">Get Direction</a>');
                infowindow.open(map, marker);
            }
        })(marker, i));
    }
}

function getlatlong(lat, lon) {
    window.open(
        'https://maps.google.com/?q=' + lat + ',' + lon,
        '_blank'
    );

}
    initialize();
    data3 = [];
    fuelData = [];
    var xhr = new XMLHttpRequest();
    xhr.withCredentials = true;

    xhr.addEventListener("readystatechange", function() {

    if(this.readyState === 4) {
        res = JSON.parse(this.responseText);
//console.log(res);
//res= this.responseText;
            fuelLocation = res.RO_Details;
            var State = [];
        var newLocations = [];
            for (i = 0; i < fuelLocation.length; i++) {
            if (fuelLocation[i].latitude != 0 && fuelLocation[i].longitude != 0) {
                var str = {
                    "name": fuelLocation[i].Roname,
                    "state": fuelLocation[i].State,
                    "city": fuelLocation[i].City,
                    "address": fuelLocation[i].Roaddress1,
                    "lattitude": fuelLocation[i].latitude,
                    "longitude": fuelLocation[i].longitude,
                    "type": 1,
                    "pincode": fuelLocation[i].Ropincode,
                    "rocode": fuelLocation[i].Rocode,
                    "roid": fuelLocation[i].Roid,
                    // "Dealername": fuelLocation[i].Dealername,
                    // "Dealerphone": fuelLocation[i].Dealerphone,
                    "Territory": fuelLocation[i].Territory
                    }
                    newLocations.push(str);
                    State.push(fuelLocation[i].State);
                }
            }
            data3 = newLocations;
        let unique = State.filter((item, i, ar) => ar.indexOf(item) === i);
        unique = unique.sort();
        var s_html = '<option selected value="" class="im">Enter State</option>';
        for (i = 0; i < unique.length; i++) {
            s_html += '<option value="' + unique[i] + '">' + unique[i] + '</option>';
        }
        document.getElementById("stateSelect").innerHTML = s_html;
        //console.clear();
        }
    });
    //xhr.open("GET", "/themes/custom/jiobp/fuel-data-json/LocationAPIOutput.txt");
    //xhr.open("GET", "/themes/custom/jiobp/fuel-data-json/rdata.txt");
xhr.open("POST", "/locatorapi.php")
    xhr.send();


    var fuelPriceLoc = [];

    /*var xhr = new XMLHttpRequest();
    xhr.withCredentials = true;

    xhr.addEventListener("readystatechange", function() {
    if(this.readyState === 4) {
        res = JSON.parse(this.responseText);
        fuelPrice = res.RODetail
        var fuelPriceLoc = [];
        for (i = 0; i < fuelPrice.length; i++) {
            var str = {
                "rocode": fuelPrice[i].ROCode, "roid": fuelPrice[i].ROID, "Product": fuelPrice[i].Product, "Price": fuelPrice[i].Price, "date": fuelPrice[i].DTStartDate
            }
            fuelPriceLoc.push(str);
        }
        fuelData = fuelPriceLoc
    }
    });
    xhr.open("GET", "/themes/custom/jiobp/fuel-data-json/PriceAPIOutput.txt");
    xhr.send();*/


    function getCity()
    {
        d = document.getElementById("stateSelect").value;
        City = [];
        for (i = 0; i < data3.length; i++) {
            if(d == data3[i].state && data3[i].city != '')
            {
                City.push(data3[i].city);
            }
        }
        var s_html = '<option selected value="">Enter City</option>';
        let Cityunique = City.filter((item, i, ar) => ar.indexOf(item) === i);
        Cityunique = Cityunique.sort();
        for (i = 0; i < Cityunique.length; i++) {
            s_html += '<option value="' + Cityunique[i] + '">' + Cityunique[i] + '</option>';
        }
        document.getElementById("citySelect").innerHTML = s_html;
    }

    //data3 = JSON.parse(data3);
    //fuelData = JSON.parse(fuelData);
    var resultBtn = document.querySelector(".show_result");
    var reset_btn = document.querySelector(".reset_btn");
    var form__results = document.querySelector(".form__results");
    var form__inputs = document.querySelector(".form__inputs");
    var stateSelect = document.querySelector("#stateSelect");
    var citySelect = document.querySelector("#citySelect");
    var form_locator = document.querySelector("#form_locator");
    var form__resetSec = document.querySelector(".form__resetSec");

    resultBtn.addEventListener("click", function () {

	if (citySelect.value == "" && stateSelect.value == "" && form_locator.value == "") {
		alert('Please select state & city or enter a pincode.');
	}
	if (citySelect.value !== "" && stateSelect.value !== "") {
		if (form_locator.value == "") 
		{
            var data_html = '';
			var fuelPriceLoc = [];
			
			
			for(var i = 0; i < data3.length; i++)
            {
                if(stateSelect.value == data3[i].state && citySelect.value == data3[i].city)
                {
					var xhr = new XMLHttpRequest();
					xhr.withCredentials = true;

					var data = new FormData();
					data.append("roid", data3[i].roid);
					xhr.addEventListener("readystatechange", function() {
						if(this.readyState === 4) {
							res = JSON.parse(this.responseText);
							fuelPrice = res.RODetail;
							fuelResponseFlag = res.Response.ResponseFlag;
							if(fuelResponseFlag == 'S')
							{
								for (i = 0; i < fuelPrice.length; i++) {
									var str = {
										"rocode": fuelPrice[i].ROCode, "roid": fuelPrice[i].ROID, "DTStartDate": fuelPrice[i].DTStartDate, "Product": fuelPrice[i].Product, "Price": fuelPrice[i].Price, "date": fuelPrice[i].DTStartDate
									}
									fuelPriceLoc.push(str);
								}
							}							
							fuelData = fuelPriceLoc;
					}
					});
					xhr.open("POST", "/PriceAPIOutput.php");
					xhr.send(data);
				}
			}
			
			
			
			
			setTimeout(function(){
			
			console.log(fuelData);
            for(var i = 0; i < data3.length; i++)
            {
                if(stateSelect.value == data3[i].state && citySelect.value == data3[i].city)
                {
                    var Roname = data3[i].name;
                    var State = data3[i].state;
                    var City = data3[i].city;
                    var Rocode = data3[i].rocode;
                    var Roid = data3[i].roid;
                    var latitude = data3[i].lattitude;
                    var longitude = data3[i].longitude;
                    var Roaddress1 = data3[i].address;
                    var Type = data3[i].type;
                    var Diesel = '';
                    var Petrol = '';
                    var LPG = '';
					document.getElementById('tag_state').innerHTML = State;
					document.getElementById('tag_city').innerHTML = City;
                    for(var j = 0; j < fuelData.length; j++)
                    {
                        if(Roid == fuelData[j].roid)
                        {
                            if(fuelData[j].Product == 'Diesel')
                            {
                                Diesel = fuelData[j].Price;
                                DTStartDate = fuelData[j].DTStartDate;
                            }
                            if(fuelData[j].Product == 'Petrol')
                            {
                                Petrol = fuelData[j].Price;
                                DTStartDate = fuelData[j].DTStartDate;
                            }
                            if(fuelData[j].Product == 'Auto LPG')
                            {
                                LPG = fuelData[j].Price;
                                DTStartDate = fuelData[j].DTStartDate;
                            }
                        }
                    }
                    data_html += '<div class="result_card" onclick="javascript:addMarker1(\'' + latitude + '\', \'' + longitude + '\', \'' + Type + '\', \'' + Roaddress1 + '\', \'' + Roname + '\');">';
                    data_html += '<h3 class="result_card_title">' + Roname + '</h3>';
                    data_html += '<div class="result_card_ro">';
                    data_html += '<div class="ro_">RO Code: ' + Rocode + '</div>';
                    data_html += '<div class="ro_">RO ID:  ' + Roid + '</div>';
                    data_html += '</div>';
                    data_html += '<div class="result_card_middle">';
                      data_html += '<div class="contact_part">';
                        data_html += '<p class="pretitle">&nbsp;</p>';
                        data_html += '<p class="name">&nbsp;</p>';
                        data_html += '<a href="#" class="tel">&nbsp;</a>';
                      data_html += '</div>';
                    data_html += '<div class="petrol_part">';
                    if(LPG != '')
                    {
                    data_html += '<div class="petrol_inner">';
                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/lpg.svg" alt="" class="petrol_img" />';
                    data_html += '<p class="petrol_text">' + LPG + ' Rs/Ltr<span class="tooltip"><img src="/themes/custom/jiobp/assets/images/icons/tooltip-icon-dark.svg" width="12px"/><span class="bottom"><span>Last Updated on: ' + DTStartDate + '</span><i></i></span></span></p>';
                    data_html += '</div>';
                    }
                    if(Diesel != '')
                    {
                    data_html += '<div class="petrol_inner">';
                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/diesel.svg" alt="" class="petrol_img" />';
                    data_html += '<p class="petrol_text">' + Diesel + ' Rs/Ltr<span class="tooltip"><img src="/themes/custom/jiobp/assets/images/icons/tooltip-icon-dark.svg" width="12px"/><span class="bottom"><span>Last Updated on: ' + DTStartDate + '</span><i></i></span></span></p>';
                    data_html += '</div>';
                    }
                    if(Petrol != '')
                    {
                    data_html += '<div class="petrol_inner">';
                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/petrol.svg" alt="" class="petrol_img" />';
                    data_html += '<p class="petrol_text">' + Petrol + ' Rs/Ltr<span class="tooltip"><img src="/themes/custom/jiobp/assets/images/icons/tooltip-icon-dark.svg" width="12px"/><span class="bottom"><span>Last Updated on: ' + DTStartDate + '</span><i></i></span></span></p>';
                    data_html += '</div>';
                    }
                    data_html += '</div>';
                    data_html += '</div>';

                    data_html += '</div>';
                    data_html += '</div>';

                    locations.push({
                        "0": data3[i]['lattitude'],
                        "1": data3[i]['longitude'],
                        "2": data3[i]['type'],
                        "3": data3[i]['address'],
                        "4": data3[i]['name']
                    });
                }
            }
			
            form__results.innerHTML = data_html;
			addMarker(locations);
            locations = [];
            form__results.classList.remove("d-none");
            form__resetSec.classList.remove("d-none");
            form__inputs.classList.add("d-none");

			const result_card_swiper = new Swiper(".result_card_swiper", {
        		// Optional parameters
        		direction: "horizontal",
        		slidesPerView: "auto",
        		spaceBetween: 4,
        		// Navigation arrows
        		navigation: {
          			nextEl: ".swiper-button-next",
          			prevEl: ".swiper-button-prev",
        		},
      		});
			}, 500);
          }
          else
          {
            alert("Please enter only location or select city and state");
          }
        }
        if (form_locator.value !== "") {
          if (citySelect.value == "" && stateSelect.value == "") {
		var data_html = '';
            for(var i = 0; i < data3.length; i++)
            {
                if(form_locator.value == data3[i].pincode)
                {
                    var Roname = data3[i].name;
                    var State = data3[i].state;
                    var City = data3[i].city;
                    var Rocode = data3[i].rocode;
                    var Roid = data3[i].roid;
                    var latitude = data3[i].lattitude;
                    var longitude = data3[i].longitude;
                    var Roaddress1 = data3[i].address;
                    var Type = data3[i].type;
                    var Diesel = '';
                    var Petrol = '';
                    var LPG = '';
		    document.getElementById('tag_state').innerHTML = State;
		    document.getElementById('tag_city').innerHTML = City;
                    for(var j = 0; j < fuelData.length; j++)
                    {
                        if(Roid == fuelData[j].roid)
                        {
                            if(fuelData[j].Product == 'Diesel')
                            {
                                Diesel = fuelData[j].Price;
                            }
                            if(fuelData[j].Product == 'Petrol')
                            {
                                Petrol = fuelData[j].Price;
                            }
                            if(fuelData[j].Product == 'Auto LPG')
                            {
                                LPG = fuelData[j].Price;
                            }
                        }
                    }

                    data_html += '<div class="result_card" onclick="javascript:addMarker1(\'' + latitude + '\', \'' + longitude + '\', \'' + Type + '\', \'' + Roaddress1 + '\', \'' + Roname + '\');">';
                    //data_html += '<div class="result_card">';
                    data_html += '<h3 class="result_card_title">' + Roname + '</h3>';
                    data_html += '<div class="result_card_ro">';
                    data_html += '<div class="ro_">RO Code: ' + Rocode + '</div>';
                    data_html += '<div class="ro_">RO ID:  ' + Roid + '</div>';
                    data_html += '</div>';
                    data_html += '<div class="result_card_middle">';
                      data_html += '<div class="contact_part">';
                        data_html += '<p class="pretitle">&nbsp;</p>';
                        data_html += '<p class="name">&nbsp;</p>';
                        data_html += '<a href="#" class="tel">&nbsp;</a>';
                      data_html += '</div>';
                    data_html += '<div class="petrol_part">';
                    if(LPG != '')
                    {
                    data_html += '<div class="petrol_inner">';
                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/lpg.svg" alt="" class="petrol_img" />';
                    data_html += '<p class="petrol_text">' + LPG + ' Rs/Ltr</p>';
                    data_html += '</div>';
                    }
                    if(Diesel != '')
                    {
                    data_html += '<div class="petrol_inner">';
                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/diesel.svg" alt="" class="petrol_img" />';
                    data_html += '<p class="petrol_text">' + Diesel + ' Rs/Ltr</p>';
                    data_html += '</div>';
                    }
                    if(Petrol != '')
                    {
                    data_html += '<div class="petrol_inner">';
                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/petrol.svg" alt="" class="petrol_img" />';
                    data_html += '<p class="petrol_text">' + Petrol + ' Rs/Ltr</p>';
                    data_html += '</div>';
                    }
                    data_html += '</div>';
                    data_html += '</div>';
//                    data_html += '<hr class="result_card_hr" />';
//                    data_html += '<div class="result_swipe">';
//                    data_html += '<div class="swiper-button-prev"><img src="/themes/custom/jiobp/assets/images/contact-us/prev.svg" alt="" /></div>';
//                    data_html += '<div class="swiper-button-next"><img src="/themes/custom/jiobp/assets/images/contact-us/next.svg" alt="" /></div>';

//                    data_html += '<div class="swiper result_card_swiper">';
//                    data_html += '<div class="swiper-wrapper">';
//                    data_html += '<div class="swiper-slide">';
//                    data_html += '<div class="result_card_data">';
//                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/washroom.svg" alt="" class="data_img" />';
//                    data_html += '<p class="data_text">Washroom</p>';
//                    data_html += '</div>';
//                    data_html += '</div>';
//                    data_html += '<div class="swiper-slide">';
//                    data_html += '<div class="result_card_data">';
//                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/air-services.svg" alt="" class="data_img" />';
//                    data_html += '<p class="data_text">Air Service</p>';
//                    data_html += '</div>';
//                    data_html += '</div>';
//                    data_html += '<div class="swiper-slide">';
//                    data_html += '<div class="result_card_data">';
//                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/lubricants.svg" alt="" class="data_img" />';
//                    data_html += '<p class="data_text">Lubricants</p>';
//                    data_html += '</div>';
//                    data_html += '</div>';
//                    data_html += '<div class="swiper-slide">';
//                    data_html += '<div class="result_card_data">';
//                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/water.svg" alt="" class="data_img" />';
//                    data_html += '<p class="data_text">Drinking Water</p>';
//                    data_html += '</div>';
//                    data_html += '</div>';
//                    data_html += '<div class="swiper-slide">';
//                    data_html += '<div class="result_card_data">';
//                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/truck.svg" alt="" class="data_img" />';
//                    data_html += '<p class="data_text">Truck Stop</p>';
//                    data_html += '</div>';
//                    data_html += '</div>';
//                    data_html += '<div class="swiper-slide">';
//                    data_html += '<div class="result_card_data">';
//                    data_html += '<img src="/themes/custom/jiobp/assets/images/contact-us/food.svg" alt="" class="data_img" />';
//                    data_html += '<p class="data_text">Food Plaza</p>';
//                    data_html += '</div>';
//                    data_html += '</div>';
//                    data_html += '</div>';
//                    data_html += '</div>';
                    data_html += '</div>';
                    data_html += '</div>';

                    locations.push({
                        "0": data3[i]['lattitude'],
                        "1": data3[i]['longitude'],
                        "2": data3[i]['type'],
                        "3": data3[i]['address'],
                        "4": data3[i]['name']
                    });
                }
            }
            form__results.innerHTML = data_html;
	    addMarker1(locations);
            locations = [];
            form__results.classList.remove("d-none");
            form__inputs.classList.add("d-none");
            form__resetSec.classList.remove("d-none");

		const result_card_swiper = new Swiper(".result_card_swiper", {
        		// Optional parameters
        		direction: "horizontal",
        		slidesPerView: "auto",
        		spaceBetween: 4,
        		// Navigation arrows
        		navigation: {
          			nextEl: ".swiper-button-next",
          			prevEl: ".swiper-button-prev",
        		},
      		});
          }
          else
          {
            alert("Please enter only location or select city and state");
          }
        }
    });

function addMarker1(lat, lon, type, address, name, contentString) {
    locations.push({
        "0": lat,
        "1": lon,
        "2": type,
        "3": address,
        "4": name
    });

    if (marker && marker.setMap) {
        marker.setMap(null);
    }

    var infowindow = new google.maps.InfoWindow();

    var icons = {
        1: {
            icon: '/themes/custom/jiobp/assets/images/icons/map-locator-pin.svg'
        },
        2: {
            icon: '/themes/custom/jiobp/assets/images/icons/map-locator-pin.svg'
        },
        3: {
            icon: '/themes/custom/jiobp/assets/images/icons/map-locator-pin.svg'
        },
        4: {
            icon: '/themes/custom/jiobp/assets/images/icons/map-locator-pin.svg'
        }
    };

    var i;


    for (i = 0; i < locations.length; i++) {
        marker = new google.maps.Marker({
            position: new google.maps.LatLng(locations[i][0], locations[i][1]),
            map: map,
            icon: icons[locations[i][2]].icon,
        });
        markersArray.push(marker);
        map.setCenter(new google.maps.LatLng(locations[i][0], locations[i][1]));
        map.setZoom(15);

        google.maps.event.addListener(marker, 'click', (function (marker, i) {
            var lName = locations[i][4]
            var lAdd = locations[i][3]
            var lLat = locations[i][0]
            var lLon = locations[i][1]
            return function () {
infowindow.setContent('<h5 class="map_pop_title">' + lName + '</h5><p class="map_pop_text">' + lAdd + '</p><a href="javascript:getlatlong('+ lLat + ',' + lLon + ');" class="btn map_pop_btn">Get Direction</a>');
                //infowindow.setContent('<div class="addrssmap"><h4>' + lName + '<p></h4><p>' + lAdd + '</p></div>');

                infowindow.open(map, marker);
            }
        })(marker, i));
    }
    locations = [];
}
    reset_btn.addEventListener("click", function () {
        window.location.reload();
        //form__results.classList.add("d-none");
        //form__inputs.classList.remove("d-none");
        //form__resetSec.classList.add("d-none");
    });