odoo.define("mail.activity.default.user.crm", function (require) {
    "use strict";
    var field_registry = require("web.field_registry");
    var core = require("web.core");
    var _t = core._t;
    require("mail.Activity");
    var MailActivity = field_registry.get("mail_activity");
    MailActivity.include({
        _openActivityForm: function (id, callback) {
            var self = this;
            if (this.model === "crm.lead") {
                return this._rpc({
                    model: "crm.lead",
                    method: "read",
                    args: [this.res_id, ["user_id"]],
                }).then(function (result) {
                    var current_context = {
                        default_res_id: self.res_id,
                        default_res_model: self.model,
                    };
                    if (result[0].user_id) {
                        current_context.default_user_id = result[0].user_id[0];
                    }
                    var action = {
                        type: "ir.actions.act_window",
                        name: _t("Schedule Activity"),
                        res_model: "mail.activity",
                        view_mode: "form",
                        views: [[false, "form"]],
                        target: "new",
                        context: current_context,
                        res_id: id || false,
                    };
                    return self.do_action(action, {on_close: callback});
                });
            }
            return this._super.apply(this, arguments);
        },
    });
});
