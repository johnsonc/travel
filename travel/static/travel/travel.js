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
        var column = el.dataset['column'];
        var order = el.dataset['order'];
        var current = el.parentElement.querySelector('.current');
        if(el === current) {
            order = (order === 'desc') ? 'asc' : 'desc';
            el.dataset['order'] = order;
        }
        else {
            current.className = '';
            el.className = 'current'
        }
        return {'column': column, 'order': order};
    };
    
    //--------------------------------------------------------------------------
    var show_summary = function(summary, filtered) {
        var el = $$('summary');
        var which = filtered || summary;
        DOM.remove_children(el);
        el.appendChild(DOM.create('strong', 'Summary: '))
        which.iter(function(key) {
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
                history.show_logs(history.current_logs);
                
            });
        });
    };
    
    //==========================================================================
    var Summary = function() {
        Iter.each(Summary.keys, function(key) {
            this[key] = {};
        }, this);
    }

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
    var profile_history = {
        media_prefix: '/media/',
        initialize: function(entities, logs, conf) {
            var media_prefix = conf.media_prefix || this.media_prefix;
            var countries = {};
            this.summary = new Summary;
            this.filters = {'type': null, 'country__code': null};
            this.entities = {};
            Iter.each(entities, function(e) {
                e = initialize_log_entry(e, media_prefix);
                if(e.country__code) {
                    countries[e.country__code] = e.country__name;
                }
                this.entities[e.id] = e;
            }, this);
            
            this.current_logs = this.all_logs = Iter.map(logs, function(log) {
                log.entity = this.entities[log.entity__id];
                log.entity.logs.push(log);
                log.arrival = moment(log.arrival.value);
                this.summary.add(log.entity);
                return log;
            }, this);
            
            console.log(this.summary);
            create_country_options(countries);
            init_ordering_by_columns(this);
            show_summary(this.summary);
        },
        
        filter_logs: function(bits) {
            var type    = bits.type;
            var co      = bits.co;
            var dt      = bits.date;
            var tf      = bits.timeframe;
            var logs    = this.all_logs;
            var summary = this.summary;
            
            console.log('filter bits', bits);
            this.filters = {'type': type, 'co': co};
            if(type || co || tf) {
                summary = new Summary;
                logs = Iter.filter(logs, function(e) {
                    var good = true;
                    if(type) {
                        good &= (e.entity.type__abbr === type);
                    }

                    if(co) {
                        good &= (e.entity.country__code === co || (e.entity.type__abbr === 'co' && e.entity.code === co));
                    }
                    
                    if(good && tf && dt) {
                        switch(tf) {
                            case '+':
                                good &= e.arrival.isAfter(dt);
                                break
                            case '-':
                                good &= e.arrival.isBefore(dt);
                                break;
                            case '=':
                                good &= (e.arrival.year() === dt.getFullYear());
                                break;
                            default:
                                good = false;
                        }
                    }
                    if(good) {
                        summary.add(e.entity);
                        return true;
                    }
                    return false;
                });
            }
            
            this.show_logs(logs, summary);
        },
        
        show_logs: function(logs, summary) {
            var i, start;
            var count = logs.length;
            var parent = $$('history');
            var el = parent.querySelector('tbody');
            this.current_logs = logs;
            $$('id_count').textContent = (count + ' entr' + (count > 1 ? 'ies' : 'y'));

            start = new Date();
            DOM.remove(el);
            el = DOM.create('tbody');
            Iter.each(logs, function(log) {
                el.appendChild(create_log_row(log));
            });
            parent.appendChild(el);
            console.log('delta', new Date() - start);
            show_summary(summary);
        },

        sort_current: function(column, order) {
            console.log('ordering', column, order);
            this.current_logs.sort(function(a, b) {
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
        }
        
    };
    

    //--------------------------------------------------------------------------
    var make_hash = function(bits) {
        var a = [];
        bits.type && a.push('type', bits.type);
        bits.co   && a.push('co', bits.co);
        bits.asc  && a.push('asc', bits.asc);
        if(bits.date && bits.timeframe) {
            a.push('date', bits.timeframe + bits.date);
        }

        return a.length ? '#' + a.join('/') : './';
    };
    
    //--------------------------------------------------------------------------
    var obj_from_hash = function(hash) {
        var obj = {};
        var arr;
        hash = hash || window.location.hash;
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
    var on_filter_change = function() {
        var bits = get_filter_bits();
        console.log(bits);
        
        update_hash(bits);
        profile_history.filter_logs(bits);
    };
    
    //--------------------------------------------------------------------------
    var set_filter_fields = function(bits) {
        $$('id_filter').value = bits.type || '';
        $$('id_timeframe').value = bits.timeframe || '';
        $$('id_co').value = bits.co || '';
        if(bits.date) {
            $$('id_date').value = bits.date;
        }
        else {
            $$('id_date').style.display = 'none';
        }
    };
    
    //--------------------------------------------------------------------------
    var on_hash_change = function() {
        var bits = obj_from_hash(window.location.hash);
        set_filter_fields(bits);
        profile_history.filter_logs(bits);
    };

    //--------------------------------------------------------------------------
    var init_profile_filter = function(conf) {
        var date_el = $$('id_date');
        var picker = new Pikaday({
            field: date_el,
            format: 'YYYY-MM-DD',
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
    
    root.profile_history = profile_history;
    return {
        profile_history: function(entities, logs, conf) {
            profile_history.initialize(entities, logs, conf);
            init_profile_filter(conf);
        }
    };
}());
