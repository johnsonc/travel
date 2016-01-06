//------------------------------------------------------------------------------
// Sample entity object
//------------------------------------------------------------------------------
// entity = {
//     "flag__thumb": "img/wh-32.png",
//     "code": "3",
//     "name": "Aachen Cathedral",
//     "locality": "State of North Rhine-Westphalia (Nordrhein-Westfalen)",
//     "country__flag__thumb": "img/flags/co/de/de-32.png",
//     "country__code": "DE",
//     "country__name": "Germany",
//     "type__abbr": "wh",
//     "id": 11942
// }
//}
//------------------------------------------------------------------------------

;var Travelogue = (function() {
    var root = this;
    var $$ = document.getElementById.bind(document);
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
            a = a.entity, b = b.entity;
            if(b.type__abbr > a.type__abbr) {
                return 1;
            }
            if(a.type__abbr < b.type__abbr) {
                return -1;
            }
            if(b.name > a.name) {
                return 1;
            }
            return (a.name < b.name) ? -1 : 0;
        },
        'name': function(a, b) {
            a = a.entity, b = b.entity;
            return (b.name > a.name) ? 1 : (a.name < b.name) ? -1 : 0;
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
    var iter_keys = function(obj, callback, ctx) {
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
    };
    
    //==========================================================================
    var Set = function(iter) {
        this.items = {};
        this.size = 0;
        if(iter) {
            iter.forEach(function(i) { this.add(i); }, this);
        }
    };
    
    Set.prototype = {
        add: function(value) {
            if(!this.has(value)) {
                this.items[value] = true;
                this.size++;
            }
        },
        has: function(value) {
            return this.items.hasOwnProperty(value);
        },
        values: function() {
            var a = [];
            for(var prop in this.items) {
                if(this.items.hasOwnProperty(prop)) {
                    a.push(prop);
                }
            }
            return a;
        },
        forEach: function(callback, ctx) {
            ctx = ctx || this;
            for(var prop in this.items) {
                if(this.items.hasOwnProperty(prop)) {
                    callback.call(ctx, prop);
                }
            }
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
                else if(Array.isArray(arg)) {
                    DOM.append_children(el, arg);
                }
                else {
                    el.textContent = arg.toString();
                }
            }
            return el;
        },
        append_children: function(el, children) {
            Array.from(children).forEach(function(child) { el.appendChild(child); });
        },
        set_attrs: function(el, attrs) {
            iter_keys(attrs, function(k,v) { el.setAttribute(k, v); });
        },
        css: function(el, vals) {
            var style = el.style;
            iter_keys(vals, function(k, v) { style[k] = v; });
        },
        evt: function(el, kind, handler, t) {
            el.addEventListener(kind, handler, t);
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
            name_td.appendChild(DOM.create('span', extras.join(', ')));
        }
        
        if(e.country__flag__thumb) {
            name_td.appendChild(DOM.create('img', {
                'src': e.country__flag__thumb,
                'class': 'flag flag-sm'
            }));
        }

        return DOM.create('tr', attrs, [
            flag_td,
            DOM.create('td', type_mapping[e.type__abbr]),
            name_td,
            DOM.create('td', {'class': 'when'}, date_tags(log.arrival)),
            DOM.create('td', {'class': 'when'}, date_tags(e.logs[e.logs.length-1].arrival)),
            DOM.create('td', e.logs.length),
            DOM.create('td', stars(log.rating))
        ]);
    };
    
    //--------------------------------------------------------------------------
    var sorted_dict = function(dct) {
        var keys = iter_keys(dct);
        keys.sort();
        return keys.map(function(key) {
            return [key, dct[key]];
        });
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
        var ordering = {'column': el.dataset.column, 'order': el.dataset.order};
        var current = el.parentElement.querySelector('.current');
        if(el === current) {
            ordering.order = (ordering.order === 'desc') ? 'asc' : 'desc';
            el.dataset.order = ordering.order;
        }
        else {
            current.className = '';
            el.className = 'current';
        }
        return ordering;
    };
    
    //--------------------------------------------------------------------------
    var show_summary = function(summary) {
        var el = $$('summary');
        DOM.remove_children(el);
        el.appendChild(DOM.create('strong', 'Summary: '));
        summary.iter(function(key) {
            var items = iter_keys(this[key]).length;
            if(items) {
                el.appendChild(DOM.create(
                    'span',
                    {'class': 'label label-info'},
                    type_mapping[key] + ': ' + items
                ));
            }
        });
    };
    
    //==========================================================================
    var Summary = function() {
        Summary.keys.forEach(function(key) {
            this[key] = {};
        }, this);
    };
    
    //--------------------------------------------------------------------------
    Summary.prototype.add = function(e) {
        var kind = this[e.type__abbr];
        kind[e.id] = kind[e.id] ? kind[e.id] + 1 : 1;
    };
    
    //--------------------------------------------------------------------------
    Summary.prototype.iter = function(callback) {
        Summary.keys.forEach(callback, this);
    };
    
    Summary.keys = iter_keys(type_mapping);
    
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
            summary = new Summary();
            logs = logs.filter(function(log) {
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
                            break;
                        case '-':
                            good &= log.arrival.isBefore(bits.date);
                            break;
                        case '=':
                            good &= (log.arrival.year() === bits.date);
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
    var show_logs = function(travel_logs) {
        var count = travel_logs.logs.length;
        var parent = $$('history');
        var el = parent.querySelector('tbody');
        var start = new Date();
        
        $$('id_count').textContent = (count + ' entr' + (count > 1 ? 'ies' : 'y'));
        DOM.remove(el);
        el = DOM.create('tbody');
        travel_logs.logs.forEach(function(log) {
            el.appendChild(create_log_row(log));
        });
        parent.appendChild(el);
        show_summary(travel_logs.summary);
        console.log('delta', new Date() - start);
    };
    
    //--------------------------------------------------------------------------
    var controller = (function() {
        var entity_dict = {};
        var current_logs, all_logs;
        var ctrl = {
            initialize: function(entities, logs, conf) {
                var media_prefix = conf.media_prefix || MEDIA_PREFIX;
                var countries = {};
                var years = new Set();
                var summary = new Summary();
                entities.forEach(function(e) {
                    e = initialize_log_entry(e, media_prefix);
                    if(e.country__code) {
                        countries[e.country__code] = e.country__name;
                    }
                    entity_dict[e.id] = e;
                });
            
                logs = logs.map(function(log) {
                    log.entity = entity_dict[log.entity__id];
                    if(!log.entity) {
                        console.log(log);
                    }
                    log.entity.logs.push(log);
                    log.arrival = moment(log.arrival.value);
                    years.add(log.arrival.year());
                    summary.add(log.entity);
                    return log;
                }, this);
            
                current_logs = all_logs = new TravelLogs(logs, summary);
                console.log(summary);
                create_country_options(countries);
                init_ordering_by_columns(this);
                create_years_option(years);
                init_profile_filter(conf);
            },
        
            filter_logs: function(bits) {
                current_logs = all_logs.filter(bits);
                show_logs(current_logs);
            },
        
            sort_current: function(column, order) {
                console.log('ordering', column, order);
                current_logs.sort();
                show_logs(current_logs);
            }
        };
        
        //----------------------------------------------------------------------
        var on_filter_change = function() {
            var bits = HashBits.from_filters();
            console.log(bits);

            bits.update();
            ctrl.filter_logs(bits);
        };

        //----------------------------------------------------------------------
        var on_hash_change = function() {
            var bits = HashBits.from_hash();
            set_filter_fields(bits);
            ctrl.filter_logs(bits);
        };
        
        //----------------------------------------------------------------------
        var init_ordering_by_columns = function(history) {
            var columns = '#history thead th[data-column]';
            Array.from(document.querySelectorAll(columns)).forEach(function(e) {
                DOM.evt(e, 'click', function(evt) {
                    var ordering = get_ordering(this);
                    if(ordering.order === 'asc') {
                        HashBits.from_filters().update();
                    }
                    history.sort_current(ordering.column, ordering.order);
                });
            });
        };
        
        //----------------------------------------------------------------------
        var create_country_options = function(countries) {
            var cos = $$('id_co');
            sorted_dict(countries).forEach(function(item) {
                cos.appendChild(DOM.create('option', item[1], {'value': item[0]}));
            });
        };
        
        //----------------------------------------------------------------------
        var create_years_option = function(years) {
            var keys = years.values();
            var sel = DOM.create('select', {
                'class': 'filter_ctrl form-control input-sm',
                'id': 'id_years'
            });

            DOM.css(sel, {'display': 'none'});
            keys.sort(function(a, b) { return b - a; });
            keys.forEach(function(yr) {
                sel.appendChild(DOM.create('option', yr, {'value': yr}));
            });
            $$('id_date').parentElement.appendChild(sel);
        };
        
        //----------------------------------------------------------------------
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
                if(this.value === '=') {
                    $$('id_years').style.display = 'inline-block';
                    date_el.style.display = 'none';
                }
                else {
                    date_el.style.display = 'inline-block';
                    $$('id_years').style.display = 'none';
                }
            });

            DOM.evt(date_el, 'input', on_filter_change);
            DOM.evt(date_el, 'propertychange', on_filter_change);
            Array.from(document.querySelectorAll('.filter_ctrl')).forEach(function(e) {
                DOM.evt(e, 'change', on_filter_change);
            });

            on_hash_change();
        };
        
        return ctrl;
    }());
    
    //==========================================================================
    var HashBits = function() {};
    
    //--------------------------------------------------------------------------
    HashBits.from_hash = function(hash) {
        var arr;
        var bits = new HashBits();
        hash = hash || window.location.hash;
        if(hash && hash[0] == '#') {
            hash = hash.substr(1);
        }
        
        if(hash) {
            arr = hash.split('/');
            for(var i = 0, j = arr.length; i < j; i += 2) {
                if(arr[i]) {
                    bits[arr[i]] = arr[i + 1];
                }
            }
            if(bits.date) {
                bits.timeframe = bits.date[0];
                if(bits.timeframe === '=') {
                    bits.date = parseInt(bits.date.substr(1));
                }
                else {
                    bits.date = moment(bits.date.substr(1));
                }
            }
        }
        return bits;
    };
    
    //--------------------------------------------------------------------------
    HashBits.from_filters = function() {
        var dt    = $$('id_date').value;
        var el    = document.querySelector('#history thead .current');
        var bits  = new HashBits();
        bits.type = $$('id_filter').value;
        bits.co   = $$('id_co').value;
        bits.timeframe = $$('id_timeframe').value;
        
        if(bits.timeframe === '=') {
            bits.date = parseInt($$('id_years').value);
        }
        else if(bits.timeframe) {
            bits.date = dt ? moment(dt) : null;
        }
        if(el && el.dataset.order == 'asc') {
            bits.asc = el.dataset.column;
        }
        return bits;
    };

    //--------------------------------------------------------------------------
    HashBits.prototype.toString = function() {
        var a = [];
        this.type && a.push('type', this.type);
        this.co   && a.push('co', this.co);
        this.asc  && a.push('asc', this.asc);
        if(this.timeframe === '-' || this.timeframe === '+') {
            if(this.date) {
                a.push('date', this.timeframe + this.date.format(DATE_FORMAT));
            }
        }
        else if(this.timeframe === '=') {
            if(this.date) {
                a.push('date', this.timeframe + this.date);
            }
        }
        return a.length ? '#' + a.join('/') : './';
        
    };
    
    //--------------------------------------------------------------------------
    HashBits.prototype.update = function() {
        window.history.pushState({}, '', this.toString());
    };
    
    //--------------------------------------------------------------------------
    var set_filter_fields = function(bits) {
        var years_el = $$('id_years');
        var date_el = $$('id_date');
        $$('id_filter').value = bits.type || '';
        $$('id_timeframe').value = bits.timeframe || '';
        $$('id_co').value = bits.co || '';

        years_el.style.display = 'none';
        date_el.style.display = 'none';
        if((bits.timeframe === '=') && bits.date) {
            years_el.value = bits.date;
            years_el.style.display = 'inline-block';
        }
        else {
            if(bits.timeframe && bits.date) {
                date_el.value = bits.date.format(DATE_FORMAT);
                date_el.style.display = 'inline-block';
            }
        }
    };
    
    root.profile_history = controller;
    root.timeit = function(fn) {
        var args = Array.from(arguments);
        var start = new Date();
        var result = fn.call(undefined, args);
        var end = new Date();
        console.log(start + ' | ' + end + ' = ' + (end - start));
        return result;
        
    };
    
    return {
        profile_history: function(entities, logs, conf) {
            controller.initialize(entities, logs, conf);
        }
    };
}());
