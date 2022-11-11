from odoo import models, fields, api
from odoo.exceptions import ValidationError
import datetime


class MaintenanceTeamModified(models.Model):
    _inherit = 'maintenance.team'

    partner_id = fields.Many2one('res.partner', string='Company')


class AccountAssetModified(models.Model):
    _inherit = 'account.asset.asset'

    maintenance_per_property = fields.One2many(
            comodel_name='maintenance.request',
            inverse_name='property_id',
            store=True)

    commission_percentage = fields.Float(string="Comisión (porcentaje)")
    commission_value = fields.Float(string="Comisión")

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
                    'default_property_id': self.id,
                    'default_property_owner_id': self.property_owner.id,
                    }
                }

    @api.onchange('commission_percentage', 'commission_value')
    def check_commission(self):
        if self.commission_percentage > 100:
            raise ValidationError('Error en valores de comisión: No puedes elegir un porcentaje mayor al 100%')
        if self.commission_percentage != 0 and self.commission_value != 0:
            raise ValidationError('Error en valores de comisión: Solo se puede definir un valor porcentual o fijo, no ambos')


class MaintenanceNames(models.Model):
    _name = 'maintenance.names'

    name = fields.Char(string='Nombre de mantenimiento')
    maintenances = fields.One2many('maintenance.request', inverse_name='name')



class MaintenancePerProperty(models.Model):
    _inherit = 'maintenance.request'

    name = fields.Many2one('maintenance.names')
    team_id = fields.Many2one('maintenance.team', string="Equipo responsable")
    cost = fields.Float(string="Costo")
    frequency = fields.Selection([('once', 'Unico'), ('Daily', 'Diario'), ('Weekly', 'Semanal'), ('Monthly', 'Mensual'), ('semestre', 'Semestral'), ('Yearly', 'Anual')], default='once', string="Frecuencia")
    to_charge = fields.Selection([('tenant','Inquilino'),('landlord','Propietario'),('admin','Administrador')], string="A cuenta de quien")
    charge = fields.Boolean(string="Aplicar cargo")

    property_id = fields.Many2one('account.asset.asset')

    def name_get(self):
        context = self.env.context
        res = []
        translation = {'once': 'Unico', 'Daily': 'Diario', 'Weekly': 'Semanal', 'Monthly': 'Mensual', 'semestre': 'Semestral', 'Yearly': 'Anual'}
        for rec in self:
            res.append((rec.id, translation[rec.frequency]))
        return res



class MaintenanceContract(models.Model):
    _name = 'maintenance.contract'

    def _compute_name(self):
        for rec in self:
            rec.table_name = rec.maintenance_request.name.name

    def _compute_team(self):
        for rec in self:
            rec.table_team = rec.maintenance_request.team_id

    def _compute_cost(self):
        for rec in self:
            rec.table_cost = rec.maintenance_request.cost

    def _compute_frequency(self):
        for rec in self:
            val = rec.maintenance_request.frequency
            if val == 'once':
                rec.table_frequency = 'Unico'
            elif val == 'Daily':
                rec.table_frequency = 'Diario'
            elif val == 'Weekly':
                rec.table_frequency = 'Semanal'
            elif val == 'Monthly':
                rec.table_frequency = 'Mensual'
            elif val == 'semestre':
                rec.table_frequency = 'Semestral'
            elif val == 'Yearly':
                rec.table_frequency = 'Anual'
            else:
                rec.table_frequency = 'Invalido'


    maintenance_request = fields.Many2one('maintenance.request')
    charge = fields.Boolean(string="Aplicar cargo")
    analytic_id = fields.Many2one('account.analytic.account')
    property_id = fields.Many2one('account.asset.asset')
    table_name = fields.Char(compute='_compute_name', string='Nombre')
    table_cost = fields.Float(compute='_compute_cost', string='Costo')
    table_team = fields.Many2one('maintenance.team', compute='_compute_team', string='Equipo')



