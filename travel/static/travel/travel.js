//------------------------------------------------------------------------------
// Sample entity object
//------------------------------------------------------------------------------
// entity = {
//    "rating": 3,
//    "id": 1463,
//    "code": "BUD",
//    "type__title": "Airport",
//    "num_visits": 1,
//    "flag__thumb": "img/ap-32.png",
//    "type__abbr": "ap",
//    "id": 276
//    "country__code": "HU",
//    "country__name": "Hungary",
//    "recent_visit": "2013-12-29 08:00:00",
//    "first_visit": "2013-12-29 08:00:00",
//    "name": "Budapest Ferenc Liszt International Airport"
// }
//------------------------------------------------------------------------------

;var Travelogue = (function() {
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
    
    var sorters = {
        'type': function(a, b) {
            if(b.type__title > a.type__title) {
                return 1;
            }
            if(a.type__title < b.type__title) {
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
        'recent': function(a, b) { return b.recent_visit.date - a.recent_visit.date; },
        'first':  function(a, b) { return b.first_visit.date - a.first_visit.date; },
        'logs':   function(a, b) { return b.num_visits - a.num_visits; },
        'rating': function(a, b) { return a.rating - b.rating; }
    };
    
    var DATE_STRING = 'MMM Do YYYY';
    var TIME_STRING = 'ddd h:ssa';
    
    //--------------------------------------------------------------------------
    var stars = (function() {
        var STARS = '★★★★★';
        return function(rating) { return STARS.substr(rating - 1); };
    }());
    
    //--------------------------------------------------------------------------
    var increment = function(obj, field) {
        obj[field] = obj[field] ? obj[field]  + 1 : 1;
    };
    
    //--------------------------------------------------------------------------
    var entity_url = function(e) {
        var bit = e.code;
        if(e.type__abbr == 'wh' || e.type__abbr == 'st') {
            bit = e.country__code + '-' + bit;
        } 
        return '/i/' + e.type__abbr + '/' + bit + '/';
    };
    
    //--------------------------------------------------------------------------
    var Iter = {
        each: function(items, callback, ctx) {
            var results = [];
            ctx = ctx || items;
            for(var i = 0, length = items.length; i < length; i++) {
                results.push(callback.call(ctx, items[i], i));
            }
            return results;
        },
        filter: function(items, callback, ctx) {
            var results = [];
            ctx = ctx || items;
            for(var i = 0, length = items.length; i < length; i++) {
                if(callback.call(ctx, items[i], i) === true) {
                    results.push(items[i]);
                }
            }
            return results;
        },
        keys: function(obj, callback, ctx) {
            var items = [];
            ctx = ctx || obj;
            for(var k in obj) {
                if(obj.hasOwnProperty(k)) {
                    items.push(k);
                    if(callback) {
                        callback.call(ctx, k, obj[k]);
                    }
                }
            }
            return items;
        }
    }
    
    //--------------------------------------------------------------------------
    var DOM = root.DOM = {
        create: function(tag) {
            var j, key, arg;
            var el = document.createElement(tag);
            for(var i = 1; i < arguments.length; i++) {
                arg = arguments[i];
                if(_.isPlainObject(arg)) {
                    DOM.set_attrs(el, arg);
                }
                else if(_.isArray(arg)) {
                    DOM.append_children(el, arg);
                }
                else {
                    el.textContent = arg.toString();
                }
            }
            return el;
        },
        append_children: function(el, children) {
            Iter.each(children, function(child) { el.appendChild(child); });
        },
        set_attrs: function(el, attrs) {
            Iter.keys(attrs, function(k,v) { el.setAttribute(k, v); });
        },
        css: function(el, vals) {
            var style = el.style;
            Iter.keys(vals, function(k, v) { style[k] = v; });
        },
        evt: function(el, kind, handler, t) {
            el.addEventListener(kind, handler, t)
        },
        remove: function(el) {
            el.parentNode.removeChild(el);
        }
    };
    
    //--------------------------------------------------------------------------
    var date_tags = function(dtw) {
        return [
            DOM.create('nobr', dtw.format(DATE_STRING)),
            DOM.create('nobr', dtw.format(TIME_STRING))
        ];
    };
    
    //--------------------------------------------------------------------------
    var create_entity_row = function(e) {
        var name_td = DOM.create('td');
        var flag_td = DOM.create('td');
        var extras = [];
        var attrs = {
            'data-id' : e.id,
            'class': e.type__abbr + ' co-' + (e.country__code ? e.country__code : (e.type__abbr == 'co' ? e.code : ''))
        };

        name_td.appendChild(DOM.create('a', e.name, {'href': e.entity_url}));

        if(e.flag__thumb) {
            flag_td.appendChild(DOM.create('img', {'src': e.flag__thumb, 'class': 'flag'}));
        }
        
        if(e.locality) {
            extras.push(e.locality);
        }

        if(e.country__name) {
            extras.push(e.country__name);
        }

        if(extras.length) {
            name_td.appendChild(DOM.create('span', extras.join(', ')))
        }
        
        if(e.country__flag__thumb) {
            name_td.appendChild(DOM.create('img', {'src': e.country__flag__thumb, 'class': 'flag flag-sm'}));
        }

        return DOM.create('tr', attrs, [
            flag_td,
            DOM.create('td', e.type__title),
            name_td,
            DOM.create('td', date_tags(e.recent_visit)),
            DOM.create('td', date_tags(e.first_visit)),
            DOM.create('td', e.num_visits),
            DOM.create('td', stars(e.rating))
        ]);
    };
    
    //--------------------------------------------------------------------------
    var sorted_dict = function(dct) {
        var keys = Iter.keys(dct);
        keys.sort();
        return Iter.each(keys, function(key) {
            return [key, dct[key]];
        });
    };
    
    //--------------------------------------------------------------------------
    var profile_history = {
        media_prefix: '/media/',
        initialize: function(history, conf) {
            var media_prefix = conf.media_prefix || this.media_prefix;
            var co_opts = $$('id_co');
            var summary = {};
            var countries = {};

            this.filters = {'type': null, 'country__code': null};
            this.all_entities = Iter.each(history, function(e) {
                e.entity_url = entity_url(e);
                e.recent_visit = moment(e.recent_visit.value);
                e.first_visit = moment(e.first_visit.value);
                e.flag__thumb = media_prefix + e.flag__thumb;
                if(e.country__flag__thumb) {
                    e.country__flag__thumb = media_prefix + e.country__flag__thumb;
                }
                if(e.country__code) {
                    countries[e.country__code] = e.country__name;
                }
                increment(summary, e.type__abbr);
                return e;
            });
            summary[''] = history.length;
            console.log(summary);
            
            Iter.each(sorted_dict(countries), function(item) {
                var opt = document.createElement('option');
                opt.value = item[0];
                opt.textContent = item[1];
                co_opts.appendChild(opt);
            });
            
            Iter.each(document.querySelectorAll('#history thead th'), function(e) {
                DOM.evt(e, 'click', sort_handler);
            });

            Iter.each(document.querySelectorAll('#id_filter option'), function(e) {
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
                entities = Iter.filter(entities, function(e) {
                    var good = true;
                    if(type) {
                        good &= (e.type__abbr === type);
                    }

                    if(co) {
                        good &= (e.country__code === co || (e.type__abbr === 'co' && e.code === co));
                    }
                    
                    if(tf && dt) {
                        if(tf == '+') {
                            good &= (e.recent_visit >= dt);
                        }
                        else if(tf == '-') {
                            good &= (e.recent_visit <= dt);
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
            var parent = $$('history');
            var el = parent.querySelector('tbody');
            this.current_entities = entities;
            $$('id_count').textContent = (count + ' entr' + (count > 1 ? 'ies' : 'y'));

            start = new Date();
            DOM.remove(el);
            el = DOM.create('tbody');
            for(i = 0; i < count; i++) {
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
        window.history.pushState({}, '', make_hash(bits));
    };
    
    //--------------------------------------------------------------------------
    var pad = function(n) {
        return n < 10 ? '0' + n : n;
    }

    //--------------------------------------------------------------------------
    var get_datepicker_iso = function() {
        var dt = document.getElementById('id_date').value;
        if(dt) {
            dt = new Date(dt);
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
        Iter.each(document.querySelectorAll('.filter_ctrl'), function(e) {
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
        var picker = new Pikaday({
            field: document.getElementById('id_date'),
            format: 'YYYY-MM-DD',
            minDate: new Date(1920,1,1),
            yearRange: [1920, (new Date()).getFullYear()],
            onSelect: function(dt) {
                console.log(dt);
                console.log(this);
            }
        });
        
        var date_el = $$('id_date');
        DOM.evt(window, 'hashchange', on_hash_change);
        Iter.each(document.querySelectorAll('.filter_ctrl'), function(e) {
            DOM.evt(e, 'change', on_filter_change);
        });
        
        DOM.evt($$('id_timeframe'), 'change', function() {
            date_el.style.display = this.value ? 'inline-block' : 'none';
        });
        
        on_hash_change();
        // .datepicker({changeMonth: true, changeYear: true, showButtonPanel: true, yearRange: 'c-50:nnnn' });
        
        DOM.evt(date_el, 'change', on_filter_change);
        DOM.evt(date_el, 'input', on_filter_change);
        DOM.evt(date_el, 'propertychange', on_filter_change);
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
}());
