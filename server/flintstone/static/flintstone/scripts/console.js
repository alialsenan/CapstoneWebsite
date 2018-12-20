// Features which can be placed on the map
var routeFeatures = {

    path: new ol.Feature({
        type: 'route',
        geometry: new ol.geom.LineString([])
    }),

    car_icon: new ol.Feature({
        type: 'car',
        geometry: new ol.geom.Point([0,0])
    }),

    dest_icon: new ol.Feature({
        type: 'destination',
        geometry: new ol.geom.Point([0,0])
    }),

    start_icon: new ol.Feature({
        type: 'start',
        geometry: new ol.geom.Point([0,0])
    }),
};

// Styles of the items on the map
var routeStyles = {
    'route': new ol.style.Style({
        stroke: new ol.style.Stroke({
        width: 6, color: [0, 0, 255, 0.8]
        })
    }),

    'car': new ol.style.Style({
        image: new ol.style.Icon({
        anchor: [0.5, 0.5],
        scale: 0.6,
        src: '/static/flintstone/img/car.png'
        })
    }),

    'destination': new ol.style.Style({
        image: new ol.style.Icon({
        anchor: [0.5, 0.875],
        scale: 0.3,
        src: '/static/flintstone/img/destination.png'
        })
    }),

    'start': new ol.style.Style({
        image: new ol.style.Icon({
        anchor: [0.5, 0.843],
        scale: 0.5,
        src: '/static/flintstone/img/start.png'
        })
    }),

};

var vectorLayer = new ol.layer.Vector({
source: new ol.source.Vector({
    features: []
    }),
    style: function(feature) {
        return routeStyles[feature.get('type')];
    }
});

var map = new ol.Map({
    target: document.getElementById('map'),

    controls: [],

    interactions: ol.interaction.defaults({
        dragPan: true,
        doubleClickZoom: true,
        mouseWheelZoom: true,
        pinchZoom: true
    }),

    layers: [
        new ol.layer.Tile({
        source: new ol.source.OSM()
        }),
        vectorLayer
    ],

    loadTilesWhileAnimating: true,

    view: new ol.View({
        projection: 'EPSG:4326',
        center: [-87.21660110543007,30.54850797462019],
        zoom: 18,
        minZoom: 2,
        maxZoom: 20
    }),
});

var menu_manager =
{
    current_menu: null,

    /**
     * Switches from one menu to the next by destroying the old template,
     * requesting the next template from the server, and triggering the 
     * on_load call of the new menu.
     **/
    transition_to: function(next_menu)
    {
        if (this.current_menu != null)
        {
            this.current_menu.destroy();
        }

        // Request the template for the menu from the server
        this.load_template(next_menu.template_url, next_menu.on_load, true);

        // Update the current menu
        this.current_menu = next_menu;

        // Update the user state code to prevent the screen from updating twice
        for (var property in user_status_codes) 
        {
            if (user_status_codes.hasOwnProperty(property) && 
                user_status_codes[property] == next_menu) 
            {
                this.user_state = property;
            }
        }
    },

    /**
     * Clears the currently loading DOM content in the overlay.
     **/
    clear_html: function()
    {
        var menu = this.get_DOM_parent();
        menu.innerHTML = "";
    },

    /**
     * Loads the current template from the server.
     */
    load_template: function(url, fill_callback, prevent_caching)
    {
        var xhttp = new XMLHttpRequest();

        // Set the callback for after the template is loaded from the server
        xhttp.onreadystatechange = fill_callback;

        // Use a random argument to prevent caching
        if (prevent_caching)
        {
            url += "/?t=" + Math.random();
        }
    
        // Request the resource
        xhttp.open("GET", url, true);
        xhttp.send();
    },

    /**
     * Returns the DOM element containing the menu
     */
    get_DOM_parent: function()
    {
        return document.getElementById("overlay");
    },

    /**
     * Loads the current status of the car from the server
     * and updates corresponding fields.
     */
    get_status_update: function()
    {
        var status_request = new XMLHttpRequest();

        // Set the callback for after the JSON path is loaded from the server
        status_request.onreadystatechange = function()
        {
            // Prepare the DOM events and styling
            if (this.readyState == 4 && this.status == 200) 
            {
                // Update path geometry
                wait_status = JSON.parse(this.responseText);

                // Was there a state change?
                if (menu_manager.user_state != wait_status.user_state)
                {
                    // Move to next menu
                    menu_manager.transition_to(user_status_codes[wait_status.user_state]);
                } 

                // Handle waiting live updates
                if (wait_status.user_state == "w")
                {
                    routeFeatures.car_icon.getGeometry().setCoordinates(wait_status.car_location);
	
                    var minutes = Math.floor(wait_status.wait_time/60);
                    var seconds = wait_status.wait_time%60;

                    // Add wait time in minute:second format
		    document.getElementById("est_wait_time").innerHTML = minutes+(seconds<9?":0":":")+seconds;
                }

                // Set the menu current state
                menu_manager.user_state = wait_status.user_state;
            }
        }

        status_request.open("GET", "status", true);
        status_request.send();
    },

    // Period in seconds between polling the status while waiting for a ride
    STATUS_REFRESH_PERIOD: 5,

    user_state: "0",

    status_timer: null,
}

