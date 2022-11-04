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


class MaintenanceNames(models.Model):
    _name = 'maintenance.names'

    name = fields.Char(string='Nombre de mantenimiento')
    maintenances = fields.One2many('maintenance.property', inverse_name='name')



class MaintenancePerProperty(models.Model):
    _name = 'maintenance.property'

    name = fields.Many2one('maintenance.names') 
    team_id = fields.Many2one('maintenance.team', string="Equipo responsable")
    cost = fields.Float(string="Costo")
    frequency = fields.Selection([('once', 'Unico'), ('Daily', 'Diario'), ('Weekly', 'Semanal'), ('Monthly', 'Mensual'), ('semestre', 'Semestral'), ('Yearly', 'Anual')], default='once', string="Frecuencia")
    charge_to = fields.Selection([('tenant','Inquilino'),('landlord','Propietario'),('admin','Administrador')], string="A cuenta de quien")
    charge = fields.Boolean(string="Aplicar cargo")

    property_id = fields.Many2one('account.asset.asset')

    def name_get(self):
        context = self.env.context
        res = []
        if context.get('special_field', False):
            for rec in self:
                res.append((rec.id, rec.name))
        elif context.get('special_field', 'team'):
            for rec in self:
                res.append((rec.id, rec.team_id))
        elif context.get('special_field', 'frequency'):
            for rec in self:
                res.append((rec.id, rec.frequency))
            for rec in self:
                res.append((rec.id, rec.cost))
        elif context.get('special_field', 'cost'):
            for rec in self:
                res.append((rec.id, rec.cost))
        return res




class MaintenanceContract(models.Model):
    _name = 'maintenance.contract'

    maintenance_id = fields.Many2one('maintenance.property')
    charge = fields.Boolean(string="Aplicar cargo")
    analytic_id = fields.Many2one('account.analytic.account')



class AccountAnalyticModified(models.Model):
    _inherit = 'account.analytic.account'

    def _compute_maintenance(self):
        if self.is_landlord_rent:
            charge_to_query = 'landlord'
        else:
            charge_to_query = 'tenant'
        related_recordset = self.property_id.maintenance_per_property.search(
                [("charge_to", "=", charge_to_query),
                    ("property_id", "=", self.property_id.id),
                    '|',
                    ("frequency", "=", self.frequency),
                    ("frequency", "=", "once")]
                )
        self.maintenance_per_property = related_recordset

    def _compute_frequency(self):
        for rec in self:
            date_diff = (rec.chech_out - rec.chech_in)
            if date_diff < datetime.timedelta(days=8):
                rec.frequency = 'Daily'
            elif date_diff < datetime.timedelta(days=32):
                rec.frequency = 'Weekly'
            elif date_diff < datetime.timedelta(days=30*6):
                rec.frequency = 'Monthly'
            elif date_diff < datetime.timedelta(days=365):
                rec.frequency = 'Semestral'
            else:
                rec.frequency = 'Yearly'

    maintenance_per_property = fields.One2many('maintenance.property', compute="_compute_maintenance")
    maintenance_per_contract = fields.One2many('maintenance.contract', inverse_name='analytic_id')
    frequency = fields.Selection([('Daily', 'Diario'), ('Weekly', 'Semanal'), ('Monthly', 'Mensual'), ('Semestral', 'Semestral'), ('Yearly', 'Anual')], compute='_compute_frequency', string="Frecuencia")
    mirror_contract_id = fields.Many2one('account.analytic.account')
    tenant_tenancy_id = fields.Many2one('account.analytic.account')

    def mirror_contract(self):
        if not self.mirror_contract_id:
            new_mirror = {
                    'name': self.name,
                    'property_id': self.property_id.id,
                    'property_owner_id': self.property_id.property_owner.id,
                    'date_start': self.date_start,
                    'date': self.date,
                    'chech_in': self.chech_in,
                    'chech_out': self.chech_out,
                    'ten_date': self.ten_date,
                    'frequency': self.frequency,
                    'is_landlord_rent': True,
                    'tenant_tenancy_id': self.id,
                    }
            mirror_record = self.mirror_contract_id.create([new_mirror,])
            self.mirror_contract_id = mirror_record[0].id


        return {
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('property_landlord_management.landlord_analytic_view_form_id').id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model' : 'account.analytic.account',
                'res_id': self.mirror_contract_id.id,
                'target': 'current',
                }
