from odoo import models, fields, api,_
from odoo.exceptions import UserError


class Others_payment(models.Model):

    _name='others.payment'


    other_product = fields.Char(
            string='Gasto',
            )

    qty = fields.Integer(
            string='Cantidad',
            )

    cost = fields.Float(
            string='Costo',
            )

    other_product_id = fields.Many2one(
            'account.analytic.account',
            string='other_id',
            )	

    inv_id = fields.Many2one(
            'account.move',
            string='Factura',
            default=False,
            )

    company_id = fields.Many2one(
            comodel_name='res.company',
            string='Company',
            default=lambda self: self.env.user.company_id)

    currency_id = fields.Many2one(
            comodel_name='res.currency',
            related='company_id.currency_id',
            string='Currency',
            required=True)

    def button_open_other_invoice(self):
        return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': self.inv_id.id,
                'target': 'current',
                }

