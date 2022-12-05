
#-*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError
from datetime import date,datetime
import calendar
import dateutil.relativedelta
# report de resultado de todo el hisorial de cada propiedad
# con sus metricas
class Estado_resultados(models.Model):

	_name="estado.result"
	_rec_name="property_id"

	property_id = fields.Many2one(
	    'account.asset.asset',
	    string='Propiedad',
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


	imagen = fields.Binary(
	    string='Foto',
	    attachment=True,
	)

	rent_cronograma = fields.Float(
	    string='Rentas Programadas',
	)
	rent_efectivo = fields.Float(
	    string='Rentas Efectivas',
	)

	ingreso_neto = fields.Float(
	    string='Ingreso Neto',
	)
	ocupacionlibre = fields.Char(
	    string='Libre',
	)
	ocupacionnl = fields.Char(
	    string='No Libre',
	)
	mantenimientos = fields.Float(
	    string='Mantenimientos',
	)
	servicios = fields.Float(
	    string='Servicios',
	)
	otros_gastos = fields.Float(
	    string='Otros Gastos',
	)
	hao = fields.Float(
	    string='HAO',
	)
	#datos historicos

	rent_cobradas = fields.Float(
	    string='Rentas Cobradas',
	)
	rent_por_cobrar = fields.Float(
	    string='Rentas ha Cobradas',
	)


	#rango de filtros
	fecha_report = fields.Datetime(
	    string='Fecha de reporte',
	)

	enviado = fields.Selection([
		('Enviado', "Correo Enviado"), 
		('Reenviado', "Correo Reenviado"),
		])

	manager_id = fields.Many2one(
	    'res.partner',
	    string='Manejador',
	)
	owner_id = fields.Many2one(
	    'landlord.partner',
	    string='Dueño',
	)

	ingresos_netos = fields.Float(
	    string='Ingresos Netos',
	)


	consulta_mes = fields.Date(string='Mes a consultar')
	##este campo de agrego para poder calcular de foma manual


	

	def action_state_property_unic_send(self):
		"""enviar por correo de forma unica ya generado el reporte"""
		if not self.manager_id:
			raise UserError("No cuentas con mangejandro de cuenta")
		if not self.owner_id:
			raise UserError("No cuenta con Dueño para el envio")
		template_id=self.env.ref('custom_property.email_template_estado').id
		self.env['mail.template'].browse(template_id).send_mail(self.id,force_send=True)
		self.enviado='Reenviado'

		
	
	def action_state_property_send(self,linea_values):
		"""
		envia correo electronico de los estados de propiedad
		valida sus respetivos remitentes y destinatarios
		"""
		template_id=self.env.ref('custom_property.email_template_estado').id
		self.env['mail.template'].browse(template_id).send_mail(linea_values.id,force_send=True)
		linea_values.enviado='Enviado'

	
				

	def calc_property_id(self):
		propiedades=self.env['account.asset.asset'].search([])
		fecha_actual=datetime.now()
		days_max=calendar.monthrange(int(fecha_actual.year),int(fecha_actual.month))
		date_start=date(int(fecha_actual.year),int(fecha_actual.month),1)
		date_stop=date(int(fecha_actual.year),int(fecha_actual.month),int(days_max[1]))
		
		for pd in propiedades:
			pagos=self.env['account.payment']
			#rentas
			rent_cobradas=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','r'),
				('payment_date','>=',date_start),('payment_date','<=',date_stop)]).mapped('amount'))

			rent_por_cobrar=sum(self.env['account.move'].search([('property_id','=',pd.id),
				('invoice_date','>=',date_start),('invoice_date','<=',date_stop)]).mapped('amount_residual'))
				
			#rent_por_cobrar=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','r')]).mapped('amount'))
			#rentas mensual
			rent_efectivo=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','r'),
			  	('payment_date','>=',date_start),('payment_date','<=',date_stop)]).mapped('amount'))
			rent_cronograma=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','r'),
				   	('payment_date','>=',date_start),('payment_date','<=',date_stop)]).mapped('amount'))

			#servicos
			servicios=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','s'),
					('payment_date','>=',date_start),('payment_date','<=',date_stop)]).mapped('amount'))
			#mantenimientos
			mantenimientos=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','m'),
				('payment_date','>=',date_start),('payment_date','<=',date_stop)]).mapped('amount'))
			#eservaciones
			activiades=self.env['calendar.event'].search([('start_date','>=',date_start),
				('stop_date','<=',date_stop)])
			libre=0			
			for item in activiades:
				libre+=(item.stop_date-item.start_date).days
			pocetaje_libre=(libre*100)/int(days_max[1])
			ocupacionlibre=str(libre) +" dias " +str(pocetaje_libre)+ "%"
			ocupacionnl=str(int(days_max[1])-libre) +" dias " +str(100-pocetaje_libre)+"%"

			otros_gastos=0

			data_save={
			     'property_id':pd.id, 
				 'fecha_report':fecha_actual,
				 'manager_id':pd.property_manager.id,
				 'owner_id':pd.property_owner.id,				 
				 'imagen':pd.image,
				 'rent_cobradas':rent_cobradas,
				 'rent_por_cobrar':rent_por_cobrar,
				 'rent_efectivo':rent_efectivo,
				 'servicios':servicios,
				 'mantenimientos':mantenimientos,
				 'ocupacionlibre':ocupacionlibre,
				 'ocupacionnl':ocupacionnl,
				 'ingresos_netos':rent_efectivo-(servicios+mantenimientos+otros_gastos),
				}
			linea_values=self.create(data_save)
			self.action_state_property_send(linea_values)
		
#si en  dado caso se el reporte de hace cada dia 1 de mes entonce hay que restarle uno al mes