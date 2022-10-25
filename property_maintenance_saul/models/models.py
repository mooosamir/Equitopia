from odoo import models, fields, api

class MaintenanceTeamModified(models.Model):
    _inherit = 'maintenance.team'

    partner_id = fields.Many2one('res.partner', string='Company')

class AccountAssetModified(models.Model):
    _inherit = 'account.asset.asset'

    maintenance_by_property = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='property_id')

    # TODO: Delete field below
    maintenance_per_property = fields.Many2one('maintenance.request')

class MaintenancePerProperty(models.Model):
    _inherit = 'maintenance.request'

    charge_tenant = fields.Boolean(string="A cuenta del inquilino")
    frequency = fields.Selection([('o', 'Unico'), ('d', 'Diario'), ('w', 'Semanal'), ('m', 'Mensual'), ('a', 'Anual')], default='o', string="Frecuencia")
    team_id = fields.Many2one('maintenance.team', string="Equipo responsable")

    cost_final = fields.Float(string="Costo al final de la renta")
    cost_daily = fields.Float(string="Costo diario")
    cost_weekly = fields.Float(string="Costo semanal")
    cost_half_monthly = fields.Float(string="Costo quincenal")
    cost_monthly = fields.Float(string="Costo mensual")
    cost_half_yearly = fields.Float(string="Costo semestral")
    cost_yearly = fields.Float(string="Costo anual")
    charge_to = fields.Selection([('tentat','Inquilino'),('landlord','Propietario'),('admin','Administrador')], string="Encargado de pagar")
 

