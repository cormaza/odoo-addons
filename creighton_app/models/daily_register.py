from odoo import fields, models


class CreightonDailyRegister(models.Model):

    _name = "creighton.daily.register"
    _description = "Creighton Daily Register"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "user_id, date DESC"

    date = fields.Date(string="Date", required=True, default=fields.Date.today())
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user.id,
    )

    day_type = fields.Selection(
        string="Day type",
        selection=[
            ("peak", "Baby"),
            ("peak_1", "Baby Day 1"),
            ("peak_2", "Baby Day 2"),
            ("peak_3", "Baby Day 3"),
            ("peak_p", "Peak Day"),
            ("g_peak_1", "Green After Peak 1"),
            ("g_peak_2", "Green After Peak 2"),
            ("g_peak_3", "Green After Peak 3"),
            ("y_peak_1", "Yellow After Peak 1"),
            ("y_peak_2", "Yellow After Peak 2"),
            ("y_peak_3", "Yellow After Peak 3"),
            ("red", "Menstrual Fluid"),
            ("green", "Green Day"),
            ("yellow", "Yellow Day"),
        ],
        required=True,
    )

    day_type_helper = fields.Selection(related="day_type", store=True)

    menstrual_type = fields.Selection(
        string="Menstrual type",
        selection=[
            ("menstrual_h", "H - High Flow"),
            ("menstrual_m", "M - Medium Flow"),
            ("menstrual_l", "L - Low Flow"),
            ("menstrual_vl", "VL - Very Low Flow"),
            ("menstrual_b", "B - Brown Blood"),
        ],
        required=False,
    )

    elasticity_type = fields.Selection(
        string="Elasticity type",
        selection=[
            ("0", "0 - Dry"),
            ("2", "2 - Wet without lubrication"),
            ("2W", "2W - Dumpened without lubrication"),
            ("4", "4 - Shine without lubrication"),
            ("6", "6 - Sticky"),
            ("8", "8 - Adhesive"),
            ("10", "10 - Elastic"),
            ("10DL", "10DL - Wet with lubrication"),
            ("10SL", "10SL - Shine with lubrication"),
            ("10WL", "10WL - Dumpened with lubrication"),
        ],
        required=False,
    )

    color_type = fields.Selection(
        string="Color type",
        selection=[
            ("color_b", "B - Brown"),
            ("color_c", "C - Cloudy"),
            ("color_ck", "C/K - Cloudy/Crystalline"),
            ("color_g", "G - Gummy"),
            ("color_k", "K - Crystalline"),
            ("color_kl", "KL - Crystalline with lubrication"),
            ("color_p", "P - Pasty"),
            ("color_pc", "PC - Pasty and Cloudy"),
            ("color_r", "R - Red"),
            ("color_y", "Y - Yellow"),
        ],
        required=False,
    )

    frequency_type = fields.Selection(
        string="Frequency type",
        selection=[
            ("frequency_x1", "X1"),
            ("frequency_x2", "X2"),
            ("frequency_x3", "X3"),
            ("frequency_ad", "AD - All Day"),
        ],
        required=False,
    )

    def name_get(self):
        res = []
        day_types = dict(self._fields["day_type"]._description_selection(self.env))
        menstrual_types = dict(
            self._fields["menstrual_type"]._description_selection(self.env)
        )
        elasticity_types = dict(
            self._fields["elasticity_type"]._description_selection(self.env)
        )
        color_types = dict(self._fields["color_type"]._description_selection(self.env))
        frequency_types = dict(
            self._fields["frequency_type"]._description_selection(self.env)
        )
        for rec in self:
            day_type = day_types.get(rec.day_type)
            menstrual_type = menstrual_types.get(rec.menstrual_type, False)
            menstrual_type = (
                menstrual_type and menstrual_type.split(" - ")[0].strip() or ""
            )
            elasticity_type = elasticity_types.get(rec.elasticity_type, False)
            elasticity_type = (
                elasticity_type and elasticity_type.split(" - ")[0].strip() or ""
            )
            color_type = color_types.get(rec.color_type, False)
            color_type = color_type and color_type.split(" - ")[0].strip() or ""
            frequency_type = frequency_types.get(rec.frequency_type, False)
            frequency_type = (
                frequency_type and frequency_type.split(" - ")[0].strip() or ""
            )
            name = "{} - {}".format(
                day_type,
                (menstrual_type + elasticity_type + color_type),
            )
            if frequency_type:
                name += " %s" % frequency_type
            res.append((rec.id, name))
        return res
