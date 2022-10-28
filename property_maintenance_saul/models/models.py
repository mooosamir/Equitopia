from odoo import models, fields, api

class MaintenanceTeamModified(models.Model):
    _inherit = 'maintenance.team'

    partner_id = fields.Many2one('res.partner', string='Company')


class AccountAssetModified(models.Model):
    _inherit = 'account.asset.asset'

    maintenance_by_property = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='property_id')

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
    _inherit = 'maintenance.request'

    #TODO: Volver a la tabla anterior con 1000 columnas

    team_id = fields.Many2one('maintenance.team', string="Equipo responsable")
    cost = fields.Float(string="Costo")
    frequency = fields.Selection([('once', 'Unico'), ('Day', 'Diario'), ('Weekly', 'Semanal'), ('Monthly', 'Mensual'), ('Yearly', 'Anual')], default='once', string="Frecuencia")
    charge_to_corrected = fields.Selection([('tenant','Inquilino'),('landlord','Propietario'),('admin','Administrador')], string="A cuenta de quien")
    charge = fields.Boolean(string="Aplicar cargo")


class AccountAnalyticModified(models.Model):
    _inherit = 'account.analytic.account'

    def _tentant(self):
        # frequency = self.rent_type_id.renttype.lowercase()
         
        maintenances_return = []
        maintenances = self.property_id.maintenance_by_property.search([("charge_to_corrected", "=", "tenant"), ("frequency", "=", "once")])
        self.tenant_maintenance = maintenances

    tenant_maintenance = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='property_id',
        compute="_tentant")
    