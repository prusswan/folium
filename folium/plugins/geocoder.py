from branca.element import MacroElement
from jinja2 import Template

from folium.elements import JSCSSMixin
from folium.utilities import parse_options


class Geocoder(JSCSSMixin, MacroElement):
    """A simple geocoder for Leaflet that by default uses OSM/Nominatim.

    Please respect the Nominatim usage policy:
    https://operations.osmfoundation.org/policies/nominatim/

    Parameters
    ----------
    collapsed: bool, default False
        If True, collapses the search box unless hovered/clicked.
    position: str, default 'topright'
        Choose from 'topleft', 'topright', 'bottomleft' or 'bottomright'.
    add_marker: bool, default True
        If True, adds a marker on the found location.
    geocodeProvider: str, default 'nominatim'
        see https://github.com/perliedman/leaflet-control-geocoder/tree/2.4.0/src/geocoders for other built-in providers
    geocodeProviderOptions: dict, default None
        For use with specific providers that may require api keys or other parameters
    serviceUrl: str, default None
        For use with user-defined geocode provider. If used, geocodeFunction must also be specified, geocodeProvider param will be ignored.
    geocodeFunction: str, default None
        geocode function of user-defined geocode provider. see https://github.com/perliedman/leaflet-control-geocoder/blob/1.13.0/src/geocoders/nominatim.js for a reference implementation
    resultsHandlerFunction: str, default None
        For use with user-defined geocode provider, to format geocoding responses into the format expected by leaflet-control-geocoder. Each result should have 'name','center' (L.latLng),'bbox' (L.latLngBounds) properties. see https://github.com/perliedman/leaflet-control-geocoder/blob/1.13.0/src/geocoders/photon.js (_decodeFeatures) for a reference implementation

    For all options see https://github.com/perliedman/leaflet-control-geocoder

    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}

            var geocoderOpts_{{ this.get_name() }} = {{ this.options|tojson }};
            if ('geocodeFunction' in geocoderOpts_{{ this.get_name() }}) {
                eval("geocoderOpts_{{ this.get_name() }}['geocodeFunction'] = " + geocoderOpts_{{ this.get_name() }}['geocodeFunction']);
            }
            if ('resultsHandlerFunction' in geocoderOpts_{{ this.get_name() }}) {
                eval("geocoderOpts_{{ this.get_name() }}['resultsHandlerFunction'] = " + geocoderOpts_{{ this.get_name() }}['resultsHandlerFunction']);
            }
            var customGeocoderTemplate_{{ this.get_name() }} = {
                class: L.Class.extend({
                    options: {
                        serviceUrl: geocoderOpts_{{ this.get_name() }}['serviceUrl'],
                        geocodingQueryParams:  geocoderOpts_{{ this.get_name() }}['geocodingQueryParams'] || {},
                        reverseQueryParams: geocoderOpts_{{ this.get_name() }}['reverseQueryParams'] || {},
                    },

                    initialize: function(options) {
                        L.Util.setOptions(this, options || {});
                    },

                    geocode: geocoderOpts_{{ this.get_name() }}['geocodeFunction'],

                    suggest: function(query,cb,context) {
                        return this.geocode(query, cb, context);
                    },

                    // placeholder: not used by folium.plugin.Geocoder
                    reverse: function(location, scale, cb, context) {
                      var params = L.extend(
                        {
                          //defaultParam: defaultParamValue
                        },
                        this.options.reverseQueryParams
                      );

                      this.getJSON(
                        this.options.serviceUrl + 'reverse',
                        params,
                        L.bind(function(data) {
                          cb.call(context, this._resultsHandler(data));
                        }, this)
                      );
                    },

                    _resultsHandler: function(data) {
                        if ('resultsHandlerFunction' in geocoderOpts_{{ this.get_name() }}) {
                            return geocoderOpts_{{ this.get_name() }}['resultsHandlerFunction'](data);
                        }
                        return data;
                    },

                    getJSON: function(url, params, callback) {
                        var xmlHttp = new XMLHttpRequest();
                        xmlHttp.onreadystatechange = function () {
                            if (xmlHttp.readyState !== 4){
                                return;
                            }
                            if (xmlHttp.status !== 200 && xmlHttp.status !== 304){
                                callback('');
                                return;
                            }
                            callback(JSON.parse(xmlHttp.response));
                        };
                        xmlHttp.open('GET', url + L.Util.getParamString(params), true);
                        xmlHttp.setRequestHeader('Accept', 'application/json');
                        xmlHttp.send(null);
                    }

                }),

                factory: function(options) {
                    return new L.Control.Geocoder.Custom_{{ this.get_name() }}(options);
                },

            }

            L.Util.extend(L.Control.Geocoder, {
                Custom_{{ this.get_name() }}: customGeocoderTemplate_{{ this.get_name() }}.class,
                custom_{{ this.get_name() }}: customGeocoderTemplate_{{ this.get_name() }}.factory
            });

            // use lowercase for geocoder name
            var geocoderName_{{ this.get_name() }};
            if ('serviceUrl' in geocoderOpts_{{ this.get_name() }}) {
                geocoderName_{{ this.get_name() }} = 'custom_{{ this.get_name() }}';
            }
            else {
                geocoderName_{{ this.get_name() }} = geocoderOpts_{{ this.get_name() }}["geocodeProvider"];
            }

            var customGeocoder_{{ this.get_name() }} = L.Control.Geocoder[ geocoderName_{{ this.get_name() }} ](
                geocoderOpts_{{ this.get_name() }}['geocodeProviderOptions']
            );
            geocoderOpts_{{ this.get_name() }}["geocoder"] = customGeocoder_{{ this.get_name() }};

            L.Control.geocoder(
                geocoderOpts_{{ this.get_name() }}
            ).on('markgeocode', function(e) {
                {{ this._parent.get_name() }}.setView(e.geocode.center, 11);
            }).addTo({{ this._parent.get_name() }});

        {% endmacro %}
    """
    )

    default_js = [
        (
            "Control.Geocoder.js",
            "https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js",
        )
    ]
    default_css = [
        (
            "Control.Geocoder.css",
            "https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css",
        )
    ]

    def __init__(self, collapsed=False, position="topright", add_marker=True,
                 geocodeProvider="nominatim",
                 geocodeProviderOptions=None,
                 serviceUrl=None,
                 geocodeFunction=None,
                 resultsHandlerFunction=None,
                 **kwargs):
        super().__init__()
        self._name = "Geocoder"
        self.options = parse_options(
            collapsed=collapsed,
            position=position,
            defaultMarkGeocode=add_marker,
            geocodeProvider=geocodeProvider,
            serviceUrl=serviceUrl,
            geocodeFunction=geocodeFunction,
            resultsHandlerFunction=resultsHandlerFunction,
            **kwargs
        )
        if geocodeProviderOptions is not None:
            self.options['geocodeProviderOptions'] = geocodeProviderOptions
