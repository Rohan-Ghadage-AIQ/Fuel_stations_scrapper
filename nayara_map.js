var geocoder;
var map;
var address = "new york city";
var dat_lat;
var dat_long;
var pump,
    result_slider1,
    directionsService,
    directionsDisplay,
    pump1,
    calculateAndDisplayRoute,
    originInput,
    destinationInput;
$.ajaxSetup({
    headers: {
        'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
    }
});
$('.locate-a-pump__results').hide();

function initMap() {
    
    const myLatlng = { lat: 18.9690, lng: 72.8205 }; // Coordinates for Mumbai
    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 8,
        center: myLatlng,
        mapTypeId: 'roadmap',
    });

 // Start of The direction code for the second tab    

 var geocoder = new google.maps.Geocoder();
 directionsService = new google.maps.DirectionsService;
 directionsDisplay = new google.maps.DirectionsRenderer;
 input = document.getElementById('enter-location');
 searchBox = new google.maps.places.SearchBox(input);
 originInput = document.getElementById('enter-source-location');
 destinationInput = document.getElementById('enter-destination-location');
 searchBox1 = new google.maps.places.SearchBox(originInput);
 searchBox2 = new google.maps.places.SearchBox(destinationInput);
 activeInfo = new google.maps.InfoWindow();
 result_slider1 = '';
 count1 = 0;
 var count = 0;
    var markers = [];
    var marker = [];
    

    calculateAndDisplayRoute = function (directionsService, directionsDisplay) {
        directionsService.route(
            {
                origin: originInput.value,
                destination: destinationInput.value,
                travelMode: 'DRIVING',
            },
            function (response, status) {
                if (status === 'OK') {
                    directionsDisplay.setDirections(response);
    
                    var startLatLng = response.routes[0].legs[0].start_location;
                    var endLatLng = response.routes[0].legs[0].end_location;

                    console.log("Start point lat" + startLatLng);
                    console.log("Start point long" + endLatLng);

                    var routeCoordinates = [];
                         for (var i = 0; i < response.routes[0].legs[0].steps.length; i++) {
                                  var step = response.routes[0].legs[0].steps[i];
                                       routeCoordinates.push({
                                       lat: step.start_location.lat(),
                                       lng: step.start_location.lng()
                                      });
                                routeCoordinates.push({
                               lat: step.end_location.lat(),
                              lng: step.end_location.lng()
                            });
                        }
    
                    // Draw the route line
                    
                    var midpointLat = (startLatLng.lat() + endLatLng.lat()) / 2;
                    var midpointLng = (startLatLng.lng() + endLatLng.lng()) / 2;
                    var midpoint = new google.maps.LatLng(midpointLat, midpointLng);
    
                    var distance = google.maps.geometry.spherical.computeDistanceBetween(startLatLng, endLatLng);
                    var radius = 1;
                    console.log('AJAX URL:', $('.find-ro-url').val());
                    console.log("radius of route" + radius);
    
                    // AJAX call to fetch pump data
                    $.ajaxSetup({
                        headers: {
                            'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
                        }
                    });
    
                    $.ajax({
                        type: 'POST',
                        url: $('.find-ro-url').val(),
                        data: {
                            radius:radius,
                            //location: { lat: midpoint.lat(), lng: midpoint.lng() },
                            route_coordinates: routeCoordinates,
                            curr_lat: startLatLng.lat(),
                            curr_long: startLatLng.lng(),
                        },
                        success: function (data) {
                            var result_slider = '';
                            console.log("List Of Petrol Pump",data);
                            var json = jQuery.parseJSON(JSON.stringify(data));
                            var bounds = new google.maps.LatLngBounds();
                            bounds.extend(startLatLng);
                            bounds.extend(endLatLng);
                            const CUSTOM_MARKER = "https://www.nayaraenergy.com/images/point_seven_red.png";
    
                            // Add pump markers
                            $.each(json, function (key, value) {
                                var lat = value.latitude;
                                var lng = value.longitude;
                                var position = new google.maps.LatLng(lat, lng);
                                bounds.extend(position);
    
                                var marker = new google.maps.Marker({
                                    position: position,
                                    map: map,
                                    icon: {
                                    url: CUSTOM_MARKER,
                                    scaledSize: new google.maps.Size(37, 50)
                                    
                                    }, 
                                    title: value.created_at
                                });
                                console.log("Marker Icon URL:", CUSTOM_MARKER);
    
                                
                            var infoWindowContent = [
                                [
                                    '<div class="info_content" style="width:170px">' +
                                      '<h3 style="font-weight: bold; margin-bottom: 10px;">' + value.ro_name + '</h3>' +
                                      '<p style="line-height: 1.5; margin-bottom: 6px;">' + value.address + '</p>' +
                                      '<a href="https://www.google.com/maps/dir/?api=1&destination=' + value.latitude + ',' + value.longitude + '" ' +
                                         'target="_blank" rel="noopener noreferrer" ' +
                                         'style="color:#007bff; text-decoration:underline; font-weight:600;">' +
                                         'Get Directions' +
                                      '</a>' +
                                    '</div>'
                                  ]
                            ];
            
                            // var petrol_price = '';
                            // var diesel_price = '';
            
                            // Validate and format Petrol price
                            // if (value.PETROL !== '' && !isNaN(value.PETROL)) {
                            //     petrol_price = '<div class="locate-a-pump__slide_price_container">' +
                            //                     '<h6 class="locate-a-pump__slide_price_title">Petrol / ltr</h6>' +
                            //                     '<i class="fa fa-inr"></i>' + parseFloat(value.PETROL).toFixed(2) +
                            //                     '</div>';
                            // } else {
                            //     petrol_price = '<div class="locate-a-pump__slide_price_container">' +
                            //                     '<h6 class="locate-a-pump__slide_price_title">Petrol / ltr</h6>' +
                            //                     '<i class="fa fa-inr"></i> N/A' +
                            //                     '</div>';
                            // }
            
                            // if (value.DIESEL !== '' && !isNaN(value.DIESEL)) {
                            //     diesel_price = '<div class="locate-a-pump__slide_price_container">' +
                            //                     '<h6 class="locate-a-pump__slide_price_title">Diesel / ltr</h6>' +
                            //                     '<i class="fa fa-inr"></i>' + parseFloat(value.DIESEL).toFixed(2) +
                            //                     '</div>';
                            // } else {
                            //     diesel_price = '<div class="locate-a-pump__slide_price_container">' +
                            //                     '<h6 class="locate-a-pump__slide_price_title">Diesel / ltr</h6>' +
                            //                     '<i class="fa fa-inr"></i> N/A' +
                            //                     '</div>';
                            // }
            
                             result_slider += '<div class="locate-a-pump__slide">' +
                                               '<h5 class="locate-a-pump__slide_title theme-gradient">' + value.ro_name + '</h5>' +
                                              '<div class="locate-a-pump__slide_address_container">' +
                                                 '<address class="locate-a-pump__slide_address">' + value.address + '</address>' +
                                               // '<div class="locate-a-pump__slide_prices_container">' +
                                               //petrol_price +
                                                //diesel_price +
                                                 '</div>' +
                            //                     '<div class="locate-a-pump__slide_prices_container-2">'+
                            //                         '<h6 class="locate-a-pump__slide_price_title">FP Facility</h6>'+ 
                            //                         '<span>'+ value.efp +'</span>'+
                            //                     '</div>'+
                            //                     '<div class="locate-a-pump__slide_ro_container">' +
                            //                     '<b class="locate-a-pump__slide_ro_title">Ro code</b>' + value.cms_code +
                            //                     '</div>' +
                            //                     '</div>' +
                                              '</div>';
                                                var infoWindow = new google.maps.InfoWindow();
                                                infoWindow.setContent(infoWindowContent[0][0]);
                    
                                                google.maps.event.addListener(marker, 'click', (function (marker, key) {
                                                    return function () {
                                                        activeInfo.close();
                                                        infoWindow.open(map, this);
                                                        activeInfo = infoWindow;
                                                    };
                                                })(marker, key));
                    
                                                markers.push(marker);
                                                map.fitBounds(bounds);
                                                count++;
                                            });
                    
                                            $('.locate-a-pump__results').show();
                                            $('.result_count').html('Total ' + count + ' Results');
                    
                                            var $slider = $('.locate-a-pump__slider');
                                            if ($slider.length && $.fn.slick) {
                           // Destroy only if initialized
                                    if ($slider.hasClass('slick-initialized')) {
                                        $slider.slick('unslick');
                                    }

                                        // Inject new slides
                                        $slider.html(result_slider);

                                        // Initialize Slick
                                    $slider.slick({
                                        slidesToShow: 3,
                                        slidesToScroll: 1,
                                        infinite: false,
                                        arrows: true,
                                        dots: false
                                    });
                                }
                                        },
                        error: function (error) {
                            console.error('Error fetching pumps:', error);
                        },
                    });
                } else {
                    console.error('Directions request failed due to ' + status);
                }
            }
        );
    };
    
    directionsDisplay.setMap(map);
    


}

