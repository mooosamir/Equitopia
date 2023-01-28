from datetime import date, datetime
import pytz
from odoo import models, fields, api,_
from odoo.exceptions import UserError,ValidationError
import math
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
import pytz
import calendar
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import json
from lxml import etree
import calendar

class Rent_type_get(models.Model):

    _inherit="rent.type"

    renttype = fields.Selection(selection_add=[('Day', 'Dia')])

    @api.constrains('sequence_in_view')
    def _check_value(self):
        pass


class Landlord_partner_hp(models.Model):

    _inherit='tenancy.rent.schedule'

    hecho_pago = fields.Char(string='H/P')

    payment_echo = fields.Float(
            string='Pago Hecho',
            compute="diff_count",
            )

    gastos_extra = fields.Boolean(string="Gastos extra", default=False)

    @api.depends("pen_amt","amount")
    def diff_count(self):
        for rec in self:
            temp=rec.amount-rec.pen_amt
            if temp:
                rec.payment_echo=temp
            else:
                rec.payment_echo=0.0



    def create_invoice(self):
        res=super(Landlord_partner_hp,self).create_invoice()
        self.env['account.move'].search([('id','=',self.invc_id.id)]).update({
            'numero_pagos':self.hecho_pago,
            })
        return res

class Account_move_hp(models.Model):

    _inherit='account.move'

    numero_pagos = fields.Char(string='Numero de pago')
    gastos_extra = fields.Boolean(string='Es un gasto extra?')

class Account_payment_custom(models.Model):
    _inherit = 'account.payment'

    tipo_de_pago = fields.Selection([('r', "Renta"), ("m", "Mantenimiento"), ("s", "Servicio"), ("o", "Otros"), ("c", "Comisiones")])

    calc_balance = fields.Boolean(string='Balance')

class Account_asset_asset_customs(models.Model):

    _inherit='account.asset.asset'


    hora_entrada = fields.Float(string='Hora de entrada')

    hora_salida = fields.Float(string='Hora de salida')

    entrega_acceso_id = fields.Many2one('res.partner',string='Entrega de accesos')

    count_reg=fields.Integer(compute="_calculo_registro")

    count_reg_state=fields.Integer(compute="_count_estados")

    count_balances=fields.Integer(compute="_contarbalances")

    tarifa_de_propiedad = fields.One2many(
            'rental.rates',
            'propiedad_id',
            string='Tarifa de propiedad',
            )

    send_state_result = fields.Boolean(string='Enviar estado de resultados',default=True)

    @api.constrains('tarifa_de_propiedad')
    def _exite_rental_rates(self):
        for rec in self:
            existe_dict_lines_tarifas={}
            #existe_reacord_lines_tarifa=[]
            #existe_reacord_lines_renta=[]
            for line in rec.tarifa_de_propiedad:
                #raise UserError(line.tipo_tarifa)
                if not line.tipo_tarifa:
                    raise ValidationError("Un campo de tarifa esta vacio")
                if not line.tipo_renta:
                    raise ValidationError("Un campo de tipo de renta esta vacio")
                for item in existe_dict_lines_tarifas.keys():
                    if line.tipo_tarifa==item and line.tipo_renta==existe_dict_lines_tarifas[item]:
                        raise ValidationError("No puede haber tarfia repetida")

                #if line.tipo_tarifa in existe_reacord_lines_tarifa and line.tipo_renta in existe_reacord_lines_renta:
                #	raise ValidationError("No puede haber tarfia repetida")
                existe_dict_lines_tarifas={
                        str(line.tipo_tarifa):line.tipo_renta,				
                        }
                #existe_reacord_lines_tarifa.append(line.tipo_tarifa)
                #existe_reacord_lines_renta.append(line.tipo_renta)

    def _calculo_registro(self):
        """
        suma la cantidad de eventos de calendario
        """
        for rec in self:
            rec.count_reg=self.env['calendar.event'].search_count([('property_calendary','=',rec.id)])

    def _count_estados(self):
        """
        contar la cantidad de estados
        """
        for rec in self:
            rec.count_reg_state=self.env['estado.result'].search_count([('property_id','=',rec.id)])



    def _contarbalances(self):
        for rec in self:
            rec.count_balances=self.env['balance.economyc.report'].search_count([
                ('property_mov_id','=',rec.id)])


    def print_report_property_pdf(self):
    	vals=[]    		
    	user_id=self.env.user.partner_id.id
    	#raise UserError(user_id)
    	estados=self.env['estado.result']    	
    	for lines in estados.search([('foreport','=',True),('manager_id','=',user_id)]):
    		#calendario=self.env['calendar.event'].search([('property_calendary','=',lines.property_id.id)])
    		#fecha_actual=datetime.now()
    		#total_dias=calendar.monthrange(int(fecha_actual.year),fecha_actual.month)[1]
    		#inicio=datetime(fecha_actual.year,fecha_actual.month,1)
    		#fin=datetime(fecha_actual.year,fecha_actual.month,total_dias)
    		#deff=fin-inicio

    		#lista_fecha=[fecha for fecha in (inicio,fin)]


    		#cal=calendar.HTMLCalendar()
    		#cal_format=calendar.month(2022,12)
    		#cal_format=cal_format.replace('border="0"','border="1"')
    		
    		#for item in calendario:

    		vals.append({
    			'property':lines.property_id.name,
    			'company':lines.company_id.name,
    			'fecha':lines.fecha_report,
    			'manager':lines.manager_id.name,
    			'owner':lines.owner_id.name,
    			'estado':lines.estado,
    			'rent_cronograma':lines.rent_cronograma,
    			'rent_efectivo':lines.rent_efectivo,
    			'mantenimientos':lines.mantenimientos,
    			'servicios':lines.servicios,
    			'otros_gastos':lines.otros_gastos,
    			'comisiones':lines.comisiones,
    			'dias_libres':lines.dias_libres,
    			'dias_ocupados':lines.dias_ocupados,
    			'rent_cobradas':lines.rent_cobradas,
    			'rent_por_cobrar':lines.rent_por_cobrar,
    			'ingresos_netos':lines.ingresos_netos,
    			'imagen':lines.imagen,
    		#	'calendar':cal_format,
    			})

    	
    	data={
    	   'ids':self.ids,
    	   'model':self._name,
    	   'vals':vals,    	   
    	}
    	return self.env.ref('custom_property.action_custom_property_report_menu').report_action(self, data=data)









