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
    var profile_history = {
        selector: '#history tbody',
        media_prefix: '/media/',
        initialize: function(history, conf) {
            var media_prefix = conf.media_prefix || this.media_prefix;
            var $co_opts = $('#id_co');
            this.filters = {'type': null, 'country_code': null};
            this.countries = {};
            this.all_entities = _.map(history, function(e) {
                e.entity_url = entity_url(e);
                e.flag_url = e.flag_url ? media_prefix + e.flag_url: '';
                e.flag_co_url = e.flag_co_url ? media_prefix + e.flag_co_url: '';
                e.most_recent_visit = date_wrapper(e.most_recent_visit);
                e.first_visit = date_wrapper(e.first_visit);
                e.html = make_entity_row(e);
                if(e.country_code) {
                    this.countries[e.country_code] = e.country_name;
                }
                return e;
            }, this);
            
            
            _.each(
                _.pairs(this.countries).sort(function(a,b) {
                    return (a[1] > b[1]) ? 1 : (a[1] < b[1] ? -1 : 0); 
                }),
                function(item) {
                    $co_opts.append('<option value="' + item[0] + '">' + item[1] + '</option>');
                }
            );
            
            this.$el = $('#history');
            this.$el.find('thead th').click(sort_handler);
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
            var count = entities.length;
            this.current_entities = entities;

            $('#id_count').text(count + ' entr' + (count > 1 ? 'ies' : 'y'));
            var html = _.reduce(entities, function(memo, e) {
                return memo + e.html;
            }, '');

            this.$el.find('tbody').html(html);
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
            type:      $$('id_type').value,
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
        $('.filter_ctrl').each(function() { this.value = ''; });
        
        if(bits.type) {
            $$('id_type').value = bits.type;
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
    var entity_url = function(e) {
        return '/i/' + e.type_abbr + '/' + (
            (e.type_abbr == 'wh' || e.type_abbr == 'st')
          ? (e.country_code + '-' + e.code)
          : e.code
        ) + '/';
    };

    //--------------------------------------------------------------------------
    var date_html = function(dtw) {
        return make_tag('nobr', dtw.date_string, '<br>') + make_tag('nobr', dtw.time_string);
    };
    
    //--------------------------------------------------------------------------
    var make_tag = root.make_tag = function(name) {
        var args = Array.prototype.slice.call(arguments, 1);
        var tag = '<' + name;
        var attrs;
        if(typeof args[0] === 'object') {
            attrs = args.shift();
            for(var key in attrs) {
                if(attrs.hasOwnProperty(key)) {
                    tag += ' ' + key + '="' + attrs[key] + '"'
                }
            }
        }
        return tag + '>' + args.join('') + '</' + name + '>';
    };
    
    //--------------------------------------------------------------------------
    var img_tag = function(src, classes) {
        var tag = '<img src="' + src + '"';
        if(classes) {
            tag += ' class="' + classes + '"';
        }
        return tag + '>';
    }
    
    //--------------------------------------------------------------------------
    var make_entity_row = function(e) {
        var co_html = '';
        var name_html = '<a href="' + e.entity_url + '">' + e.name + '</a>';
        var html = make_tag('td', e.flag_url ? img_tag(e.flag_url, 'flag') : '');
        var attrs = {
            'data-id' : e.id,
            'class': e.type_abbr + ' co-' + e.country_code ? e.country_code : (e.type_abbr == 'co' ? e.code : '')
        };
        
        if(e.locality) {
            co_html += e.locality;
        }
        if(e.country_name) {
            co_html += co_html.length ? ', ' + e.country_name : e.country_name;
            if(e.flag_co_url) {
                co_html += ' ' + img_tag(e.flag_co_url, 'flag');
            }
        }

        if(co_html.length) {
            name_html += '<br>' + co_html;
        }

        return make_tag('tr', attrs, (
              html
            + make_tag('td', e.type_title)
            + make_tag('td', name_html)
            + make_tag('td', date_html(e.most_recent_visit))
            + make_tag('td', date_html(e.first_visit))
            + make_tag('td', e.num_visits)
            + make_tag('td', stars(e.rating))
        ));
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
