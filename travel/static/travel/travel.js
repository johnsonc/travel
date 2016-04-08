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

;var Travelogue = (function(root) {
    function noop() {};    
    function defClass(prototype) {
        var constructor = prototype.hasOwnProperty('constructor') ? prototype.constructor : noop;
        constructor.prototype = prototype;
        return constructor;
    }

    var TYPE_MAPPING = {
        'cn': 'Continents',
        'co': 'Countries',
        'st': 'States',
        'ap': 'Airports',
        'ct': 'Cities',
        'np': 'National Parks',
        'lm': 'Landmarks',
        'wh': 'World Heritage sites'
    };
    
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
    var iterKeys = function(obj, callback, ctx) {
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
    var Set = defClass({
        constructor: function(iter) {
            this.items = {};
            this.size = 0;
            if(iter) {
                iter.forEach(function(i) { this.add(i); }, this);
            }
        },
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
    });
    
    //--------------------------------------------------------------------------
    var DOM = {
        $: document.getElementById.bind(document),
        create: function(tag) {
            var j, key, arg;
            var el = document.createElement(tag);
            for(var i = 1; i < arguments.length; i++) {
                arg = arguments[i];
                if(_.isPlainObject(arg)) {
                    DOM.setAttrs(el, arg);
                }
                else if(Array.isArray(arg)) {
                    DOM.appendChildren(el, arg);
                }
                else {
                    el.textContent = arg.toString();
                }
            }
            return el;
        },
        appendChildren: function(el, children) {
            Array.from(children).forEach(function(child) { el.appendChild(child); });
        },
        setAttrs: function(el, attrs) {
            iterKeys(attrs, function(k,v) { el.setAttribute(k, v); });
        },
        css: function(el, vals) {
            var style = el.style;
            iterKeys(vals, function(k, v) { style[k] = v; });
        },
        evt: function(el, kind, handler, t) {
            el.addEventListener(kind, handler, t);
        },
        remove: function(el) {
            el.parentNode.removeChild(el);
        },
        removeChildren: function(el) {
            while(el.lastChild) {
              el.removeChild(el.lastChild);
            }
        }
    };
    
    //--------------------------------------------------------------------------
    var dateTags = function(dtw) {
        return [
            DOM.create('div', dtw.format(DATE_STRING)),
            DOM.create('div', dtw.format(TIME_STRING))
        ];
    };
    
    //--------------------------------------------------------------------------
    var createLogRow = function(log) {
        var e = log.entity;
        var nameTd = DOM.create('td');
        var flagTd = DOM.create('td');
        var extras = [];
        var attrs = {
            'data-id' : e.id,
            'class': e.type__abbr + ' co-' + (
                e.country__code ?
                e.country__code :
                (e.type__abbr == 'co' ? e.code : '')
            )
        };

        nameTd.appendChild(DOM.create('a', e.name, {'href': e.entityUrl}));
        if(e.flag__thumb) {
            flagTd.appendChild(DOM.create('img', {'src': e.flag__thumb, 'class': 'flag'}));
        }
        
        e.locality && extras.push(e.locality);
        e.country__name && extras.push(e.country__name);
        if(extras.length) {
            nameTd.appendChild(DOM.create('span', extras.join(', ')));
        }
        
        if(e.country__flag__thumb) {
            nameTd.appendChild(DOM.create('img', {
                'src': e.country__flag__thumb,
                'class': 'flag flag-sm'
            }));
        }

        return DOM.create('tr', attrs, [
            flagTd,
            DOM.create('td', TYPE_MAPPING[e.type__abbr]),
            nameTd,
            DOM.create('td', {'class': 'when'}, dateTags(log.arrival)),
            DOM.create('td', {'class': 'when'}, dateTags(e.logs[e.logs.length-1].arrival)),
            DOM.create('td', e.logs.length),
            DOM.create('td', stars(log.rating))
        ]);
    };
    
    //--------------------------------------------------------------------------
    var sortedDict = function(dct) {
        var keys = iterKeys(dct);
        keys.sort();
        return keys.map(function(key) {
            return [key, dct[key]];
        });
    };
    
    //--------------------------------------------------------------------------
    var entityUrl = function(e) {
        var bit = e.code;
        if(e.type__abbr == 'wh' || e.type__abbr == 'st') {
            bit = e.country__code + '-' + bit;
        } 
        return '/i/' + e.type__abbr + '/' + bit + '/';
    };

    //--------------------------------------------------------------------------
    var initializeLogEntry = function(e, mediaPrefix) {
        e.logs = [];
        e.entityUrl = entityUrl(e);
        e.flag__thumb = mediaPrefix + e.flag__thumb;
        if(e.country__flag__thumb) {
            e.country__flag__thumb = mediaPrefix + e.country__flag__thumb;
        }
        return e;
    };
    
    //--------------------------------------------------------------------------
    var getOrdering = function(el) {
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
    var showSummary = function(summary) {
        var el = DOM.$('summary');
        DOM.removeChildren(el);
        el.appendChild(DOM.create('strong', 'Summary: '));
        summary.iter(function(key) {
            var items = iterKeys(this[key]).length;
            if(items) {
                el.appendChild(DOM.create(
                    'span',
                    {'class': 'label label-info'},
                    TYPE_MAPPING[key] + ': ' + items
                ));
            }
        });
    };
    
    //==========================================================================
    var Summary = defClass({
        constructor: function Summary() {
            Summary.keys.forEach(function(key) {
                this[key] = {};
            }, this);
        },
        add: function(e) {
            var kind = this[e.type__abbr];
            kind[e.id] = kind[e.id] ? kind[e.id] + 1 : 1;
        },
        iter:  function(callback) {
            Summary.keys.forEach(callback, this);
        }
    });
    
    Summary.keys = iterKeys(TYPE_MAPPING);
    
    //==========================================================================
    var TravelLogs = defClass({
        constructor: function(logs, summary) {
            this.logs = logs;
            this.summary = summary;
        },
        sort: function(column, order) {
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
        },
        filter: function(bits) {
            var logs    = this.logs;
            var summary = this.summary;
            
            console.log('filter bits', bits);
            if(bits.type || bits.co || bits.timeframe || bits.limit) {
                summary = new Summary();
                logs = logs.filter(function(log) {
                    var e = log.entity;
                    var good = true;
                    if(bits.type) {
                        good = (e.type__abbr === bits.type);
                    }

                    if(good && bits.co) {
                        good = (
                            e.country__code === bits.co ||
                            (e.type__abbr === 'co' && e.code === bits.co)
                        );
                    }
                    
                    if(good && bits.limit) {
                        if(e.logs.length === 1) {
                            good = true;
                        }
                        else if(bits.limit === 'recent') {
                            good = e.logs[0].id === log.id;
                        }
                        else {
                            good = e.logs[e.logs.length - 1].id == log.id;
                        }
                    }

                    if(good && bits.timeframe && bits.date) {
                        switch(bits.timeframe) {
                            case '+':
                                good = log.arrival.isAfter(bits.date);
                                break;
                            case '-':
                                good = log.arrival.isBefore(bits.date);
                                break;
                            case '=':
                                good = (log.arrival.year() === bits.date);
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
        }
    });
    //--------------------------------------------------------------------------
    var showLogs = function(travelLogs) {
        var count = travelLogs.logs.length;
        var parent = DOM.$('history');
        var el = parent.querySelector('tbody');
        var start = new Date();
        
        DOM.$('id_count').textContent = (count + ' entr' + (count > 1 ? 'ies' : 'y'));
        DOM.remove(el);
        el = DOM.create('tbody');
        travelLogs.logs.forEach(function(log) {
            el.appendChild(createLogRow(log));
        });
        parent.appendChild(el);
        showSummary(travelLogs.summary);
        console.log('delta', new Date() - start);
    };
    
    //--------------------------------------------------------------------------
    var controller = (function() {
        var entityDict = {};
        var currentLogs, allLogs;
        var ctrl = {
            initialize: function(entities, logs, conf) {
                var mediaPrefix = conf.mediaPrefix || MEDIA_PREFIX;
                var countries = {};
                var years = new Set();
                var summary = new Summary();
                entities.forEach(function(e) {
                    e = initializeLogEntry(e, mediaPrefix);
                    if(e.country__code) {
                        countries[e.country__code] = e.country__name;
                    }
                    entityDict[e.id] = e;
                });
            
                logs = logs.map(function(log) {
                    log.entity = entityDict[log.entity__id];
                    if(!log.entity) {
                        console.log(log);
                    }
                    log.entity.logs.push(log);
                    log.arrival = moment(log.arrival.value);
                    years.add(log.arrival.year());
                    summary.add(log.entity);
                    return log;
                }, this);
            
                currentLogs = allLogs = new TravelLogs(logs, summary);
                console.log(summary);
                createCountryOptions(countries);
                initOrderingByColumns(this);
                createYearsOption(years);
                initProfileFilter(conf);
            },
        
            filterLogs: function(bits) {
                currentLogs = allLogs.filter(bits);
                showLogs(currentLogs);
            },
        
            sortCurrent: function(column, order) {
                console.log('ordering', column, order);
                currentLogs.sort();
                showLogs(currentLogs);
            }
        };
        
        //----------------------------------------------------------------------
        var onFilterChange = function() {
            var bits = HashBits.fromFilters();
            console.log(bits);

            bits.update();
            ctrl.filterLogs(bits);
        };

        //----------------------------------------------------------------------
        var onHashChange = function() {
            var bits = HashBits.fromHash();
            setFilterFields(bits);
            ctrl.filterLogs(bits);
        };
        
        //----------------------------------------------------------------------
        var initOrderingByColumns = function(history) {
            var columns = '#history thead th[data-column]';
            Array.from(document.querySelectorAll(columns)).forEach(function(e) {
                DOM.evt(e, 'click', function(evt) {
                    var ordering = getOrdering(this);
                    if(ordering.order === 'asc') {
                        HashBits.fromFilters().update();
                    }
                    history.sortCurrent(ordering.column, ordering.order);
                });
            });
        };
        
        //----------------------------------------------------------------------
        var createCountryOptions = function(countries) {
            var cos = DOM.$('id_co');
            sortedDict(countries).forEach(function(item) {
                cos.appendChild(DOM.create('option', item[1], {'value': item[0]}));
            });
        };
        
        //----------------------------------------------------------------------
        var createYearsOption = function(years) {
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
            DOM.$('id_date').parentElement.appendChild(sel);
        };
        
        //----------------------------------------------------------------------
        var initProfileFilter = function(conf) {
            var dateEl = DOM.$('id_date');
            var picker = new Pikaday({
                field: dateEl,
                format: DATE_FORMAT,
                minDate: new Date(1920,1,1),
                yearRange: [1920, (new Date()).getFullYear()],
                onSelect: function(dt) { console.log(dt, this); }
            });

            DOM.evt(window, 'hashchange', onHashChange);
            DOM.evt(DOM.$('id_timeframe'), 'change', function() {
                if(this.value === '=') {
                    DOM.$('id_years').style.display = 'inline-block';
                    dateEl.style.display = 'none';
                }
                else {
                    dateEl.style.display = 'inline-block';
                    DOM.$('id_years').style.display = 'none';
                }
            });

            DOM.evt(dateEl, 'input', onFilterChange);
            DOM.evt(dateEl, 'propertychange', onFilterChange);
            Array.from(document.querySelectorAll('.filter_ctrl')).forEach(function(e) {
                DOM.evt(e, 'change', onFilterChange);
            });

            onHashChange();
        };
        
        return ctrl;
    }());
    
    //==========================================================================
    var HashBits = function() {};
    
    //--------------------------------------------------------------------------
    HashBits.fromHash = function(hash) {
        var arr;
        var kvp;
        var i = 0;
        var bits = new HashBits();
        hash = hash || window.location.hash;
        if(hash && hash[0] == '#') {
            hash = hash.substr(1);
        }
        
        if(hash) {
            arr = hash.split('/');
            for(i = 0; i < arr.length; i++) {
                kvp = arr[i].split(':');
                if(kvp.length === 2) {
                    bits[kvp[0]] = kvp[1];
                }
                else {
                    bits[kvp[0]] = true;
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
    HashBits.fromFilters = function() {
        var dt    = DOM.$('id_date').value;
        var el    = document.querySelector('#history thead .current');
        var bits  = new HashBits();
        bits.type = DOM.$('id_filter').value;
        bits.co   = DOM.$('id_co').value;
        bits.timeframe = DOM.$('id_timeframe').value;
        bits.limit = DOM.$('id_limit').value;

        if(bits.timeframe === '=') {
            bits.date = parseInt(DOM.$('id_years').value);
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
        this.type  && a.push('type:' + this.type);
        this.co    && a.push('co:' + this.co);
        this.asc   && a.push('asc:' + this.asc);
        this.limit && a.push('limit:' + this.limit);

        if(this.timeframe === '-' || this.timeframe === '+') {
            if(this.date) {
                a.push('date:' + this.timeframe + this.date.format(DATE_FORMAT));
            }
        }
        else if(this.timeframe === '=') {
            if(this.date) {
                a.push('date:' + this.timeframe + this.date);
            }
        }
        return a.length ? '#' + a.join('/') : './';
        
    };
    
    //--------------------------------------------------------------------------
    HashBits.prototype.update = function() {
        window.history.pushState({}, '', this.toString());
    };
    
    //--------------------------------------------------------------------------
    var setFilterFields = function(bits) {
        var yearsEl = DOM.$('id_years');
        var dateEl = DOM.$('id_date');
        DOM.$('id_filter').value = bits.type || '';
        DOM.$('id_timeframe').value = bits.timeframe || '';
        DOM.$('id_co').value = bits.co || '';
        DOM.$('id_limit').value = bits.limit || '';

        yearsEl.style.display = 'none';
        dateEl.style.display = 'none';
        if((bits.timeframe === '=') && bits.date) {
            yearsEl.value = bits.date;
            yearsEl.style.display = 'inline-block';
        }
        else {
            if(bits.timeframe && bits.date) {
                dateEl.value = bits.date.format(DATE_FORMAT);
                dateEl.style.display = 'inline-block';
            }
        }
    };
    
    return {
        parseHash: function(hsh) {
            return HashBits.fromHash(hsh);
        },
        timeit: function(fn) {
            var args = Array.from(arguments);
            var start = new Date();
            var result = fn.call(undefined, args);
            var end = new Date();
            console.log(start + ' | ' + end + ' = ' + (end - start));
            return result;
        },
        DOM: DOM,
        controller: controller,
        profileHistory: function(entities, logs, conf) {
            controller.initialize(entities, logs, conf);
        }
    };
}(window));
