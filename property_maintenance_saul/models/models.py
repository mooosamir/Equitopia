from odoo import models, fields, api
import datetime


class MaintenanceTeamModified(models.Model):
    _inherit = 'maintenance.team'

    partner_id = fields.Many2one('res.partner', string='Company')


class AccountAssetModified(models.Model):
    _inherit = 'account.asset.asset'

    maintenance_per_property = fields.One2many(
        comodel_name='maintenance.property',
        inverse_name='property_id',
        store=True)

    def create_tenancy(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear contrato',
            'res_model': 'account.analytic.account',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('property_management.property_analytic_view_form').id,
            'target': 'current',
            'context': {
                'default_property_id': self.id
            }
        }


class MaintenancePerProperty(models.Model):
    _name = 'maintenance.property'

    name = fields.Char(string='Nombre')
    team_id = fields.Many2one('maintenance.team', string="Equipo responsable")
    cost = fields.Float(string="Costo")
    frequency = fields.Selection([('once', 'Unico'), ('Daily', 'Diario'), ('Weekly', 'Semanal'), ('Monthly', 'Mensual'), ('Yearly', 'Anual')], default='once', string="Frecuencia")
    charge_to = fields.Selection([('tenant','Inquilino'),('landlord','Propietario'),('admin','Administrador')], string="A cuenta de quien")
    charge = fields.Boolean(string="Aplicar cargo")

    property_id = fields.Many2one('account.asset.asset')


class AccountAnalyticModified(models.Model):
    _inherit = 'account.analytic.account'

    def _compute_maintenance(self):
        related_recordset = self.property_id.maintenance_per_property.search(
            [("charge_to", "=", "tenant"),
             ("property_id", "=", self.property_id.id),
             '|',
             ("frequency", "=", self.frequency),
             ("frequency", "=", "once")]
        )
        self.maintenance_per_property = related_recordset

    def _compute_frequency(self):
        for rec in self:
            date_diff = (rec.date - rec.date)
            if date_diff < datetime.timedelta(days=8):
                rec.frequency = 'Daily'
            elif date_diff < datetime.timedelta(days=32):
                rec.frequency = 'Monthly'
            else:
                rec.frequency = 'Yearly'

    maintenance_per_property = fields.One2many('maintenance.property', compute="_compute_maintenance")
    frequency = fields.Selection([('Daily', 'Diario'), ('Weekly', 'Semanal'), ('Monthly', 'Mensual'), ('Yearly', 'Anual')], compute='_compute_frequency', string="Frecuencia")