class AccountAnalyticModified(models.Model):
    _inherit = 'account.analytic.account'

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

    maintenance_per_property = fields.One2many('maintenance.contract', inverse_name='analytic_id')
    frequency = fields.Selection([('Daily', 'Diario'), ('Weekly', 'Semanal'), ('Monthly', 'Mensual'), ('Semestral', 'Semestral'), ('Yearly', 'Anual')], compute='_compute_frequency', string="Frecuencia")
    # Mirror contract: For tenant view
    mirror_contract_id = fields.Many2one('account.analytic.account')
    # Mirror contract: For landlord view
    tenant_tenancy_id = fields.Many2one('account.analytic.account')

    def mirror_contract(self):

        return {
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('property_landlord_management.landlord_analytic_view_form_id').id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model' : 'account.analytic.account',
                'res_id': self.mirror_contract_id.id,
                'target': 'current',
                }

    def calular_precios_renta(self):  # FIXME: Typo
        res = super(AccountAnalyticModified,self).calular_precios_renta()

        for rec in self:
            if rec.is_landlord_rent:
                to_charge_query = 'landlord'
            else:
                to_charge_query = 'tenant'
            related_recordset = rec.property_id.maintenance_per_property.search(
                    [
                        ("to_charge", "=", to_charge_query),
                        ("property_id", "=", rec.property_id.id),
                        '|',
                        ("frequency", "=", rec.frequency),
                        ("frequency", "=", "once")
                        ]
                    )
            for maintenance in related_recordset:
                if maintenance.frequency == 'Daily':
                    times = 0
                    while times < rec.chech_in - rec.chech_out:
                        self.add_maintenance(rec, rec.chech_out + times, maintenance)
                        times += 1
                elif maintenance.frequency == 'Weekly':
                    times = 0
                    while times < rec.chech_in - rec.chech_out:
                        self.add_maintenance(rec, rec.chech_out + times*8, maintenance)
                        times += 1
                elif maintenance.frequency == 'Montly':
                    times = 0
                    while times < rec.chech_in - rec.chech_out:
                        self.add_maintenance(rec, rec.chech_out + times*32, maintenance)
                        times += 1
                elif maintenance.frequency == 'Semestral':
                    times = 0
                    while times < rec.chech_in - rec.chech_out:
                        self.add_maintenance(rec, rec.chech_out + times*30*6, maintenance)
                        times += 1
                elif maintenance.frequency == 'Yearly':
                    times = 0
                    while times < rec.chech_in - rec.chech_out:
                        self.add_maintenance(rec, rec.chech_out + times*365, maintenance)
                        times += 1
                else:
                    self.add_maintenance(rec, rec.chech_in , maintenance)

            maintenance_entries = self.env['maintenance.contract'].search([('analytic_id', '=', rec.id)])
            rec.maintenance_per_property = maintenance_entries

        # Mirror contract
        for rec in self:
            if not rec.mirror_contract_id:
                new_mirror = {
                        'name': rec.name,
                        'property_id': rec.property_id.id,
                        'property_owner_id': rec.property_id.property_owner.id,
                        'date_start': rec.date_start,
                        'date': rec.date,
                        'chech_in': rec.chech_in,
                        'chech_out': rec.chech_out,
                        'ten_date': rec.ten_date,
                        'frequency': rec.frequency,
                        'is_landlord_rent': True,
                        'tenant_tenancy_id': rec.id,
                        'landlord_rent': rec.landlord_rent,
                        'deposit': rec.deposit,
                        }
                mirror_record = rec.mirror_contract_id.create([new_mirror,])
                rec.mirror_contract_id = mirror_record[0].id
                rec.mirror_contract_id.calular_precios_renta()


        return res

    def add_maintenance(self, rec, date, maintenance):
        new_maintenance = {
                'maintenance_request': maintenance.id,
                'analytic_id': rec.id,
                'property_id': rec.property_id.id,
                'charge': True, 
                }

        maintenance_entry = rec.maintenance_per_property.create([new_maintenance,])
        maintenance_entry.maintenance_request.schedule_date = date

    def action_invoice_payment(self):
        res = super(AccountAssetModified, self).action_invoice_payment() 

        for rec in self:
            for maintenance in rec.maintenance_per_property:
                pass



