app = Tea.Application({
    init : function() {
        this.stack = Tea.Stack({
            id: 'stack'
        });
    },
    ready : function() {
        this.stack.render().appendTo(document.body);
        
        this.master = Node({
            address: location.host.split(":")
        });
        this.master.cycle(1000);
        
        this.stack.push(NodeMenu({
            value: this.master
        }));
        
        this._service_types = {};
        for(var i = 0; i < this.service_types.length; i++) {
            var t = this.service_types[i];
            this._service_types[t.type] = t;
        }
    },
    post : function(options) {
        var opts = jQuery.extend({
                        type: "post",
    			        contentType: 'application/json',
    			        processData: false,
    			        data: null
                    }, options);
        opts.data = Tea.toJSON(opts.data);
        jQuery.ajax(opts);
    },
    getType : function(name) {
        return this._service_types[name];
    }
});

MenuButton = Tea.Button.extend('MenuButton', {
    options: {
        panel: null,
        value: null
    },
    __init__ : function(options) {
        this.__super__(options);
        this.click = function() {
            var panel = Tea.manifest({
                type: this.panel,
                value: this.value
            });
            Tea.pushStack(panel, this);
            this.hook(panel, 'remove', this.unHighlight);
            this.highlight();
        }
    },
    highlight : function() {
        this.source.addClass('active');
    },
    unHighlight : function() {
        this.source.removeClass('active');
    }
});