//2nd Tab Route Functionality 

$('#ro_route').on('click',function() {
    $('.locate-a-pump__slider').empty();
    initMap();
    $('#hid_route').trigger('click');
    calculateAndDisplayRoute(directionsService, directionsDisplay);
})



// Google Map Javascript is loading
$(document).ready(function () {
    function loadGoogleMapsApi() {
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyCt8g09M4pRLpiK76c4_4jH5FPJDTcVODg&libraries=places,directions&callback=initMap`;
        script.async = true;
        script.defer = true;
        $('head').append(script);
    }
loadGoogleMapsApi();

    
        $('#current-btn').on('click', function () {
            if ("geolocation" in navigator) {
                navigator.geolocation.getCurrentPosition(
                    function (position) {
                        handleGeolocationSuccess(position);
                    },
                    function (error) {
                        handleGeolocationError(error);
                    }
                );
            } else {
                console.error("Browser doesn't support geolocation!");
                alert("Geolocation is not supported by your browser.");
            }
        });
    
        function handleGeolocationSuccess(position) {
            const geoLocation = processGeolocationResult(position);
            const [latitude, longitude] = geoLocation.split(",");
            initializeCurrent(latitude, longitude);
        }

        function handleGeolocationError(error) {
            let errorMessage = "An unknown error occurred.";
            switch (error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage = "Location permission denied. Please enable location services.";
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage = "Location information is unavailable.";
                    break;
                case error.TIMEOUT:
                    errorMessage = "The request to get user location timed out.";
                    break;
            }
            console.error("Geolocation error:", errorMessage);
            alert(errorMessage);
        }
    
        function processGeolocationResult(position) {
            const latitude = position.coords.latitude.toFixed(8); 
            const longitude = position.coords.longitude.toFixed(8); 
            return `${latitude}, ${longitude}`;
        }
        function initializeCurrent(latitude, longitude) {
            const geocoder = new google.maps.Geocoder();
            const location = new google.maps.LatLng(latitude, longitude);
            dat_lat = latitude;
            dat_long = longitude;
            getCurrentAddress(geocoder, location);
        }

        function getCurrentAddress(geocoder, location) {
            geocoder.geocode({ location: location }, function (results, status) {
                if (status === google.maps.GeocoderStatus.OK && results.length > 0) {
                    const address = results[0].formatted_address;
                    $("#enter-location").val(address);
                    $(".location_coordinates").attr("data-lat", dat_lat);
                    $(".location_coordinates").attr("data-long", dat_long);
                } else {
                    console.error("Geocoder failed due to:", status);
                    alert(`Geocoding failed: ${status}`);
                }
            });
        }
    });

// 1st Tab Code 

$('#location_button').on('click', function() {
    var radius = $('#location-radius').val();
    var location = $('#enter-location').val();
    var curr_lat = $('.location_coordinates').attr('data-lat');
    var curr_long = $('.location_coordinates').attr('data-long');
    var url = $('.ro-code-radius').val();
    var btn = $(this);

    // Validate input
    if (!radius || !location) {
        alert('Please enter a valid location and radius.');
        return;
    }

    // Disable the button while the request is in progress
    btn.prop('disabled', true).addClass('btn-loading');
  
        // Geocode the entered location
        geocodeLocation(location, function(lat, lng) {
            if (lat && lng) {
                curr_lat = lat;
                curr_long = lng;
                $('.location_coordinates').attr('data-lat', lat);
                $('.location_coordinates').attr('data-long', lng);
                fetchPumpDetails(lat, lng, radius, url, btn);
            } else {
                alert('Unable to find the location. Please try again.');
                btn.prop('disabled', false).removeClass('btn-loading');
            }
        });
    
});

// Function to geocode a location using Google Maps Geocoding API
function geocodeLocation(location, callback) {
    var geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: location }, function(results, status) {
        if (status === google.maps.GeocoderStatus.OK && results.length > 0) {
            var lat = results[0].geometry.location.lat();
            var lng = results[0].geometry.location.lng();
            callback(lat, lng);
        } else {
            console.error('Geocoding failed:', status);
            callback(null, null);
        }
    });
}

// Function to fetch pump details from the backend
function fetchPumpDetails(lat, lng, radius, url, btn) {
    console.log('Fetching pumps for:', { lat: lat, lng: lng, radius: radius });
    $('.error').text('');

    $.ajax({
        type: 'POST',
        url: url,
        data: {
            curr_lat: lat,
            curr_long: lng,
            radius: radius
        },
        success: function(data) {
            btn.prop('disabled', false).removeClass('btn-loading');

            if (!data || data.length === 0) {
                $('.error').text('No Petrol Pump found.');
                return;
            }

            initializeMapAndResults(lat, lng, data);
        },
        error: function(xhr, status, error) {
            console.error('Error fetching pumps:', error);
            $('.error').text('Failed to fetch data. Please try again.');
            btn.prop('disabled', false).removeClass('btn-loading');
        }
    });
}

// Function to initialize the map and display pump details
function initializeMapAndResults(centerLat, centerLng, data) {
    var bounds = new google.maps.LatLngBounds();
    var map = new google.maps.Map($('#map')[0], {
        zoom: 8,
        center: { lat: centerLat, lng: centerLng }
    });

    var resultSlider = '';
    var count = 0;
    const CUSTOM_MARKER = "https://www.nayaraenergy.com/images/point_seven_red.png";

    $.each(data, function(index, pump) {
        var position = new google.maps.LatLng(pump.latitude, pump.longitude);
        bounds.extend(position);

        // Create a marker
        var marker = new google.maps.Marker({
            position: position,
            map: map,
              icon: {
                                    url: CUSTOM_MARKER,
                                    scaledSize: new google.maps.Size(37, 50)
                                    }, 
            title: pump.ro_name
        });
        console.log("Marker Icon URL:", CUSTOM_MARKER);

        // InfoWindow content
        var infoWindowContent = `
            <div class="info_content" style="width:170px">
                <h3 style="font-weight: bold; margin-bottom: 10px;">${pump.ro_name}</h3>
                <h3 style="font-weight: bold; margin-bottom: 10px;">${pump.address1}</h3>
                <p style="line-height: 1.5">
                    <a href="https://www.google.com/maps/search/?api=1&query=${pump.latitude},${pump.longitude}" target="_blank" rel="noopener noreferrer">
                        ${pump.address}
                    </a>
                </p>
                <a href="https://www.google.com/maps/dir/?api=1&destination=${pump.latitude},${pump.longitude}" target="_blank" rel="noopener noreferrer" style="color:#007bff; text-decoration:underline; font-weight:600;">
                    Get Directions
                </a>
            </div>`;
        var infoWindow = new google.maps.InfoWindow({ content: infoWindowContent });

        marker.addListener('click', function() {
            infoWindow.open(map, marker);
        });

        // Build slider content
        resultSlider += `
            <div class="locate-a-pump__slide">
                <h5 class="locate-a-pump__slide_title theme-gradient">${pump.ro_name}</h5>
                <div class="locate-a-pump__slide_address_container">
                    <address class="locate-a-pump__slide_address">${pump.address}</address>
                </div>
            </div>`;
        count++;
    });
    map.fitBounds(bounds);
    var $slider = $('.locate-a-pump__slider');

    if ($slider.length) {
        // Destroy only if initialized
        if ($slider.hasClass('slick-initialized')) {
            $slider.slick('unslick');
        }
        $slider.html(resultSlider);
        $slider.slick({
            slidesToShow: 3,
            slidesToScroll: 1,
            infinite: false,
            arrows: true,
            dots: false
        });
    }
    $('.result_count').html(`Total ${count} Results`);
    $('.locate-a-pump__results').show();
}




// 3rd Tab  Search the Ro Based On the CMS RO code 

$('#code_button').on('click', function() {
    var ro_code = $('#search-ro').val();
    var btn = this;
    var markers = [];
    var marker = [];
    var key;
    var activeInfo = new google.maps.InfoWindow();
    var infoWindow = '';

    if (ro_code != '') {
        $.ajaxSetup({
            headers: {
                'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
            }
        });

        $.ajax({
            type: 'POST',
            url: $('.ro-code-url').val(),
            data: {
                ro_code: ro_code
            },
            beforeSend: function() {
                // $('#code_button').addClass('btn-loading');
            },
            success: function(data) {
                btn.disabled = false;
                $('#code_button').removeClass('btn-loading');
                var result_slider = '';
                const CUSTOM_MARKER = "https://www.nayaraenergy.com/images/point_seven_red.png";

                if (data.error) {
                    alert(data.error);
                } else {
                    var mumbai = {
                        lat: 19.0760,
                        lng: 72.8777
                    };
                    var bounds = new google.maps.LatLngBounds();
                    var map = new google.maps.Map(
                        document.getElementById('map'), {
                            zoom: 4,
                            center: mumbai
                        });

                    $.each(data, function(key, value) {
                        var lat = value.latitude;
                        var lng = value.longitude;
                        var position = new google.maps.LatLng(lat, lng);
                        bounds.extend(position);

                        var marker = new google.maps.Marker({
                            position: position,
                            map: map,
                             icon: {
                                    url: CUSTOM_MARKER,
                                    scaledSize: new google.maps.Size(37, 50)
                                   
                                    },
                            title: value.address1
                        });
                        console.log("Marker Icon URL:", CUSTOM_MARKER);

                        var infoWindowContent = [
                            [
                                '<div class="info_content" style="width:170px">' +
                                  '<h3 style="font-weight: bold; margin-bottom: 10px;">' + value.ro_name + '</h3>' +
                                  '<p style="line-height: 1.5; margin-bottom: 6px;">' + value.address + '</p>' +
                                  '<a href="https://www.google.com/maps/dir/?api=1&destination=' + value.latitude + ',' + value.longitude + '" ' +
                                     'target="_blank" rel="noopener noreferrer" ' +
                                     'style="color:#007bff; text-decoration:underline; font-weight:600;">' +
                                     'Get Directions' +
                                  '</a>' +
                                '</div>'
                              ]
                        ];

                        // var petrol_price, diesel_price;
                        // if (value.PETROL === '') {
                        //     petrol_price = '<div class="locate-a-pump__slide_price_container">' +
                        //         '<h6 class="locate-a-pump__slide_price_title">Petrol / ltr</h6>' +
                        //         '<i class="fa fa-inr"></i> N/A' +
                        //         '</div>';
                        // } else {
                        //     petrol_price = '<div class="locate-a-pump__slide_price_container">' +
                        //         '<h6 class="locate-a-pump__slide_price_title">Petrol / ltr</h6>' +
                        //         '<i class="fa fa-inr"></i>' + parseFloat(value.PETROL).toFixed(2) +
                        //         '</div>';
                        // }

                        // if (value.DIESEL === '') {
                        //     diesel_price = '<div class="locate-a-pump__slide_price_container">' +
                        //         '<h6 class="locate-a-pump__slide_price_title">Diesel / ltr</h6>' +
                        //         '<i class="fa fa-inr"></i> N/A' +
                        //         '</div>';
                        // } else {
                        //     diesel_price = '<div class="locate-a-pump__slide_price_container">' +
                        //         '<h6 class="locate-a-pump__slide_price_title">Diesel / ltr</h6>' +
                        //         '<i class="fa fa-inr"></i>' + parseFloat(value.DIESEL).toFixed(2) +
                        //         '</div>';
                        // }

                        result_slider += '<div class="locate-a-pump__slide">' +
                            '<h5 class="locate-a-pump__slide_title theme-gradient">' + value.ro_name + '</h5>' +
                            '<div class="locate-a-pump__slide_address_container">' +
                            '<address class="locate-a-pump__slide_address">' + value.address + '</address>' +
                            // '<div class="locate-a-pump__slide_prices_container">' +
                            // petrol_price +
                            // diesel_price +
                            // '</div>' +
                            // '<div class="locate-a-pump__slide_prices_container-2">' +
                            // '<h6 class="locate-a-pump__slide_price_title">FP Facility</h6>' +
                            // '<span>' + value.efp + '</span>' +
                            // '</div>' +
                            // '<div class="locate-a-pump__slide_ro_container">' +
                            // '<b class="locate-a-pump__slide_ro_title">Ro code</b>' + value.cms_code +
                            // '</div>' +
                            // '</div>' +
                            '</div>';

                        var infoWindow = new google.maps.InfoWindow();
                        infoWindow.setContent(infoWindowContent[0][0]);
                        google.maps.event.addListener(marker, 'click', (function(marker, key) {
                            return function() {
                                activeInfo.close();
                                infoWindow.open(map, this);
                                activeInfo = infoWindow;
                            };
                        })(marker, key));

                        markers.push(marker);
                        map.fitBounds(bounds);
                    });

                    $('.locate-a-pump__results').show();
                    $('.result_count').html('About ' + data.length + ' Results');
                    $('.locate-a-pump__slider')
                        .slick('unslick')
                        .html(result_slider);
                }
            },
            error: function(xhr, textStatus, error) {
                btn.disabled = false;
                $('#code_button').removeClass('btn-loading');
                if (xhr.status == 500) {
                    alert('Something went wrong on the server.');
                } else if (xhr.status == 404) {
                    alert('Pump not found.');
                } else if (xhr.status == 400) {
                    alert('Bad request. Please check the input.');
                } else {
                    alert('Error: ' + textStatus + ' - ' + error);
                }
            }
        });
    } else {
        alert('Please Enter RO Code');
    }
});