/**
 * A menu is a helper model for the menu manager. It controls which template
 * the menu uses, events related to the template, and setup/cleanup when
 * switching between templates.
 */
function Menu(template_url, on_load, destroy)
{
    this.template_url = template_url;
    this.on_load = on_load;
    this.destroy = destroy;
}

var set_ride_menu = new Menu(
    "set_ride_form", 

    function() 
    {
        // Prepare the DOM events and styling
        if (this.readyState == 4 && this.status == 200) 
        {
            menu = menu_manager.get_DOM_parent();
            menu.style.height = "100%";
            menu.innerHTML = this.responseText;
            document.getElementById("ride_requester").addEventListener("click",  
                function()
                {
                    set_ride_menu.send_form();
                });
        }
    },

    function() {
        menu_manager.clear_html();
    }
);

set_ride_menu.send_form = function()
{
    start_field = document.getElementById("start_field");
    dest_field = document.getElementById("dest_field");

    ride_request = 
    {
        start: start_field.options[start_field.selectedIndex].value,
        destination: dest_field.options[dest_field.selectedIndex].value,
    }
    

    var ride_request_handler = new XMLHttpRequest();

    // Set the callback for after the JSON path is loaded from the server
    ride_request_handler.onreadystatechange = function()
    {
        // Prepare the DOM events and styling
        if (this.readyState == 4 && this.status == 200) 
        {
            route_data = JSON.parse(this.responseText);

            // Show errors if they are present, otherwise proceed
            if (route_data.status == "error")
            {
                document.getElementById("error_field").innerHTML = route_data.error_message;
            }
            else
            {
                menu_manager.transition_to(wait_menu);
            }
        }
    }

    ride_request_handler.open("POST", "set_ride/", true);
    ride_request_handler.setRequestHeader("Content-Type", "application/json");
    ride_request_handler.send(JSON.stringify(ride_request));
}


var wait_menu = new Menu(
    "wait",

    function() {
        if (this.readyState == 1) 
        {
            wait_menu.load_path();

            // Add geography to the map
            vectorLayer.getSource().addFeature(routeFeatures.path);
            vectorLayer.getSource().addFeature(routeFeatures.car_icon);
            vectorLayer.getSource().addFeature(routeFeatures.dest_icon);
            vectorLayer.getSource().addFeature(routeFeatures.start_icon);
        }
        else if (this.readyState == 4 && this.status == 200) 
        {
            menu = menu_manager.get_DOM_parent();
            menu.innerHTML = this.responseText;
            menu.style.height = "4em";
            document.getElementById("wait_menu_cancel").addEventListener("click",  
                function()
                {
                    if (confirm("Are you sure you want to cancel the ride?") == true) 
                    {
                        menu_manager.transition_to(set_ride_menu);
                    }
                }
            )
        }
    },

    function() {
        menu_manager.clear_html();
        routeFeatures.path.setGeometry(new ol.geom.LineString([]));

        // Remove geography from the map
        vectorLayer.getSource().removeFeature(routeFeatures.path);
        vectorLayer.getSource().removeFeature(routeFeatures.car_icon);
        vectorLayer.getSource().removeFeature(routeFeatures.dest_icon);
        vectorLayer.getSource().removeFeature(routeFeatures.start_icon);
    }
);

/**
 * Loads the path the car is following from the server.
 */
wait_menu.load_path = function()
{
    var path_request = new XMLHttpRequest();

    // Set the callback for after the JSON path is loaded from the server
    path_request.onreadystatechange = function()
    {
        // Prepare the DOM events and styling
        if (this.readyState == 4 && this.status == 200) 
        {
            route_data = JSON.parse(this.responseText);

            // Update path geometry
            routeFeatures.path.setGeometry(new ol.geom.LineString(route_data.points));
            routeFeatures.dest_icon.getGeometry().setCoordinates(route_data.destination_loc);
            routeFeatures.start_icon.getGeometry().setCoordinates(route_data.start_loc);
        }
    }

    path_request.open("GET", "currentpath", true);
    path_request.send();
}

var arrived_menu = new Menu(
    "arrived", 

    function() 
    {
        // Prepare the DOM events and styling
        if (this.readyState == 4 && this.status == 200) 
        {
            menu = menu_manager.get_DOM_parent();
            menu.style.height = "100%";
            menu.innerHTML = this.responseText;
            document.getElementById("ride_requester").addEventListener("click",  
                function()
                {
                    menu_manager.transition_to(set_ride_menu)
                }
            )
        }
    },

    function() {
        menu_manager.clear_html();
    }
);

/**
 * Dictionary for looking up the current state of the user.
 */
var user_status_codes =
{
    r: set_ride_menu,
    w: wait_menu,
    a: arrived_menu,
    p: arrived_menu,
}

menu_manager.status_timer = setInterval(menu_manager.get_status_update, menu_manager.STATUS_REFRESH_PERIOD*1000);

// Force the first update
menu_manager.get_status_update()
