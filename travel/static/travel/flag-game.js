;var FlagGame = (function(root, $) {
    
    //--------------------------------------------------------------------------
    var random_int = function(max) {
      return Math.floor(Math.random() * max);
    };
    
    //--------------------------------------------------------------------------
    var make_template = function(template_id, func) {
        var content = document.getElementById(template_id).textContent.trim();
        return _.template(content);
    };
    
    //--------------------------------------------------------------------------
    var flag_view = make_template('flag_view_template');
    
    //==========================================================================
    function Groups(group_ids) {
        this.group_ids = group_ids;
        this.reset();
    };

    //--------------------------------------------------------------------------
    Groups.prototype.reset = function() {
        this.random_order  = _.shuffle(_.range(this.group_ids.length));
        this.current_index = 0;
    };
    
    //-------------------------------------------------------------------------
    Groups.prototype.random_group = function() {
        var random_group_index = this.random_order[this.current_index++];
        return _.shuffle(this.group_ids[random_group_index]);
    };
    
    //--------------------------------------------------------------------------
    Groups.prototype.next = function() {
        (this.current_index >= this.group_ids.length) && this.reset();
        return this.random_group();
    };
    
    //==========================================================================
    function Score() {
        this.score = [0, 0];
    };
    
    //--------------------------------------------------------------------------
    Score.prototype.set_result = function(is_correct) {
        ++this.score[1];
        is_correct && ++this.score[0];
        return this.score.join(' / ');
    };
    
    //==========================================================================
    function Views(co_map) {
        this.co_map = co_map;
    };
    
    //--------------------------------------------------------------------------
    Views.prototype.score_view = function(text) {
        document.getElementById('game_score').textContent = text;
    };
    
    //--------------------------------------------------------------------------
    Views.prototype.group_view = function(group) {
        var co_id = group[random_int(group.length)];
        var correct = this.co_map[co_id];
        var flags_html = _.reduce(group, function(str, i) {
            return str + flag_view({'co': this.co_map[i], 'correct': correct.id});
        }, '', this);
        
        $('#co-name').html(correct.name);
        $('#item').html(flags_html).parent().removeClass('correct incorrect');
    };
    
    //--------------------------------------------------------------------------
    Views.prototype.indicate_correct = function(is_correct) {
        console.log('is_correct', is_correct);
        $('#item').parent()
            .removeClass('incorrect correct')
            .addClass(is_correct ? 'correct' : 'incorrect');
    };
    
    //--------------------------------------------------------------------------
    return {
        play: function(cos, group_ids) {
            var views = new Views(cos);
            var groups = new Groups(group_ids);
            var score = new Score();
            
            $('#item').on('click', 'img', function() {
                var is_correct = (this.dataset.correct == this.dataset.id);
                views.indicate_correct(is_correct);
                views.score_view(score.set_result(is_correct));
                setTimeout(function() { views.group_view(groups.next()); }, 1000);
            });

            $('#next_button').on('click', function() {
                views.score_view(score.set_result(false));
                views.group_view(groups.next());
            });
            views.group_view(groups.next());
        }
    };
}(this, jQuery));
