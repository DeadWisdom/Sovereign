app = Tea.Application({
    init : function() {
        this.services = Tea.Container({
            cls: 'services'
        });
    },
    ready : function() {
        this.services.render().appendTo(document.body);
        this.getInfo();
    },
    getInfo : function() {
        $.ajax({
            url: '/info',
            success: Tea.method(this.onInfo, this)
        });
    },
    onInfo : function(node) {
        this.services.clear();
        $.each(node.services, function(i, item) {
            console.log(item);
            app.services.append(
                Tea.Element({
                    cls: 'service',
                    html: item.id + ' - ' + item.status
                })
            )
        });
    }
});