class Rental_rates(models.Model):

    _name='rental.rates'

    tipo_tarifa=fields.Selection(
        string='Tarifa',
        selection=[
                 ('1', 'Tarifa Normal'),                 
                 ('2', 'Tarifa Alta'),
                 ('3', 'Tarifa baja'),                 
        ],
        )

    costo_tarifa = fields.Float(
        string='Costo',
    )	

    tipo_renta=fields.Selection(
        string='Tipo de renta',
        selection=[
                 ('1', 'Diario'),
                 ('2', 'Semanal'),
                 ('3', 'Mensual'),                 
        ],
        )

    fecuencia_de_pagos = fields.Integer(
        string='Frecuencia',
        default="1",
    )

    deposito = fields.Float(
        string='Desposito',
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

    propiedad_id = fields.Many2one(
        'account.asset.asset',
        string='Propiedad id',
    )

class Account_analytic_account_bh(models.Model):

    _inherit='account.analytic.account'

    chech_in = fields.Datetime(string='Check in')

    chech_out = fields.Datetime(string='Check out')

    hora_entrada = fields.Float(string='Hora de entrada')

    hora_salida = fields.Float(string='Hora de salida')

    entrega_acceso_id = fields.Many2one('res.partner',string='Entrega de accesos')

    telefono = fields.Char(string='telefono')

    email = fields.Char(string='Correo')

    chech_in_realizado = fields.Datetime(string='Realizado')

    bandera_in_realizado = fields.Boolean(string='Realizado')

    rate_busy=fields.Html(
            string='Rango ocupado',
            )

    suggested_month=fields.Selection(
        string='Mes',
        selection=[
                 ('1', 'ENERO'),
                 ('2', 'FEBRERO'),
                 ('3', 'MARZO'), 
                  ('4', 'ABRIL'),
                 ('5', 'MAYO'),
                 ('6', 'JUNIO'),                 
                  ('7', 'JULIO'),
                 ('8', 'AGOSTO'),
                 ('9', 'SEPTIEMBRE'), 
                  ('10', 'OCTUBRE'),
                 ('11', 'NOVIEMBRE'),
                 ('12', 'DICIEMBRE'), 
        ],
        default=lambda self:str(fields.datetime.now().month),
        )



    other_line_product_ids = fields.One2many(
            'others.payment',
            'other_product_id',
            string='Otros gastos',
            )



    def buscar_rango(self,days):
        """"
        Funcion para filtar la consulta dependiendo de los dias
        como resultado arroja como la respuesta de la consulta
        """
        if days>=1 and days<=7:
            tarifa_dias=self.env['rental.rates'].search([('propiedad_id','=',self.property_id.id),
                ('tipo_tarifa','=',self.tipo_tarifa),('tipo_renta','=',1)])
            return tarifa_dias #rango uno
        if days>=8 and days<31:
            tarifa_dias=self.env['rental.rates'].search([('propiedad_id','=',self.property_id.id),
                ('tipo_tarifa','=',self.tipo_tarifa),('tipo_renta','=',2)])
            return tarifa_dias #rango dos
        if days>31:
            tarifa_dias=self.env['rental.rates'].search([('propiedad_id','=',self.property_id.id),
                ('tipo_tarifa','=',self.tipo_tarifa),('tipo_renta','=',3)])
            return tarifa_dias #rango tres


    def get_correct_date(self,fecha):
        """
        Convertir la fecha que esta guarda en la base de datos a una que sea
        totalmente funcional para el website
        """     
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        fecha_real=datetime.strftime(pytz.utc.localize
            (datetime.strptime(fecha.strftime("%Y-%m-%d %H:%M:%S"), DEFAULT_SERVER_DATETIME_FORMAT)).
            astimezone(local),"%Y-%m-%d %H:%M:%S")
        return fecha_real


    def calcular_precios_renta(self):
        if not self.property_owner_id:
            ṕropiedad=self.env['account.asset.asset'].search([
                ('id','=',self.property_id.id)])
            self.property_owner_id=ṕropiedad.property_owner.id
            #raise UserError("El campo de dueño esta vacio")
        if not self.chech_in:
            raise UserError("Favor de marcar la hora de entrada")
        if not self.chech_out:
            raise UserError("Favor de marcar la hora de salida")

        self.validate_ranges_date(self.chech_in,self.chech_out)

        data={
                'actividad':'new_tenancy',
                'propiedad_id':self.property_id.id,
                'contratos_id':self._origin.id,
                'duenos_id':self.property_owner_id.id
                }
        self.env['alert.clock'].create(data)
        partner_ids=self.env.user.partner_id.ids
        if self.manager_id:
            partner_ids.append(self.manager_id.partner_id.id)
        if self.property_owner_id:
            partner_ids.append(self.property_owner_id.parent_id.id)
        if self.property_id.property_manager:
            partner_ids.append(self.property_id.property_manager.id)

        name_name=''
        if self.property_id.name:
            name_name+=self.property_id.name+":"
        if self.code:
            name_name+=self.code+"/"
        if self.tenant_id.name:
            name_name+=self.tenant_id.name

        data_calendary={
                'name':name_name,
                'partner_ids':partner_ids,
                'start':self.get_correct_date(self.chech_in),
                'stop':self.get_correct_date(self.chech_out),
                'allday':True,
                'property_calendary':self.property_id.id,  
                'property_tanency':self.id,
                }
        self.env['calendar.event'].create(data_calendary)

        for tenancy_rec in self:
            day_diff=(self.chech_out-self.chech_in).days
            tarifa_select=self.buscar_rango(day_diff)
            if len(tarifa_select)==0:
                raise UserError("No se encontro una tarifa para usar")
            d1=self.chech_in
            #DIARIO
            if day_diff>=1 and day_diff<=7:
                renta_total=tarifa_select.costo_tarifa*day_diff
                pago_real=renta_total/tarifa_select.fecuencia_de_pagos
                for iteracion in range(0,tarifa_select.fecuencia_de_pagos):
                    vard_data={
                            'start_date':d1,
                            'amount':pago_real,
                            'pen_amt':pago_real,
                            'property_id': tenancy_rec.property_id
                            and tenancy_rec.property_id.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id,									
                            }
                    self.write({
                        'rent_schedule_ids':[(0,0,vard_data)]
                        })
                    d1=d1+relativedelta(days=1)
                tenancy_rec.deposit=tarifa_select.deposito	
                tenancy_rec.rent=pago_real		
            #SEMANAL		
            if day_diff>=8 and day_diff<31:
                renta_total=tarifa_select.costo_tarifa*day_diff
                pago_real=renta_total/tarifa_select.fecuencia_de_pagos
                for iteracion in range(0,tarifa_select.fecuencia_de_pagos):
                    vard_data={
                            'start_date':d1,
                            'amount':pago_real,
                            'pen_amt':pago_real,
                            'property_id': tenancy_rec.property_id
                            and tenancy_rec.property_id.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id,	
                            }
                    self.write({
                        'rent_schedule_ids':[(0,0,vard_data)]
                        })
                    d1=d1+relativedelta(weeks=1)
                tenancy_rec.deposit=tarifa_select.deposito
                tenancy_rec.rent=pago_real
            #MENSUAL
            if day_diff>=31:
                intervalo=math.ceil(abs(day_diff/31))
                renta_total=tarifa_select.costo_tarifa*day_diff
                pago_real=renta_total/intervalo
                for iteracion in range(0,intervalo):
                    vard_data={
                            'start_date':d1,
                            'amount':pago_real,
                            'pen_amt':pago_real,
                            'property_id': tenancy_rec.property_id
                            and tenancy_rec.property_id.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id,	
                            }
                    self.write({
                        'rent_schedule_ids':[(0,0,vard_data)]
                        })
                    d1=d1+relativedelta(days=30)
                tenancy_rec.deposit=tarifa_select.deposito	
                tenancy_rec.rent=pago_real						
            self.set_number_pay()
            self.state='open'
            return tenancy_rec.write({'rent_entry_chck': True})	

    tipo_tarifa=fields.Selection(
            string='Tarifa',
            selection=[
                ('1', 'Tarifa Normal'),                 
                ('2', 'Tarifa Alta'),
                ('3', 'Tarifa baja'),                 
                ]
            )

    def insert_accion(self,accion):
        """
        crear los registro de alerta depediendode la actividad o accion
        """
        self.env['alert.clock'].create({
            'actividad':accion,
            'propiedad_id':self.property_id.id,
            'contratos_id':self._origin.id,
            'duenos_id':self.property_owner_id.id,
      })

    @api.onchange('bandera_in_realizado')
    def _onchange_bandera_in_realizado(self):
        if self.bandera_in_realizado:
            self.chech_in_realizado=datetime.now()
            self.insert_accion('checking_in')
        else:
            self.chech_in_realizado=False

    chech_out_realizado = fields.Datetime(string='Realizado')

    bandera_out_realizado = fields.Boolean(string='Realizado')

    @api.onchange('bandera_out_realizado')
    def _onchange_bandera_out_realizado(self):
        if self.bandera_out_realizado:
            self.chech_out_realizado=datetime.now()
            self.insert_accion('checking_out')
        else:
            self.chech_out_realizado=False


    @api.onchange('property_id')
    def _onchange_property_id(self):
        self.entrega_acceso_id=self.property_id.entrega_acceso_id.id
        self.email=self.entrega_acceso_id.email
        self.telefono=self.entrega_acceso_id.phone
        self.hora_entrada=self.property_id.hora_entrada
        self.hora_salida=self.property_id.hora_salida


    def set_number_pay(self):
        """
        crear listado de nombre para la facturacion
        """
        pago=1
        total_hecho=len(self.rent_schedule_ids)
        for rec in self.rent_schedule_ids:
            rec.hecho_pago=str(pago)+"/"+str(total_hecho)
            pago+=1

    def action_invoice_payment(self):
        self.tenancy_invoice()
        self.invoice_other_payments()

    def tenancy_invoice(self):
        inv_obj = self.env['account.move']
        for payment in self.rent_schedule_ids:
            if not payment.invc_id:
                inv_line_values = payment.get_invloice_lines()
                inv_line_dict = inv_line_values[0][2]
                inv_line_dict.update({
                    'name': payment.maintenance_id.name.name if payment.maintenance_id else 'Pago de renta',
                    'is_service': payment.is_service,
                    'maintenance_id': payment.maintenance_id.id,
                })
                new_line_values = [(0, 0, inv_line_dict)]
                inv_values = {
                    'partner_id': payment.tenancy_id.tenant_id.parent_id.id or False,
                    'type': 'out_invoice',
                    'property_id': payment.tenancy_id.property_id.id or False,
                    'invoice_date': datetime.now().strftime(
                        DEFAULT_SERVER_DATE_FORMAT) or False,
                    'invoice_line_ids': new_line_values,
                    'new_tenancy_id': payment.tenancy_id.id,
                    'numero_pagos':payment.hecho_pago,
                    'invoice_date_due':payment.start_date,
                }
                invoice_id = inv_obj.create(inv_values)
                payment.write({'invc_id': invoice_id.id, 'inv': True})
        #publicar las facturas	
        for payment in self.rent_schedule_ids:
            inv_obj = self.env['account.move'].search([('id','=',payment.invc_id.id)])
            if inv_obj.state!='posted':
                inv_obj.action_post()
                payment.move_check=True

    def action_invoice_tenancy(self):
        for invoice_teancy in self.rent_schedule_ids:
            if invoice_teancy.tenancy_id.is_landlord_rent:
                account_jrnl_obj = self.env['account.journal'].search(
                    [('type', '=', 'purchase')], limit=1)
                inv_lines_values = {
                # 'origin': 'tenancy.rent.schedule',
                'quantity': 1,
                'price_unit': invoice_teancy.amount or 0.00,
                'account_id':
                    invoice_teancy.tenancy_id.property_id.expense_account_id.id or False,
                'analytic_account_id': invoice_teancy.tenancy_id.id or False,
                'name': invoice_teancy.maintenance_id.name.name if invoice_teancy.maintenance_id else 'Pago de renta',
                'is_service': invoice_teancy.is_service,
                'maintenance_id': invoice_teancy.maintenance_id.id,
                }
                owner_rec = invoice_teancy.tenancy_id.property_owner_id
                invo_values = {
                'partner_id': invoice_teancy.tenancy_id.property_owner_id.id or False,
                'type': 'in_invoice',
                'invoice_line_ids': [(0, 0, inv_lines_values)],
                'property_id': invoice_teancy.tenancy_id.property_id.id or False,
                'invoice_date': invoice_teancy.start_date or False,
                # 'schedule_id': self.id,
                'new_tenancy_id': invoice_teancy.tenancy_id.id,
                'journal_id': account_jrnl_obj.id or False
                 }
                acc_id = self.env['account.move'].create(invo_values)
                invoice_teancy.write({'invc_id': acc_id.id, 'inv': True})
        #publicar las facturas	
        for payment in self.rent_schedule_ids:
            inv_obj = self.env['account.move'].search([('id','=',payment.invc_id.id)])
            if inv_obj.state!='posted':
                inv_obj.action_post()
                payment.move_check=True

    def invoice_other_payments(self):
        # TODO: Marcar las facturas al finalizar cada mes, si
        # el contrato tiene una frecuencia mensual o superior
        for payment in self.other_line_product_ids:
            if str(payment.inv_id) != 'account.move()':
                continue
            inv_obj = self.env['account.move']

            # 1. Generar facturas
            inv_lines_values = {
                    'quantity': 1,
                    'price_unit': payment.cost or 0.00,
                    'account_id':
                    self.property_id.expense_account_id.id or False,
                    'analytic_account_id': self.id or False,
                    'name': 'Gastos extra',
                    'is_service': False,
                    'maintenance_id': False,
                    }
            invo_values = {
                        'partner_id': self.property_owner_id.id or False,
                        'type': 'in_invoice',
                        'invoice_line_ids': [(0, 0, inv_lines_values)],
                        'property_id': self.property_id.id or False,
                        'invoice_date': self.date or False,
                        # 'schedule_id': self.id,
                        'new_tenancy_id': self.id,
                        'gastos_extra': True,
                        }
            new_invoice = inv_obj.create(invo_values)

            # 2. Publicar las facturas
            new_invoice.action_post()

            # 3. Añadir factura a la tabla
            payment.inv_id = new_invoice.id

    def button_cancel_tenancy(self):
        """
        Cuando se cancela un contrato se eliminar la alerta y al programacion del
        calendario
        """
        res=super(Account_analytic_account_bh,self).button_cancel_tenancy()
        self.env['alert.clock'].search([('contratos_id','=',self.id)]).unlink()
        self.env['calendar.event'].search([('property_tanency','=',self.id)]).unlink()
        return res

    def button_close(self):
        """
        Cuando se cancela un contrato se eliminar la alerta y al programacion del
        calendario pero con solo cerrar el contrato
        """
        res=super(Account_analytic_account_bh,self).button_close()
        self.env['alert.clock'].search([('contratos_id','=',self.id)]).unlink()
        self.env['calendar.event'].search([('property_tanency','=',self.id)]).unlink()
        return res


    def action_quotation_send(self):
        """
        envia correo electronico de los contratos de inquilino
        valida sus respetivos remitentes y destinatarios
        """
        if not self.manager_id:
            raise UserError("No cuenta con el remitente ")
        if not self.tenant_id:
            raise UserError("Inquilino esta vacio")
        if not self.entrega_acceso_id:
            raise UserError("Entrega de accesos vacio")

        template_id=self.env.ref('custom_property.email_template_contrato').id
        self.env['mail.template'].browse(template_id).send_mail(self.id,force_send=True)

    def action_tenancy_send(self):
        """
        Envia correo electronico de los contratos de propietario
        valida sus respetivos remitentes y destinatarios
        """
        if not self.property_owner_id:
            raise UserError("No cuenta con el remitente ")
        if not self.contact_id:
            raise UserError("Contacto esta vacio")
        if not self.manager_id:
            raise UserError("Gerente de cuentas o remitente vacio")

        template_id=self.env.ref('custom_property.email_template_contrato_tenancy').id
        self.env['mail.template'].browse(template_id).send_mail(self.id,force_send=True)


    def get_correct_date_show(self,fecha):
        """
        Convertir la fecha que esta guarda en la base de datos a una que sea
        totalmente funcional para el website
        """
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        fecha_real=datetime.strftime(pytz.utc.localize
            (datetime.strptime(fecha.strftime("%Y-%m-%d %H:%M:%S"), DEFAULT_SERVER_DATETIME_FORMAT)).
            astimezone(local),"%d-%m-%Y %H:%M:%S")
        return fecha_real



    def validate_ranges_date(self,inicio,fin):
        """
        con esta funcion se evita que selecionar reservas de propiedad
        con fechas que ya estan ocupadas
        """
        dates_calendar=self.env['calendar.event'].search([])


        date_is_range_busy_start=False
        date_is_range_busy_stop=False
        for calen_dete in dates_calendar:
            if (inicio>=calen_dete.start and inicio<=calen_dete.stop) and calen_dete.property_calendary.id==self.property_id.id:
                date_is_range_busy_start=True				
            if (fin>=calen_dete.start and fin<=calen_dete.stop) and calen_dete.property_calendary.id==self.property_id.id:
                date_is_range_busy_stop=True

        if date_is_range_busy_start or date_is_range_busy_stop:
            raise UserError(_("El rengo de fecha de reserva ya esta ocupado, Favor de usar otra"))

    def _matrix2vector(self, matrix):
        vector = []
        for element in matrix:
            for item in element:
                vector.append(item)
        return vector


    @api.onchange('suggested_month','property_id')
    def _onchange_property_id(self):

        date_temp=str(self.suggested_month)
        actual=datetime.now()
        date_suggested=actual.replace(month=int(date_temp))
       

        total_dias=calendar.monthrange(int(date_suggested.year),date_suggested.month)[1]
        start_filter=date(date_suggested.year,date_suggested.month,1)
        stop_filter=date(date_suggested.year,date_suggested.month,total_dias)

        rangos=self.env['calendar.event'].search([('property_calendary','=',self.property_id.id),
                                                  ('start','>=',start_filter),('stop','<=',stop_filter)])

        month_all=[x for x in range(1,total_dias+1)]	
        
        cal=calendar.HTMLCalendar()

        cal_format=cal.formatmonth(actual.year,int(date_temp))
        cal_format=cal_format.replace('border="0"','border="1"')

        list_free_days=[]
        if rangos:
            busy_days=[]
            for item in rangos:
                busy_days.append([x for x in range(item.start.day,item.stop.day+1)])
            #raise UserError(str(self._matrix2vector(busy_days)))
            day_free=set(month_all).difference(set(self._matrix2vector(busy_days)))
            list_free_days.append(day_free)

        if list_free_days==0:
        	list_free_days=month_all
        #html=''
        #cont=1
        #mark_cal=cal_format
        for lisx in list_free_days:        	
        	for x in lisx:
        		cal_format=cal_format.replace('>%i<'%x, 'style="color:green" bgcolor="#66ff66"><b><u>%i</u></b><'%x)

        self.rate_busy=cal_format

    def get_correct_date_show(self,fecha):
        """
        Convertir la fecha que esta guarda en la base de datos a una que sea
        totalmente funcional 
        """
        if fecha:			
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            fecha_real=datetime.strftime(pytz.utc.localize
                (datetime.strptime(fecha.strftime("%Y-%m-%d %H:%M:%S"), DEFAULT_SERVER_DATETIME_FORMAT)).
                astimezone(local),"%d-%m-%Y %H:%M:%S")
            return fecha_real




# Codigo por Saul
class AccounMoveLineModified(models.Model):
    _inherit = 'account.move.line'

    is_service = fields.Boolean(default=False, string="Es un servicio?")
    maintenance_id = fields.Many2one('maintenance.request', string="Mantenimiento")

