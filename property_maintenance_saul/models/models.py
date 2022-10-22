from odoo import models, fields, api

class MaintenanceTeamModified(models.Model):
    _inherit = 'maintenance.team'

    partner_id = fields.Many2one('res.partner', string='Company')