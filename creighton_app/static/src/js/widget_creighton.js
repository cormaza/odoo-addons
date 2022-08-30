odoo.define("web.creighton_widget", function(require) {
    "use strict";
    var basic_fields = require("web.basic_fields");
    var field_registry = require("web.field_registry");

    var CreightonWidget = basic_fields.FieldChar.extend({
        template: "field.creighton",

        _render_creighton_widget: function() {
            var src = "";
            var value = this.value;
            if (!this.value) {
                value = "unknown";
            }

            src = "/creighton_app/static/src/img/" + value + ".png";
            this.$("> img").attr("src", src);
        },

        _renderReadonly: function() {
            return this._render_creighton_widget();
        },

        _renderEdit: function() {
            return this._render_creighton_widget();
        },
    });

    field_registry.add("creighton_widget", CreightonWidget);
    return CreightonWidget;
});
