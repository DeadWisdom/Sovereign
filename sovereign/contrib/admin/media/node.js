NodeBase = Tea.Class({
    load : function(options) {
        $.ajax(jQuery.extend({
            url: '/info',
            success: Tea.method(this.onLoad, this)
        }, options));
    },
    onLoad : function(info) {
        var old_services = {};
        jQuery.each(this.services || [], function(i, item) {
            old_services[item.id] = item;
        });
        
        jQuery.extend(this, info);
        
        var nw = [];
        var seen = {};
        var node = this;
        this.services = jQuery.map(this.services, function(service) {
            service = Service(service);
            service.node = node;
            seen[service.id] = true;
            if (!old_services[service.id]) nw.push(service);
            return service;
        })
        
        jQuery.each(old_services, function(id, service) {
            if (!seen[id]) service.destroy();
        })
        
        var self = this;
        jQuery.each(nw, function(id, service) {
            self.trigger('new-service', [service]);
        });
        
        self.trigger('update');
    },
    cycle : function(interval) {
        var self = this;
        var refresh = function() {
            self.load({
                success: function(info) {
                    self.onLoad(info);
                    setTimeout(refresh, interval);
                }
            });
        }
        refresh();
    }
});

Node = function(object) {
    if (object instanceof Tea.Object) return object;
    
    var id = object.address.join(":");
    var existing = Node.cache[id];
    if (existing) {
        jQuery.extend(existing, object);
        existing.trigger('update');
        return existing;
    }
    return Node.cache[id] = NodeBase(object);
}

Node.cache = {}

NodeMenu = Tea.Panel.extend({
    options : {
        title: "menu",
        value: null
    },
    init : function() {
        this.append({
            type: 'MenuButton',
            text: 'services',
            icon: 'service',
            panel: 'ServiceList',
            value: this.value
        });
        
        this.append({
            type: 'MenuButton',
            text: 'tasks',
            icon: 'task',
            panel: 'TaskList',
            value: this.value
        });
        
        this.append({
            type: 'MenuButton',
            text: 'vassals',
            icon: 'vassals',
            panel: 'VassalList',
            value: this.value
        });
        
        this.append({
            type: 'MenuButton',
            text: 'packages',
            icon: 'package',
            panel: 'PackageList',
            value: this.value
        });
        
        this.append({
            type: 'MenuButton',
            text: 'users',
            icon: 'user',
            panel: 'UserList',
            value: this.value
        });
        
        // Services - [ +add ]
            // ( node )
            //  - ( service )
        // Tasks - [ +add ]
            // Running
            // Scheduled
            // Library
        // Vassals  - [ +add ]
        // Packages - [ +add ]
        
        this.hook(this.value, 'update', this.refresh);
    },
    refresh : function() {
        this.setTitle(this.value.id);
    }
});

VassalList = Tea.Panel.extend('VassalList', {
    options : {
        title: "vassals",
        value: null
    },
    init : function() {
        
    }
});