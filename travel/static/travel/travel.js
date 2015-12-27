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
    var initialize_log_entry = function(e, media_prefix) {
        e.entity_url = entity_url(e);
        e.recent_visit = moment(e.recent_visit.value);
        e.first_visit = moment(e.first_visit.value);
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
    var update_type_selector = function(summary, filtered) {
        Iter.each(document.querySelectorAll('#id_filter option'), function(e) {
            var format = e.dataset.format;
            var total = summary[e.value] || '';
            var sub = '';
            var text = total;
            if(total) {
                if(filtered) {
                    text = (filtered[e.value] || 0) +  ' of ' + total;
                }
                text = '(' + text + ')';
            }
            e.text = format.replace('$', text);
        });
    };
    
    //--------------------------------------------------------------------------
    var profile_history = {
        media_prefix: '/media/',
        initialize: function(history, conf) {
            var media_prefix = conf.media_prefix || this.media_prefix;
            var co_opts = $$('id_co');
            var countries = {};
            this.summary = {'': history.length};
            this.filters = {'type': null, 'country__code': null};
            this.current_entities = this.all_entities = Iter.each(history, function(e) {
                e = initialize_log_entry(e, media_prefix);
                if(e.country__code) {
                    countries[e.country__code] = e.country__name;
                }
                increment(this.summary, e.type__abbr);
                return e;
            }, this);
            console.log(this.summary);
            
            Iter.each(sorted_dict(countries), function(item) {
                var opt = document.createElement('option');
                opt.value = item[0];
                opt.textContent = item[1];
                co_opts.appendChild(opt);
            });
            
            Iter.each(document.querySelectorAll('#history thead th[data-column]'), function(e) {
                var ph = this;
                DOM.evt(e, 'click', function(evt) {
                    var ordering = get_ordering(this);
                    if(ordering.order === 'asc') {
                        update_hash(get_filter_bits());
                    }
                    ph.sort_current(ordering.column, ordering.order);
                    ph.show_entities(this.current_entities);
                    
                });
            }, this);

            update_type_selector(this.summary);
        },
        
        filter: function(bits) {
            var type     = bits.type;
            var co       = bits.co;
            var dt       = bits.date ? new Date(bits.date) : null;
            var tf       = bits.timeframe;
            var entities = this.all_entities;
            var summary  = null;
            
            console.log('filter bits', bits);
            this.filters = {'type': type, 'co': co};
            if(type || co || dt) {
                summary = {};
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
                    if(good) {
                        increment(summary, e.type__abbr);
                        return true;
                    }
                    return false;
                });
                summary[''] = entities.length
            }
            
            this.show_entities(entities, summary);
        },
        
        show_entities: function(entities, summary) {
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
            update_type_selector(this.summary, summary);
        },

        sort_current: function(column, order) {
            console.log('ordering', column, order);
            this.current_entities.sort(function(a, b) {
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
    };

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
        var bits = {
            type:      $$('id_filter').value,
            co:        $$('id_co').value,
            timeframe: $$('id_timeframe').value,
            date:      get_datepicker_iso()
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
    
    
    return {
        profile_history: profile_history,
        initialize: function(history, conf) {
            profile_history.initialize(history, conf);
            init_profile_filter();
        }
    };
}());
