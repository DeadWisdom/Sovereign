IntegerInput = Tea.TextInput.extend({
    onRender : function() {
        this.source.keydown(function(e){
            console.log(e);
        })
    }
})


IdField = Tea.TextField.extend('IdField', {});

NoteField = Tea.TextAreaField.extend('NoteField', {});

BoolField = Tea.CheckBoxField.extend('BoolField', {});

StringList = Tea.TextAreaField.extend('StringList', {});
StringDict = Tea.TextAreaField.extend('StringDict', {});

StringField = Tea.TextField.extend('StringField', {});
IntegerField = Tea.TextField.extend('IntegerField', {
    options: {
        input: IntegerInput
    }
});

AddressField = Tea.TextField.extend('AddressField', {});