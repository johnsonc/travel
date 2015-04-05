/* @preserve Version 0.1, Copyright (c) 2015 David A Krauth */
;Almanac = (function() {
    var MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    var KEY_ESC = 27;
    var DEFAULT_OPTS = {
        days_of_week: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
        month_names: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        day_post_create: null,
        year_range: '-50',
        show_other_month_days: true,

        month_tag: 'div',
        month_class: 'month',
        week_tag: 'div',
        week_class: 'week',
        day_tag: 'div',
        day_class: 'day',
        day_num_tag: 'span',
        day_num_class: 'day-num',
        
        weekday_wrapper_tag: 'div',
        weekday_wrapper_class: 'weekdays',
        weekday_tag: 'span',
        
        selector_tag: 'div',
        selector_class: 'selector',
        selector_month_class: 'month-select',
        selector_year_class: 'year-select',
        
        show_cancel: false,
        footer_class: 'footer'
    };

    var DOM = {
        create: function(tag) {
            var j, key, arg;
            var el = document.createElement(tag);
            for(var i = 1; i < arguments.length; i++) {
                arg = arguments[i];
                if(Utils.is_array(arg)) {
                    for(j = 0; j < arg.length; j++) {
                        el.appendChild(arg[j]);
                    }
                }
                else if(Utils.is_object(arg)) {
                    for(key in arg) {
                        if(el.hasOwnProperty(key)) {
                            el[key] = arg[key];
                        }
                        else {
                            el.setAttribute(key, arg[key])
                        }
                    }
                }
                else if(arg){
                    el.textContent = arg.toString();
                }
            }
            return el;
        },
        option: function(text, value) {
            return this.create('option', text, {'value': value});
        },
        display_element: function(el, yesno) {
            if(typeof el === 'string') {
                el = document.getElementById(el);
            }
            el.style.display = yesno ? 'block' : 'none';
        }
    };

    var Utils = {
        is_leap: function(yr) {
            return yr % 4 == 0 && (yr % 100 != 0 || yr % 400 == 0);
        },
        last_day: function(year, month) {
            return MONTH_DAYS[month] + ((month == 1 && this.is_leap(year) ? 1 : 0));
        },
        merge: function() {
            var merged = {};
            var obj;
            for(var i = 0; i < arguments.length; i++) {
                obj = arguments[i];
                for(var key in obj) {
                    if(obj.hasOwnProperty(key)) {
                        merged[key] = obj[key];
                    }
                }
            }
            return merged;
        },
        is_object: function(obj) {
            return Object.prototype.toString.call(obj) === '[object Object]';
        },
        iso_string: function(dt) {
            var day = dt.getDate();
            var mon = dt.getMonth() + 1;
            return (
                  dt.getFullYear()
                + '-' + (mon < 10 ? '0' + mon : mon)
                + '-' + (day < 10 ? '0' + day : day)
            );
        },
        is_date: function(obj) {
            return Object.prototype.toString.call(obj) === '[object Date]';
        },
        is_string: function(obj) {
            return typeof obj === 'string';
        },
        is_array: function(obj) {
            return Object.prototype.toString.call(obj) === '[object Array]';
        }
    };

    var parse_year_range = function(val, rel) {
        var end, incr;
        var range = [];
        rel = rel || (new Date()).getFullYear();
        val = parseInt(val);
        incr = val < 0 ? -1: 1;
        end = rel + val;
        
        for(; rel != end; rel += incr) {
            range.push(rel);
        }
        return range;
    };

    var create_weekday_header_elements = function(opts) {
        var el = DOM.create(opts.weekday_wrapper_tag, {'class': opts.weekday_wrapper_class});
        opts.days_of_week.forEach(function(name) {
            el.appendChild(DOM.create(opts.weekday_tag, name));
        });
        return el;
    };

    var make_selector_change_handler = function(opts) {
        return function() {
            var month_sel = this.parentElement.querySelector('select[data-type="month"]');
            var year_sel = this.parentElement.querySelector('select[data-type="year"]');
            var container = this.parentElement.parentElement;
            var month_el = container.querySelector('.' + opts.month_class);
        
            var month = parseInt(month_sel.value);
            var year =  parseInt(year_sel.value);
            var dt = new Date(year, month);
            container.replaceChild(create_days_elements(dt, opts), month_el);
            container.setAttribute('data-date', Utils.iso_string(dt));
        };
    };
    
    // var on_other_month = function() { };
    
    var make_month_selector = function(mo, opts) {
        var el = DOM.create('select', {'class': opts.selector_month_class});
        el.dataset['type'] = 'month';
        el.addEventListener('change', make_selector_change_handler(opts), false);
        opts.month_names.forEach(function(name, i) {
            el.appendChild(DOM.option(name, i));
            if(i == mo) {
                el.selectedIndex = i;
            }
        });
        return el;
    };
    
    var make_year_selector = function(year, opts) {
        var i = 0;
        var el = DOM.create('select', {'class': opts.selector_year_class});
        var year_range = opts.year_range;
        el.dataset['type'] = 'year';
        el.addEventListener('change', make_selector_change_handler(opts), false);
        
        if(Utils.is_string(year_range)) {
            year_range = parse_year_range(year_range, year);
        }
        
        for(; i < year_range.length; i++) {
            el.appendChild(DOM.option(year_range[i], year_range[i]));
            if(year_range[i] == year) {
                el.selectedIndex = i;
            }
        }
        return el;
    };
    
    var create_date_selectors_elements = function(dt, opts) {
        var el = DOM.create(opts.selector_tag, {'class': opts.selector_class});
        el.appendChild(make_month_selector(dt.getMonth(), opts));
        el.appendChild(make_year_selector(dt.getFullYear(), opts));
        return el;
    };

    var AlmanacDay = function(year, month, day, is_current) {
        this.date        = new Date(year, month, day);
        this.day_of_week = this.date.getDay();
        this.year        = year;
        this.month       = month;
        this.day         = day;
        this.last_day    = Utils.last_day(year, month);
        this.is_current  = !!is_current;
    };
    
    AlmanacDay.prototype.replace = function(day) {
        return new AlmanacDay(this.year, this.month, day, this.is_current);
    };
    
    AlmanacDay.prototype.prev_month = function() {
        var month = this.month, year = this.year;
        if(month == 0) {
            month = 11;
            --year;
        }
        else {
            --month;
        }
        return new AlmanacDay(year, month, this.last_day);
    };
    
    AlmanacDay.prototype.next_month = function() {
        var month = this.month, year = this.year;
        if(month == 1) {
            month = 0;
            ++year;
        }
        else {
            ++month;
        }
        return new AlmanacDay(year, month, 1);
    };
    
    AlmanacDay.prototype.toISOString = function() {
        return Utils.iso_string(this.date);
    };
    
    AlmanacDay.range = function(value) {
        var dt     = value || new Date();
        var today  = new AlmanacDay(dt.getFullYear(), dt.getMonth(), dt.getDate(), true);
        var offset = (new Date(today.year, today.month)).getDay();
        var days   = [];
        var i, j, prev, next;
        
        if(offset) {
            prev = today.prev_month();
            for(i = (prev.day - offset) + 1, j = prev.day; i <= j; i++) {
                days.push(prev.replace(i));
            }
        }
        
        for(i = 1, j = Utils.last_day(today.year, today.month); i <= j; i++ ) {
            days.push(today.replace(i));
        }
        
        offset = days.length % 7;
        if(offset) {
            next = today.next_month();
            for(i = 1, j = (7 - offset); i <= j; i++) {
                days.push(next.replace(i))
            }
        }

        return days;
    };
    
    var create_day_element = function(cdt, opts) {
        var el = DOM.create(opts.day_tag, {'class': opts.day_class});
        var active = cdt.is_current || opts.show_other_month_days;
        if(!cdt.is_current) {
            el.className += ' other';
        }
        
        if(active) {
            el.dataset['date'] = cdt.toISOString();
            if(opts.day_onclick) {
                if(Utils.is_string(opts.day_onclick)) {
                    el.addEventListener('click', function() {
                        document.getElementById(opts.day_onclick).value = this.dataset['date'];
                    }, false);
                }
                else {
                    el.addEventListener('click', opts.day_onclick, false);
                }
            }
        }
        
        el.appendChild(DOM.create(opts.day_num_tag, 
            {'class': opts.day_num_class},
            active ? cdt.day : ''
        ));
        
        if(opts.day_post_create) {
            opts.day_post_create(el, cdt)
        }
        
        return el;
    };
    
    var create_days_elements = function(dt, opts) {
        var cdt, week_el;
        var month_el = DOM.create(opts.month_tag, {'class': opts.month_class});
        var cal = AlmanacDay.range(dt);
        for(var i = 0; i < cal.length; i++) {
            cdt = cal[i];
            if(i % 7 == 0) {
                week_el = DOM.create(opts.week_tag, {'class': opts.week_class})
                month_el.appendChild(week_el);
            }
            
            week_el.appendChild(create_day_element(cdt, opts));
        }
        return month_el;
    };
    
    var create_footer_element = function(opts) {
        var el = DOM.create('div', {'class': opts.footer_class});
        var a = DOM.create('a', 'Cancel', {'href': '#'});
        a.addEventListener('click', function(evt) {
            DOM.display_element(el.parentElement, false);
            evt.stopPropagation();
            evt.preventDefault();
        }, false);
        el.appendChild(a);
        return el;
    };
    
    var dismiss_on_escape = function(id) {
        document.addEventListener('keyup', function(evt) {
            if(evt.keyCode === KEY_ESC) {
                DOM.display_element(id, false);
            }
        }, false);
    };
    
    var dismiss_by_clicking_away = function(id) {
        document.addEventListener('click', function(evt) {
            var el = document.getElementById(id);
            var r = el.getBoundingClientRect(),
                x = evt.clientX,
                y = evt.clientY;

            var contains = (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom);
            console.log('contains', contains);
            if(!contains && el.style.block !== 'none') {
                DOM.display_element(el, false);
            }
        }, false);
        
    };
    
    var popout_decorator = function(element_id, output_id, default_handler) {
        return function() {
            var el;
            if(default_handler && false === default_handler()) {
                return;
            }
            DOM.display_element(element_id, false);
            el = document.getElementById(output_id);
            el.value = this.dataset['date'];
            el.focus();
        };
    };
    
    var initialize_almanac = function(el, opts) {
        var dt = opts.date || new Date();
        var doc_frag = document.createDocumentFragment();
        opts = Utils.merge(DEFAULT_OPTS, opts || {});

        el.setAttribute('data-date', Utils.iso_string(dt));
        
        doc_frag.appendChild(create_date_selectors_elements(dt, opts));
        doc_frag.appendChild(create_weekday_header_elements(opts));
        doc_frag.appendChild(create_days_elements(dt, opts));
        if(opts.show_cancel) {
            doc_frag.appendChild(create_footer_element(opts));
        }
        el.appendChild(doc_frag);
    };

    var popout_almanac = function(element_id, output_id, opts) {
        var almanac_el = document.getElementById(element_id);
        document.getElementById(output_id).addEventListener('click', function() {
            DOM.display_element(element_id, true);
            this.blur();
        }, false);
        
        dismiss_on_escape(element_id);
        dismiss_by_clicking_away(element_id);

        opts.day_onclick = popout_decorator(element_id, output_id, opts.day_onclick);
        initialize_almanac(almanac_el, opts);
    };
    
    return {
        initialize: initialize_almanac,
        popout: popout_almanac,
        Day: AlmanacDay,
        Utils: Utils,
        DOM: DOM
    };
}());
