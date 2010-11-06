app = Tea.Application({
    init : function() {
        this.stack = Tea.Stack({
            id: 'stack'
        });
    },
    ready : function() {
        this.stack.render().appendTo(document.body);
        
        var key = null;
        if (window.location.hash)
            key = window.location.hash.substr(1);
        
        this.master = Node({
            address: location.host.split(":"),
            key: key
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
    getType : function(name) {
        return this._service_types[name];
    },
    ajaxError : function() {
        console.log("ajaxError", arguments);
    },
    ajaxSend : function(e, xhr, options) {
        xml.setRequestHeader('Authorization', this.auth);
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

AuthenticationDialog = Tea.Dialog.extend({
    options: {
        placement: 'center',
        title: 'Auth Key',
        node: null,
        items: [
            {type: 't-text', name: 'key', cls: 'fill'},
            {type: 't-button', text: 'Go', icon: 'enable', cls: 'right'}
        ]
    },
    onRender : function() {
        var self = this;
        this.items[0].input.source.keydown(function(e) {
            if (e.keyCode == 13) {
                self.do();
            }
        })
        this.items[1].source.click(Tea.method(this.do, this));
    },
    do: function() {
        this.node.key = this.items[0].getValue();
        this.node.load();
        this.hide();
    },
    show : function() {
        this.__super__();
        this.items[0].focus();
        app.stack.hide();
    },
    hide : function() {
        this.__super__();
        app.stack.source.fadeIn();
    }
})