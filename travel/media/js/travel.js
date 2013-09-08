;var Travelogue = (function($) {

    var stripe = function(selector) {
        $(selector + ':visible')
            .removeClass('even')
            .not(':odd')
            .addClass('even');
    };
    
    var change_hash = function(bits) {
        var hash = bits.length ? '#' + bits.join('+') : './';
        console.log('hash', hash);
        window.history.pushState({}, '', hash);
    };
    
    var on_filter_change = function() {
        var bits = [],
            filt = $('#id_filter').val(),
            co   = $('#id_country').val();
        
        if(filt) {
            bits.push(filt);
        }
        
        if(co) {
            bits.push(co);
        }
        
        change_hash(bits);
        do_filter_logs('#id_entries tr', bits);
    };
    
    var on_hash_change = function() {
        var $filters = $('.filter_ctrl');
        var hash = window.location.hash
                 ? window.location.hash.substring(1).split('+')
                 : [];
                 
        console.log('starting hash', hash);
        $filters.each(function() {
            $(this).val('');
        });
        _.each(hash, function(o) {
            var sel = 'option[value="' + o + '"]';
            $filters.find(sel).parent().val(o)
        });
        do_filter_logs('#id_entries tr', hash);
    };

    var do_filter_logs = function(selector, filters) {
        var filter_cls = _.reduce(
            filters || [],
            function(accum, val) { return val? accum + '.' + val : accum; },
            ''
        );
        var $what = $(selector + filter_cls);
        var count = $what.length;
        console.log('selector + filter_cls =', selector + filter_cls);

        $('#id_count').text(count + ' entr' + (count > 1 ? 'ies' : 'y'));
        if(filter_cls) {
            $(selector).hide();
        }
        $what.show();
        stripe('#id_entries tr');
    };
    
    return {
        log_entry_prep: function() {
            $("#id_arrival,#id_departure").datetimepicker({
                changeMonth: true,
                changeYear: true,
                numberOfMonths: 1,
                showOn: "button",
                minDate: "-100Y",
                yearRange: "-40:+1",
                buttonImage: "/media/img/calendar2.png",
                buttonImageOnly: true,
                dateFormat: 'yy-mm-dd',
                timeFormat: 'hh:mm t',
                hour: 12,
                hourGrid: 4,
                minuteGrid: 15
            })
        },
        
        init_profile_filter: function() {
            $(window).on('hashchange', on_hash_change);
            $('.filter_ctrl').on('change', on_filter_change);
            on_hash_change();
        }
    };
}(jQuery));
