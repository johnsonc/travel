//------------------------------------------------------------------------------
// Sample entity object
//------------------------------------------------------------------------------
// entity = {
//    "rating": 3,
//    "entity_id": 1463,
//    "code": "BUD",
//    "type_title": "Airport",
//    "num_visits": 1,
//    "flag_url": "img/ap-32.png",
//    "type_abbr": "ap",
//    "id": 276
//    "country_code": "HU",
//    "country_name": "Hungary",
//    "most_recent_visit": "2013-12-29 08:00:00",
//    "first_visit": "2013-12-29 08:00:00",
//    "name": "Budapest Ferenc Liszt International Airport"
// }
//------------------------------------------------------------------------------

;var Travelogue = (function($) {
    var root = this;
    var $$ = _.bind(document.getElementById, document);
    var type_mapping = {
        'cn': 'Continents',
        'co': 'Countries',
        'st': 'States',
        'ap': 'Airports',
        'ct': 'Cities',
        'np': 'National Parks',
        'lm': 'Landmarks',
        'wh': 'World Heritage sites'
    };
    
    _.templateSettings.interpolate = /{{([\s\S]+?)}}/g;
    
    var profile_datepicker_opts = {
        changeMonth: true,
        changeYear: true,
        showButtonPanel: true,
        yearRange: 'c-50:nnnn'
    };
    
    var sorters = {
        'type': function(a, b) {
            if(b.type_title > a.type_title) {
                return 1;
            }
            if(a.type_title < b.type_title) {
                return -1;
            }
            if(b.name > a.name) {
                return 1;
            }
            return (a.name < b.name) ? -1 : 0;
        },
        'name': function(a, b) {
            if(b.name > a.name) {
                return 1;
            }
            return (a.name < b.name) ? -1 : 0;
        },
        'recent': function(a, b) { return b.most_recent_visit.date - a.most_recent_visit.date; },
        'first':  function(a, b) { return b.first_visit.date - a.first_visit.date; },
        'logs':   function(a, b) { return b.num_visits - a.num_visits; },
        'rating': function(a, b) { return a.rating - b.rating; }
    };
    
    //--------------------------------------------------------------------------
    var stars = (function() {
        var STARS = '★★★★★';
        return function(rating) { return STARS.substr(rating - 1); };
    }());
    
    //--------------------------------------------------------------------------
    var date_wrapper = function(dt_str) {
        var dt = new Date(dt_str);
        var str = dt.toString().split(' ');
        var hours = dt.getHours();
        var hours12 = hours ? hours % 12 : 12;
        
        return {
            'date': dt,
            'date_string': str[1] + ' ' + dt.getDate() + ', ' + dt.getFullYear(),
            'time_string': str[0] + ' ' + hours12  + ':' + pad(dt.getMinutes()) + (hours > 12 ? 'pm' : 'am')
        }
    };
    
    //--------------------------------------------------------------------------
    var increment = function(obj, field) {
        obj[field] = obj[field] ? obj[field]  + 1 : 1;
    };
    
    //--------------------------------------------------------------------------
    var country_cmp = function(a, b) {
        return (a[1] > b[1]) ? 1 : (a[1] < b[1] ? -1 : 0);
    };
    
    //--------------------------------------------------------------------------
    var entity_url = function(e) {
        return '/i/' + e.type_abbr + '/' + (
            (e.type_abbr == 'wh' || e.type_abbr == 'st')
          ? (e.country_code + '-' + e.code)
          : e.code
        ) + '/';
    };

    //--------------------------------------------------------------------------
    var DOM = root.DOM = {
        create: function(tag) {
            var j, key, arg;
            var el = document.createElement(tag);
            for(var i = 1; i < arguments.length; i++) {
                arg = arguments[i];
                if(_.isPlainObject(arg)) {
                    for(key in arg) {
                        if(arg.hasOwnProperty(key)) {
                            el.setAttribute(key, arg[key]);
                        }
                    }
                }
                else if(_.isArray(arg)) {
                    for(j = 0; j < arg.length; j++) {
                        el.appendChild(arg[j]);
                    }
                }
                else {
                    el.textContent = arg.toString();
                }
            }
            return el;
        }
    };
    
    //--------------------------------------------------------------------------
    var date_tags = function(dtw) {
        return [
            DOM.create('nobr', dtw.date_string),
            DOM.create('nobr', dtw.time_string)
        ];
    };
    
    //--------------------------------------------------------------------------
    var create_entity_row = function(e) {
        var name_td = DOM.create('td');
        var flag_td = DOM.create('td');
        var extras = [];
        var attrs = {
            'data-id' : e.id,
            'class': e.type_abbr + ' co-' + e.country_code ? e.country_code : (e.type_abbr == 'co' ? e.code : '')
        };

        name_td.appendChild(DOM.create('a', e.name, {'href': e.entity_url}));

        if(e.flag_url) {
            flag_td.appendChild(DOM.create('img', {'src': e.flag_url, 'class': 'flag'}));
        }
        
        if(e.locality) {
            extras.push(e.locality);
        }

        if(e.country_name) {
            extras.push(e.country_name);
        }

        if(extras.length) {
            name_td.appendChild(DOM.create('span', extras.join(', ')))
        }
        
        if(e.flag_co_url) {
            name_td.appendChild(DOM.create('img', {'src': e.flag_co_url, 'class': 'flag flag-sm'}));
        }

        return DOM.create('tr', attrs, [
            flag_td,
            DOM.create('td', e.type_title),
            name_td,
            DOM.create('td', date_tags(e.most_recent_visit)),
            DOM.create('td', date_tags(e.first_visit)),
            DOM.create('td', e.num_visits),
            DOM.create('td', stars(e.rating))
        ]);
    };
    
    //--------------------------------------------------------------------------
    var profile_history = {
        media_prefix: '/media/',
        initialize: function(history, conf) {
            var media_prefix = conf.media_prefix || this.media_prefix;
            var co_opts = $$('id_co');
            var summary = {};
            var countries = {};

            this.filters = {'type': null, 'country_code': null};
            this.all_entities = _.map(history, function(e) {
                e.entity_url = entity_url(e);
                e.most_recent_visit = date_wrapper(e.most_recent_visit);
                e.first_visit = date_wrapper(e.first_visit);
                if(e.country_code) {
                    countries[e.country_code] = e.country_name;
                }
                increment(summary, e.type_abbr);
                return e;
            }, this);
            summary[''] = history.length;
            console.log(summary);
            
            _.each(_.pairs(countries).sort(country_cmp), function(item) {
                var opt = document.createElement('option');
                opt.value = item[0];
                opt.textContent = item[1];
                co_opts.appendChild(opt);
            });
            
            this.$el = $('#history');
            this.$el.find('thead th').click(sort_handler);
            _.each(document.querySelectorAll('#id_filter option'), function(e) {
                if(summary[e.value]) {
                    e.text += ' ' + ' (' + summary[e.value] + ')';
                }
            });
        },

        filter: function(bits) {
            var type     = bits.type;
            var co       = bits.co;
            var dt       = bits.date ? new Date(bits.date) : null;
            var tf       = bits.timeframe;
            var entities = this.all_entities;
            
            console.log('filter bits', bits);
            this.filters = {'type': type, 'co': co};
            if(type || co || dt) {
                entities = _.filter(entities, function(e) {
                    var good = true;
                    if(type) {
                        good &= (e.type_abbr === type);
                    }

                    if(co) {
                        good &= (e.country_code === co || (e.type_abbr === 'co' && e.code === co));
                    }
                    
                    if(tf && dt) {
                        if(tf == '+') {
                            good &= (e.most_recent_visit.date >= dt);
                        }
                        else if(tf == '-') {
                            good &= (e.most_recent_visit.date <= dt);
                        }
                    }

                    return !!good;
                });
            }
            
            this.show_entities(entities);
        },
        
        show_entities: function(entities) {
            var i, start;
            var count = entities.length;
            var el = document.querySelector('#history tbody');
            var parent = el.parentElement;
            this.current_entities = entities;
            $$('id_count').textContent = (count + ' entr' + (count > 1 ? 'ies' : 'y'));

            start = new Date();
            parent.removeChild(el);
            el = DOM.create('tbody');
            for(i = 0; i < entities.length; i++) {
                el.appendChild(create_entity_row(entities[i]));
            }
            parent.appendChild(el);
            console.log('delta', new Date() - start);
        },

        sort: function(col, order) {
        }
        
    };
    

    //--------------------------------------------------------------------------
    var make_hash = function(bits) {
        var a = []
        bits.type && a.push('type', bits.type);
        bits.co   && a.push('co', bits.co);
        if(bits.date && bits.timeframe) {
            a.push('date', bits.timeframe + bits.date);
        }

        return a.length ? '#' + a.join('/') : './';
    };
    
    //--------------------------------------------------------------------------
    var obj_from_hash = function(hash) {
        var obj = {};
        if(hash) {
            var a = hash.split('/');
            for(var i = 0, j = a.length; i < j; i += 2) {
                if(a[i]) {
                    obj[a[i]] = a[i + 1];
                }
            }
            if(obj.date) {
                obj.timeframe = obj.date[0];
                obj.date = obj.date.substr(1);
            }
        }
        return obj;
    };
    
    //--------------------------------------------------------------------------
    var update_hash = function(bits) {
        var hash = make_hash(bits);
        console.log('hash', hash);
        window.history.pushState({}, '', hash);
    };
    
    //--------------------------------------------------------------------------
    var pad = function(n) {
        return n < 10 ? '0' + n : n;
    }

    //--------------------------------------------------------------------------
    var get_datepicker_iso = function() {
        var dt = $('#id_date').datepicker('getDate');
        if(dt) {
            return dt.getFullYear()
                 + '-' + pad(dt.getMonth() + 1)
                 + '-' + pad(dt.getDate());
        }
        return '';
    }
    
    //--------------------------------------------------------------------------
    var get_filter_bits = function() {
        return {
            type:      $$('id_filter').value,
            co:        $$('id_co').value,
            timeframe: $$('id_timeframe').value,
            date:      get_datepicker_iso()
        };
    };
    
    //--------------------------------------------------------------------------
    var on_filter_change = function() {
        var bits = get_filter_bits();
        console.log(bits);
        
        update_hash(bits);
        profile_history.filter(bits);
    };
    
    //--------------------------------------------------------------------------
    var on_hash_change = function() {
        var hash = window.location.hash;
        var bits = obj_from_hash(hash.length > 1 ? hash.substr(1) : '');
        var dt = $$('id_date');

        console.log('bits', bits);
        _.each(document.querySelectorAll('.filter_ctrl'), function(e) {
            e.value = '';
        });
        
        if(bits.type) {
            $$('id_filter').value = bits.type;
        }
        if(bits.co) {
            $$('id_co').value = bits.co;
        }
        if(bits.timeframe) {
            $$('id_timeframe').value = bits.timeframe;
        }
        if(bits.date) {
            dt.value = bits.date;
        }
        else {
            dt.style.display = 'none';
        }
        profile_history.filter(bits);
    };

    //--------------------------------------------------------------------------
    var init_profile_filter = function() {
        $(window).on('hashchange', on_hash_change);
        $('.filter_ctrl').on('change', on_filter_change);
        $('#id_timeframe').on('change', function() {
            $$('id_date').style.display = this.value ? 'inline-block' : 'none';
        })
        on_hash_change();
        $('#id_date')
            .datepicker(profile_datepicker_opts)
            .on('change input propertychange', on_filter_change);
        
    };
    
    //--------------------------------------------------------------------------
    var sort_handler = function() {
        var bits;
        var col = 'recent';
        var order = 'desc';
        var class_names = this.className.split(' ');
        
        for(var i = 0, j = class_names.length; i < j; i++) {
            bits = class_names[i].split('_');
            if(bits[0] === 'col') {
                col = bits[1];
            }
            else if(bits[0] === 'sort') {
                order = bits[1];
                class_names[i] = 'sort_' + (order === 'asc' ? 'desc' : 'asc');
            }
        }
        
        this.className = class_names.join(' ');
        profile_history.sort(col, order);
    };
    
    return {
        profile_history: profile_history,
        initialize: function(history, conf) {
            profile_history.initialize(history, conf);
            init_profile_filter();
        }
    };
}(jQuery));
