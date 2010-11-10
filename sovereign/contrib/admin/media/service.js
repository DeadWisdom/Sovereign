ServiceBase = Tea.Class({
    load : function() {
        this.node.ajax({
            url: '/services/' + this.id,
            success: Service
        });
    },
    destroy : function() {
        this.trigger('destroy');
        delete Service.cache[this.id];
        delete this;
    },
    cancelLogCycle : function() {
        if (this._logCycle)
            this._logCycle.cancel()
    },
    logCycle : function(interval) {
        if (this._logCycle)
            this._logCycle.refresh(interval);
        else {
            this.hook(this, 'log', function() { this._logCycle() });
            this._logCycle = Tea.latent(interval, this.updateLog, this);
            this._logCycle.call();
        }
    },
    updateLog : function() {
        if (this._since) {
            this.node.ajax({
                url: '/services/' + this.id + '/log?since=' + this._since,
                success : Tea.method(this.onUpdateLog, this)
            });
        } else {
            this.node.ajax({
                url: '/services/' + this.id + '/log',
                success : Tea.method(this.onUpdateLog, this)
            });
        }
    },
    onUpdateLog : function(log) {
        if (this.log)
            this.log = this.log.concat(log);
        else
            this.log = log;
        
        if (log.length > 0)
            this._since = Math.floor( log[log.length-1].created );
        
        this.trigger('log', [log]);
    },
    msg : function(options) {
        this.node.post({
            url: '/services/' + this.id + '/~' + options.msg,
            data: options.args || {},
            success: Tea.method(options.success || jQuery.noop, options.context || this)
        });
    },
    redeploy : function(callback, context) {
        this.msg({
            msg: 'redeploy',
            callback: callback,
            context: context
        });
    },
    del : function(callback, context) {
        this.msg({
            msg: 'delete',
            callback: callback,
            context: context
        });
    },
    disable : function(callback, context) {
        this.msg({
            msg: 'disable',
            callback: callback,
            context: context
        });
    },
    enable : function(callback, context) {
        this.msg({
            msg: 'enable',
            callback: callback,
            context: context
        });
    }
});

Service = function(object) {
    if (object instanceof Tea.Object) return object;
    
    var id = object.id;
    var existing = Service.cache[id];
    if (existing) {
        jQuery.extend(existing, object);
        existing.trigger('update');
        return existing;
    }
    return Service.cache[id] = ServiceBase(object);
}

Service.cache = {}

ServiceButton = MenuButton.extend({
    options: {
        value: null,
        cls: 'service',
        panel: 'ServicePanel',
        icon: 'service'
    },
    init : function() {
        this.hook(this.value, 'update',  this.refresh);
        this.hook(this.value, 'destroy', this.remove);
    },
    onRender : function() {
        this.status = $('<div class="status">').appendTo(this.source);
        this.refresh();
    },
    refresh : function() {
        var service = this.value;
        this.setText(service.id);
        this.status.empty().append(service.status);
        if (this.value.disabled) {
            this.status.css({
                color: 'gray'
            });
        } else if (this.value.failed) {
            this.status.css({
                color: '#BF777F'
            });
        } else {
            this.status.css({
                color: '#6891BD'
            });
        }
    }
});

ServicePanel = Tea.Panel.extend('ServicePanel', {
    options: {
        value: null,
        closable: true,
        cls: 'service-panel',
        top: [
            { type: 't-button',
              text: 'redeploy',
              icon: 'redeploy',
              click: 'redeploy'},
            { type: 't-button',
              text: 'edit',
              icon: 'edit',
              click: 'edit'},
            { type: 't-button',
              text: 'delete',
              icon: 'delete',
              cls: 'right',
              click: 'del' },
            { type: 't-button',
              text: 'disable',
              icon: 'disable',
              cls: 'right',
              click: 'dis_or_en_able' }
        ]
    },
    init : function() {
        this.title = this.value.id;
    },
    onRender : function() {
        this.refresh();
        this.hook(this.value, 'update', this.refresh);
        this.hook(this.value, 'log', this.updateLog);
        
        this.value.logCycle(1000);
        this.value.hook(this, 'remove', this.value.cancelLogCycle);
        
        this.log = this.append({
            type: 't-element',
            cls: 'log'
        });
        
        this._scrollTop = true;
        
        if (this.value.log)
            this.updateLog(this.value.log);
        
        this.skin.content.scroll(Tea.method(this.scrollChange, this));
    },
    scrollChange : function(e) {
        var content = this.skin.content;
        if (content[0].scrollTop + content.height() >= content[0].scrollHeight) this._scrollTop = true;
        else this._scrollTop = false;
    },
    refresh : function() {
        var button = this.skin.top.items[3];
        if (this.value.disabled) {
            button.setText('enable');
            button.setIcon('enable');
        } else {
            button.setText('disable');
            button.setIcon('disable');
        }
    },
    updateLog : function(lines) {
        var self = this;
        jQuery.each(lines, function(index, item) {
            //var date = new Date(item.created * 1000);
            self.last = item.created;
            $('<div class="log-item">')
                .append($('<div class="icon icon-' + item.levelname.toLowerCase() + '">'))
                .append(item.message)
                .attr('title', item.filename + ":" + item.funcName + "()")
                .addClass('level-' + item.levelname.toLowerCase())
                .appendTo(self.log.source);
        });
        
        if (this._scrollTop) {
            var content = this.skin.content;
            content[0].scrollTop = content[0].scrollHeight;
        }
    },
    redeploy : function() {
        this.value.redeploy();
    },
    del : function() {
        console.log("Delete");
        dialog = ConfirmDialog({
            prompt: "Are you sure you want to delete this service?  This cannot be undone.",
            success: this.value.del,
            context: this.value
        });
        dialog.show();
    },
    dis_or_en_able : function() {
        console.log("toggle_enabled");
        if (this.value.disabled) {
            this.value.enable();
        } else {
            this.value.disable();
        }
    },
    edit : function() {
        var stack = this.findParent(Tea.Stack);
        stack.pop(this);
        stack.push(ServiceEditPanel({value: this.value}));
    }
});

ServiceList = Tea.Panel.extend("ServiceList", {
    options : {
        title: 'services',
        cls: 'services',
        value: null,
        closable: true
    },
    init : function() {
        this.hook(this.value, 'new-service', this.addService);
        for(var i = 0; i < this.value.services.length; i++) {
            this.addService(Service(this.value.services[i]));
        }
    },
    addService : function(service) {
        var button = ServiceButton({value: service});
        this.append(button);
    }
});

ServiceEditPanel = Tea.Panel.extend("ServiceEditPanel", {
    options : {
        closable: true,
        cls: 'service-editor editor',
        value: null,
        title: "edit service"
    },
    init : function() {
        this.setValue(this.value);
    },
    setValue : function(v) {
        if (v) {
            this.setFields(app.getType(v.type).fields);
        }
        this.__super__(v);
    },
    setFields : function(fields) {
        this.empty();
        for (var i = 0; i < fields.length; i++) {
            var field = fields[i];
            console.log(field);
            console.log( this.append(field) );
        }
    }
});