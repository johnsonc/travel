//------------------------------------------------------------------------------
// Sample entity object
//------------------------------------------------------------------------------
// entity = {
//    "flag__thumb": "img/flags/co/fr/fr-32.png",
//    "first_visit": {"value": "2013-08-04T10:00:00Z", "content_type": "datetime"},
//    "code": "FR",
//    "rating": 3,
//    "name": "France",
//    "locality": "",
//    "country__flag__thumb": null,
//    "country__code": null,
//    "country__name": null,
//    "num_visits": 15,
//    "type__title": "Country",
//    "type__abbr": "co",
//    "recent_visit": {"value": "2015-12-23T11:00:00Z", "content_type": "datetime"},
//    "id": 86
//}
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
        'recent': function(a, b) { return b.arrival.date - a.arrival.date; },
        'first':  function(a, b) { return b.first_visit.date - a.first_visit.date; },
        'logs':   function(a, b) { return b.num_visits - a.num_visits; },
        'rating': function(a, b) { return a.rating - b.rating; }
    };
    
    var DATE_STRING  = 'MMM Do YYYY';
    var TIME_STRING  = 'ddd h:ssa';
    var MEDIA_PREFIX = '/media/';
    var DATE_FORMAT  = 'YYYY-MM-DD';
    var STARS        = '★★★★★';
    
    
    //--------------------------------------------------------------------------
    var stars = function(rating) { return STARS.substr(rating - 1); };
    
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
            var i = 0, length = items.length;
            ctx = ctx || items;
            for(; i < length; i++) {
                callback.call(ctx, items[i], i);
            }
        },
        map: function(items, callback, ctx) {
            var results = [], i = 0, length = items.length;
            ctx = ctx || items;
            for(; i < length; i++) {
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
    };
    
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
        },
        remove_children: function(el) {
            while(el.lastChild) {
              el.removeChild(el.lastChild);
            }
        }
    };
    
    //--------------------------------------------------------------------------
    var date_tags = function(dtw) {
        return [
            DOM.create('div', dtw.format(DATE_STRING)),
            DOM.create('div', dtw.format(TIME_STRING))
        ];
    };
    
    //--------------------------------------------------------------------------
    var create_log_row = function(log) {
        var e = log.entity;
        var name_td = DOM.create('td');
        var flag_td = DOM.create('td');
        var extras = [];
        var attrs = {
            'data-id' : e.id,
            'class': e.type__abbr + ' co-' + (
                e.country__code ?
                e.country__code :
                (e.type__abbr == 'co' ? e.code : '')
            )
        };

        name_td.appendChild(DOM.create('a', e.name, {'href': e.entity_url}));
        if(e.flag__thumb) {
            flag_td.appendChild(DOM.create('img', {'src': e.flag__thumb, 'class': 'flag'}));
        }
        
        e.locality && extras.push(e.locality);
        e.country__name && extras.push(e.country__name);
        if(extras.length) {
            name_td.appendChild(DOM.create('span', extras.join(', ')))
        }
        
        if(e.country__flag__thumb) {
            name_td.appendChild(DOM.create('img', {
                'src': e.country__flag__thumb,
                'class': 'flag flag-sm'
            }));
        }

        return DOM.create('tr', attrs, [
            flag_td,
            DOM.create('td', e.type__title),
            name_td,
            DOM.create('td', {'class': 'when'}, date_tags(log.arrival)),
            DOM.create('td', {'class': 'when'}, date_tags(e.logs[e.logs.length-1].arrival)),
            DOM.create('td', e.logs.length),
            DOM.create('td', stars(log.rating))
        ]);
    };
    
    //--------------------------------------------------------------------------
    var sorted_dict = function(dct) {
        var keys = Iter.keys(dct);
        keys.sort();
        return Iter.map(keys, function(key) {
            return [key, dct[key]];
        });
    };
    
    //--------------------------------------------------------------------------
    var initialize_log_entry = function(e, media_prefix) {
        e.logs = [];
        e.entity_url = entity_url(e);
        e.flag__thumb = media_prefix + e.flag__thumb;
        if(e.country__flag__thumb) {
            e.country__flag__thumb = media_prefix + e.country__flag__thumb;
        }
        return e;
    };
    
    //--------------------------------------------------------------------------
    var get_ordering = function(el) {
        var ordering = {'column': el.dataset['column'], 'order': el.dataset['order']}
        var current = el.parentElement.querySelector('.current');
        if(el === current) {
            ordering.order = (ordering.order === 'desc') ? 'asc' : 'desc';
            el.dataset['order'] = ordering.order;
        }
        else {
            current.className = '';
            el.className = 'current'
        }
        return ordering;
    };
    
    //--------------------------------------------------------------------------
    var show_summary = function(summary) {
        var el = $$('summary');
        DOM.remove_children(el);
        el.appendChild(DOM.create('strong', 'Summary: '))
        summary.iter(function(key) {
            var items = Iter.keys(this[key]).length;
            if(items) {
                el.appendChild(DOM.create(
                    'span',
                    {'class': 'label label-info'},
                    type_mapping[key] + ': ' + items
                ));
            }
        });
    };
    
    //--------------------------------------------------------------------------
    var create_country_options = function(countries) {
        var cos = $$('id_co');
        Iter.each(sorted_dict(countries), function(item) {
            cos.appendChild(DOM.create('option', item[1], {'value': item[0]}));
        });
        
    };
    
    //--------------------------------------------------------------------------
    var init_ordering_by_columns = function(history) {
        var columns = document.querySelectorAll('#history thead th[data-column]');
        Iter.each(columns, function(e) {
            DOM.evt(e, 'click', function(evt) {
                var ordering = get_ordering(this);
                if(ordering.order === 'asc') {
                    update_hash(get_filter_bits());
                }
                history.sort_current(ordering.column, ordering.order);
            });
        });
    };
    
    //==========================================================================
    var Summary = function() {
        Iter.each(Summary.keys, function(key) {
            this[key] = {};
        }, this);
    };
    
    //--------------------------------------------------------------------------
    Summary.prototype.add = function(e) {
        increment(this[e.type__abbr], e.id);
    };
    
    //--------------------------------------------------------------------------
    Summary.prototype.iter = function(callback) {
        Iter.each(Summary.keys, callback, this);
    };
    
    Summary.keys = ['cn', 'co', 'st', 'ap', 'ct', 'np', 'lm', 'wh'];
    
    //--------------------------------------------------------------------------
    var show_logs = function(travel_logs) {
        var count = travel_logs.logs.length;
        var parent = $$('history');
        var el = parent.querySelector('tbody');
        var start = new Date();
        
        $$('id_count').textContent = (count + ' entr' + (count > 1 ? 'ies' : 'y'));
        DOM.remove(el);
        el = DOM.create('tbody');
        Iter.each(travel_logs.logs, function(log) {
            el.appendChild(create_log_row(log));
        });
        parent.appendChild(el);
        show_summary(travel_logs.summary);
        console.log('delta', new Date() - start);
    };
    
    //==========================================================================
    var TravelLogs = function(logs, summary) {
        this.logs = logs;
        this.summary = summary;
    };
    
    //--------------------------------------------------------------------------
    TravelLogs.prototype.sort = function(column, order) {
        console.log('ordering', column, order);
        this.logs.sort(function(a, b) {
            var result = 0;
            if(a[column] > b[column]) {
                result = 1;
            }
            else {
                if(a[column] < b[column]) {
                    result = -1;
                }
            }
            return (result && order === 'desc') ? -result : result;
        });
    };
    
    //--------------------------------------------------------------------------
    TravelLogs.prototype.filter = function(bits) {
        var logs    = this.logs;
        var summary = this.summary;
        
        console.log('filter bits', bits);
        if(bits.type || bits.co || bits.timeframe) {
            summary = new Summary;
            logs = Iter.filter(logs, function(log) {
                var e = log.entity;
                var good = true;
                if(bits.type) {
                    good &= (e.type__abbr === bits.type);
                }

                if(bits.co) {
                    good &= (
                        e.country__code === bits.co ||
                        (e.type__abbr === 'co' && e.code === bits.co)
                    );
                }
                
                if(good && bits.timeframe && bits.date) {
                    switch(bits.timeframe) {
                        case '+':
                            good &= log.arrival.isAfter(bits.date);
                            break
                        case '-':
                            good &= log.arrival.isBefore(bits.date);
                            break;
                        case '=':
                            good &= (log.arrival.year() === bits.date.year());
                            break;
                        default:
                            good = false;
                    }
                }
                
                if(good) {
                    summary.add(e);
                    return true;
                }
                
                return false;
            });
            return new TravelLogs(logs, summary);
        }
        return this;
    };
    
    //--------------------------------------------------------------------------
    var controller = (function() {
        var entity_dict = {};
        var current_logs, all_logs;
        
        return {
            initialize: function(entities, logs, conf) {
                var media_prefix = conf.media_prefix || MEDIA_PREFIX;
                var countries = {};
                var summary = new Summary;
                Iter.each(entities, function(e) {
                    e = initialize_log_entry(e, media_prefix);
                    if(e.country__code) {
                        countries[e.country__code] = e.country__name;
                    }
                    entity_dict[e.id] = e;
                });
            
                logs = Iter.map(logs, function(log) {
                    log.entity = entity_dict[log.entity__id];
                    if(!log.entity) {
                        console.log(log);
                    }
                    log.entity.logs.push(log);
                    log.arrival = moment(log.arrival.value);
                    summary.add(log.entity);
                    return log;
                }, this);
            
                current_logs = all_logs = new TravelLogs(logs, summary);
                console.log(summary);
                create_country_options(countries);
                init_ordering_by_columns(this);
            },
        
            filter_logs: function(bits) {
                current_logs = all_logs.filter(bits)
                show_logs(current_logs);
            },
        
            sort_current: function(column, order) {
                console.log('ordering', column, order);
                current_logs.sort();
                show_logs(current_logs);
            }
        };
    }());
    

    //--------------------------------------------------------------------------
    var make_hash = function(bits) {
        var a = [];
        bits.type && a.push('type', bits.type);
        bits.co   && a.push('co', bits.co);
        bits.asc  && a.push('asc', bits.asc);
        if(bits.date && bits.timeframe) {
            a.push('date', bits.timeframe + bits.date.format(DATE_FORMAT));
        }

        return a.length ? '#' + a.join('/') : './';
    };
    
    //--------------------------------------------------------------------------
    var obj_from_hash = function(hash) {
        var arr, obj = {};
        if(hash && hash[0] == '#') {
            hash = hash.substr(1);
        }
        
        if(hash) {
            arr = hash.split('/');
            for(var i = 0, j = arr.length; i < j; i += 2) {
                if(arr[i]) {
                    obj[arr[i]] = arr[i + 1];
                }
            }
            if(obj.date) {
                obj.timeframe = obj.date[0];
                obj.date = moment(obj.date.substr(1));
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
    };

    //--------------------------------------------------------------------------
    var get_datepicker = function() {
        var dt = document.getElementById('id_date').value;
        return dt ? moment(dt) : null;
    }
    
    //--------------------------------------------------------------------------
    var get_filter_bits = function() {
        var bits = {
            type:      $$('id_filter').value,
            co:        $$('id_co').value,
            timeframe: $$('id_timeframe').value,
            date:      get_datepicker()
        };
        var el = document.querySelector('#history thead .current');
        if(el && el.dataset['order'] == 'asc') {
            bits['asc'] = el.dataset['column'];
        }
        return bits;
    };

    //--------------------------------------------------------------------------
    var set_filter_fields = function(bits) {
        $$('id_filter').value = bits.type || '';
        $$('id_timeframe').value = bits.timeframe || '';
        $$('id_co').value = bits.co || '';
        if(bits.date) {
            $$('id_date').value = bits.date.format(DATE_FORMAT);
        }
        else {
            $$('id_date').style.display = 'none';
        }
    };
    
    //--------------------------------------------------------------------------
    var on_filter_change = function() {
        var bits = get_filter_bits();
        console.log(bits);
        
        update_hash(bits);
        controller.filter_logs(bits);
    };
    
    //--------------------------------------------------------------------------
    var on_hash_change = function() {
        var bits = obj_from_hash(window.location.hash);
        set_filter_fields(bits);
        controller.filter_logs(bits);
    };

    //--------------------------------------------------------------------------
    var init_profile_filter = function(conf) {
        var date_el = $$('id_date');
        var picker = new Pikaday({
            field: date_el,
            format: DATE_FORMAT,
            minDate: new Date(1920,1,1),
            yearRange: [1920, (new Date()).getFullYear()],
            onSelect: function(dt) { console.log(dt, this); }
        });
        
        DOM.evt(window, 'hashchange', on_hash_change);
        DOM.evt($$('id_timeframe'), 'change', function() {
            date_el.style.display = this.value ? 'inline-block' : 'none';
        });
        
        DOM.evt(date_el, 'change', on_filter_change);
        DOM.evt(date_el, 'input', on_filter_change);
        DOM.evt(date_el, 'propertychange', on_filter_change);
        Iter.each(document.querySelectorAll('.filter_ctrl'), function(e) {
            DOM.evt(e, 'change', on_filter_change);
        });

        on_hash_change();
    };
    
    root.profile_history = controller;
    return {
        profile_history: function(entities, logs, conf) {
            controller.initialize(entities, logs, conf);
            init_profile_filter(conf);
        }
    };
}());
