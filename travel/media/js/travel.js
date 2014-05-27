;var Travelogue = (function($) {
    var root = this;
    var STARS = '★★★★★';
    
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
        'recent': function(a, b) { return b.most_recent_visit - a.most_recent_visit; },
        'first':  function(a, b) { return b.first_visit - a.first_visit; },
        'logs':   function(a, b) { return b.num_visits - a.num_visits; },
        'rating': function(a, b) { return a.rating - b.rating; }
    };
    
    var profile_history = root.profile_history = {
        selector: '#history tbody',
        media_prefix: '/media/',
        initialize: function(history, conf) {
            var media_prefix = conf.media_prefix || this.media_prefix;
            var $co_opts = $('#id_country');
            this.filters = {'type': null, 'country_code': null};
            this.countries = {};
            this.all_entities = _.map(history, function(e) {
                // "rating": 3,             "entity_id": 1463,
                // "code": "BUD",           "type_title": "Airport",
                // "num_visits": 1,         "flag_url": "img/ap-32.png",
                // "type_abbr": "ap",       "id": 276
                // "country_code": "HU",    "country_name": "Hungary",
                // "most_recent_visit": "2013-12-29 08:00:00",
                // "first_visit": "2013-12-29 08:00:00",
                // "name": "Budapest Ferenc Liszt International Airport",
                e.entity_url = entity_url(e);
                e.flag_url = e.flag_url ? media_prefix + e.flag_url: '';
                e.most_recent_visit = new Date(e.most_recent_visit);
                e.first_visit = new Date(e.first_visit);
                e.html = make_entity_row(e);
                if(e.country_code) {
                    this.countries[e.country_code] = e.country_name;
                }
                return e;
            }, this);
            
            _.each(this.countries, function(value, key) {
                $co_opts.append('<option value="co-' + key + '">' + value + '</option>');
            });
            
            this.$el = $('#history');
            this.$el.find('thead th').click(sort_handler);
        },

        filter: function(type, country_code) {
            var entities = this.all_entities;
            this.filters = {'type': type, 'country_code': country_code};
            if(type || country_code) {
                entities = _.filter(entities, function(e) {
                    var good = true;
                    if(type) {
                        good &= (e.type_abbr === type);
                    }

                    if(country_code) {
                        good &= (e.country_code === country_code);
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
    var change_hash = function(bits) {
        var hash = bits.length ? '#' + bits.join('+') : './';
        // console.log('hash', hash);
        window.history.pushState({}, '', hash);
    };
    
    //--------------------------------------------------------------------------
    var on_filter_change = function() {
        var bits = [];
        var type = document.getElementById('id_filter').value;
        var country = document.getElementById('id_country').value;
        
        if(type) {
            bits.push(type);
            type = type.substr(5);
        }
        
        if(country) {
            bits.push(country);
            country = country.substr('3')
        }
        
        change_hash(bits);
        profile_history.filter(type, country);
    };
    
    //--------------------------------------------------------------------------
    var on_hash_change = function() {
        var $filters = $('.filter_ctrl');
        var params = {'type': null, 'co': null};
        var bits;
        var hash = window.location.hash
                 ? window.location.hash.substring(1).split('+')
                 : [];
                 
        for(var i = 0, j = hash.length; i < j; i++) {
            bits = hash[i].split('-');
            params[bits[0]] = bits[1];
        }

        // console.log('starting hash', hash);
        $filters.each(function() {
            this.value = '';
        });
        
        _.each(hash, function(o) {
            var sel = 'option[value="' + o + '"]';
            $filters.find(sel).parent().val(o)
        });
        profile_history.filter(params.type, params.co);
    };

    //--------------------------------------------------------------------------
    var init_profile_filter = function() {
        $(window).on('hashchange', on_hash_change);
        $('.filter_ctrl').on('change', on_filter_change);
        on_hash_change();
    };
    
    //--------------------------------------------------------------------------
    var entity_url = function(e) {
        return '/i/' + e.type_abbr + '/' + (
            e.type_abbr == 'wh'
          ? (e.country_code + '-' + e.code)
          : e.code
        ) + '/';
    };

    //--------------------------------------------------------------------------
    var date_html = function(dt) {
        var ampm, html;
        var str = dt.toString().split(' ');
        var hours = dt.getHours();
        var minutes = dt.getMinutes();
        hours = hours ? hours % 12 : 12;
        ampm = (hours > 12) ? 'p' : 'a';
        if(minutes < 10) {
            minutes = '0' + minutes;
        }
        
        return (
            '<nobr>'            +
            str[1] + ' '        +
            dt.getDate() + ', ' +
            dt.getFullYear()    +
            '</nobr><br><nobr>' +
            str[0] + ' '        +
            hours  + ':'        +
            minutes             +
            ampm + '.m.</nobr>'
        );
    };
    
    //--------------------------------------------------------------------------
    var make_tag = function(name, html) {
        return '<' + name + '>' + html + '</' + name + '>';
    };
    
    //--------------------------------------------------------------------------
    var make_entity_row = function(e) {
        var html = '<tr class="type-' + e.type_abbr;
        if(e.country_code) {
            html += ' co-' + e.country_code;
        }
        
        html += '" data-id="' + e.id + '">';
        html += make_tag('td', e.flag_url
          ? '<img class="flag" src="' + e.flag_url + '" />'
          : ''
        );
        
        html += make_tag('td', e.type_title);
        html += make_tag('td', '<a href="' + e.entity_url + '">' + e.name + '</a>');
        html += make_tag('td', date_html(e.most_recent_visit));
        html += make_tag('td', date_html(e.first_visit));
        html += make_tag('td', e.num_visits);
        html += make_tag('td', STARS.substr(e.rating - 1));
        return html + '</tr>\n';
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
        initialize: function(history, conf) {
            profile_history.initialize(history, conf);
            init_profile_filter();
            
        }
    };
}(jQuery));
