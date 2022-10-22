from odoo import models, fields, api

class SaulMaintenance(models.Model):
    _inherit = 'maintenance.request'

    cost_final = fields.Float(string="Costo al final de la renta")
    cost_daily = fields.Float(string="Costo diario")
    cost_weekly = fields.Float(string="Costo semanal")
    cost_monthly = fields.Float(string="Costo mensual")
    cost_half_yearly = fields.Float(string="Costo semestral")
    cost_yearly = fields.Float(string="Costo anual")
    charge_to = fields.Selection([('tentat','Inquilino'),('landlord','Property'),('admin','Administrador')], string="Encargado de pagar")
    

class SaulAccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    maintenance_per_property_ids = fields.Many2one(comodel_name='maintenance.request')
