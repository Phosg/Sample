Templates.header_alert_bar = [
    '<div class="icon"><!-- icon --></div>',
    '<div class="message"></div>',
    '<div class="close">&times;</div>'
].join("\n");

/*
    Example triggers in Backbone for this utility:

    Backbone.trigger('alert:default', {
        'message': 'Cookie use consent copy here.',
        'type': 'warning',
        'cookie': 'cookie_consent'
    });

    Backbone.trigger('alert:default', {
        'message': 'Notification copy here. <button class="action">Do Something</button>',
        'type': 'info',
        'callback' : function() { ... },
        'data': { 'variables': 'passed', ... }
    });

*/
App.View.HeaderAlert = Backbone.View.extend({
    initialize: function () {
        // create new method for each vastly differing type of alert we will need
        this.listenTo(Backbone, 'alert:default', this._defaultAlert);
    },

    render: function(){
    },

    setCookie: function(cookieName){
        var d = new Date(); d.setTime(d.getTime() + (30*24*60*60*1000));
        document.cookie = "_alert"+cookieName+"=seen; "+d.toUTCString()+"; path=/" 
    },

    _defaultAlert: function(options){
        // check cookies for persistance and ignore any already closed
        var show = true;
        var needs_cookie = false;
        if(options.cookie) {
            needs_cookie = true;
            // is this cookie already set, then the user does not need to see this again
            var check = (document.cookie.indexOf('_alert'+options.cookie+'=') != -1);
            if(check) {
                show = false;
            }
        } else if(options.unique) {
            // verify if this is currently in view, suppress duplicates
            if($("#"+options.unique).length > 0) {
                show = false;
            }
        }

        if(show) {
            var uid = "",
                self = this;

            if(options.unique) {
                uid = options.unique;
            } else {
                uid = "alert-"+Math.random().toString(36).substr(2, 10);
            }

            var alertTemplate = _.template('<div id="'+uid+'" class="header-alert-bar">'+Templates.header_alert_bar+'</div>');

            this.$el.append(alertTemplate);

            // set up alternate icon if type specified
            if(options.type) {
                this.$el.find('#'+uid).addClass(options.type);
            }

            // attach message to body
            this.$el.find('#'+uid+' .message').html(options.message);

            // attach ways to get rid of this alert
            this.$el.find('#'+uid+' .close').click(function(e){
                if(needs_cookie) {
                    self.setCookie(options.cookie);
                }

                $('#'+uid).slideUp('500',function(){
                    $('#'+uid).remove();
                });
            });

            // attach action if there is a callback method given
            if(options.callback && typeof(options.callback) == 'function') {
                this.$el.find('#'+uid+' .action').click(function(e){
                    if(needs_cookie) {
                        self.setCookie(options.cookie);
                    }
                    $('#'+uid).remove();
                    var data = options.data || {};
                    data['alertId'] = '#'+uid;
                    options.callback(data);
                }); 
            }

            // show it
            if(options.element) {
                $(options.element).append(this.$el);
            } else {
                $('body').append(this.$el);
            }
        }
    }
});
