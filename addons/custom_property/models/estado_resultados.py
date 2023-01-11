
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
	_rec_name="mes_estado"

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

	
	dias_libres = fields.Float(
	    string='Libre',
	)
	dias_ocupados = fields.Float(
	    string='No Libre',
	)

	porcent_libre = fields.Float(
	    string='Libre',
	)

	procetaje_ocupado = fields.Float(
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
	comisiones = fields.Float(
	    string='Comisiones',
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
	    default=lambda self: fields.datetime.now(),
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

	mes_estado = fields.Char(
	    string='Mes',
	)

	mes_num=fields.Char(
	    string='Num Mes',
	)

	estado = fields.Char(
	    string='Estado',
	)

	foreport = fields.Boolean(
	    string='Website',
	)

	totalgastos_full = fields.Float(
	    string='Totalgastos',
	)

	preview = fields.Boolean(
	    string='Previesta',
	)

	reservaciones = fields.Text(
	    string='recervaciones',
	)

    #Al seleccionar una propiedad llama a la funcion o accion para cargar los respectivos datos 
	@api.onchange('property_id')
	def _onchange_property_id(self):
		fecha_actual=datetime.now()
		dict_state={
			'new_draft':'Reserva Abierta',
			'draft':'Disponible',
			'book':'Reservados',
			'normal':'En Arrendamiento',
			'close':'Ventas',
			'sold':'Vendido',
			'open':'Correr',
			'cancel':'Cancelar',
			}
		self.mes_estado=self.mes_find(fecha_actual.month)
		self.mes_num=fecha_actual.month
		if self.property_id:
			self.imagen=self.property_id.image
			self.manager_id=self.property_id.property_manager.id
			self.owner_id=self.property_id.property_owner.id
			self.estado=dict_state[self.property_id.state]
			self.calc_property_id()




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

	
	def mes_find(self,mes):
		vec=['','ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']
		return vec[mes]				

	def calc_property_id(self):		
		if self.property_id:
			#si no entonces toma solo el de la consulta como resultado solo una propiedad
			propiedades=self.env['account.asset.asset'].search([('id','=',self.property_id.id)])
		else:
			#si el campo de propiedad esta vacio como resultado todas las propiedades
			propiedades=self.env['account.asset.asset'].search([])		

		
		fecha_actual=datetime.now()
		days_max=calendar.monthrange(int(fecha_actual.year),int(fecha_actual.month))
		date_start=date(int(fecha_actual.year),int(fecha_actual.month),1)
		date_stop=date(int(fecha_actual.year),int(fecha_actual.month),int(days_max[1]))		
		datfor=self.env['estado.result']
		for item in datfor.search([('foreport','=',True),('mes_num','=',int(fecha_actual.month))]):
			item.foreport=False		
		for pd in propiedades:
			pagos=self.env['account.payment']
			
			#rentas
			rent_cobradas=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','r')]).mapped('amount'))

			rent_por_cobrar=sum(self.env['account.move'].search([('type','=','out_invoice'),
				('property_id','=',pd.id)]).mapped('amount_residual'))				
			#rentas mensual
			rent_efectivo=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','r'),
			  	('payment_date','>=',date_start),('payment_date','<=',date_stop)]).mapped('amount'))

			rent_cronograma=sum(self.env['account.move'].search([
				('type','=','out_invoice'),('property_id','=',pd.id),
				('invoice_date_due','>=',date_start),
				('invoice_date_due','<=',date_stop)]).mapped('amount_residual'))
			#servicos
			servicios=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','s'),
					('payment_date','>=',date_start),('payment_date','<=',date_stop)]).mapped('amount'))
			#mantenimientos
			mantenimientos=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','m')]).mapped('amount'))
			#eservaciones
			activiades=self.env['calendar.event'].search([('start_date','>=',date_start),
				('stop_date','<=',date_stop),('property_calendary','=',pd.id)])
			ocupados=0			
			for item in activiades:
				ocupados+=(item.stop_date-item.start_date).days

			dias_ocupados=ocupados
			procetaje_ocupado=(ocupados*100)/int(days_max[1])
			dias_libres=int(days_max[1])-ocupados
			porcent_libre=100-procetaje_ocupado
			otros_gastos=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','o'),
			  	('payment_date','>=',date_start),('payment_date','<=',date_stop)]).mapped('amount'))

			reservaciones=self.env['calendar.event'].search([('property_calendary','=',pd.id),
				('start','>=',date_start),('stop','<=',date_stop)])

			html=''
			for item in reservaciones:
				html+=str(item.start)+">"+str(item.stop)+'\n'

			dict_state={
			'new_draft':'Reserva Abierta',
			'draft':'Disponible',
			'book':'Reservados',
			'normal':'En Arrendamiento',
			'close':'Ventas',
			'sold':'Vendido',
			'open':'Correr',
			'cancel':'Cancelar',
			}

			totalgastos=mantenimientos+servicios+otros_gastos		

			#comsiones
			comisiones=sum(pagos.search([('property_id','=',pd.id),('tipo_de_pago','=','c'),
			  	('payment_date','>=',date_start),('payment_date','<=',date_stop)]).mapped('amount'))


			if len(propiedades)>1:
				data_save={
			     'property_id':pd.id, 
				 'fecha_report':fecha_actual,
				 'manager_id':pd.property_manager.id,
				 'owner_id':pd.property_owner.id,				 
				 'imagen':pd.image,
				 'rent_cobradas':rent_cobradas,
				 'rent_cronograma':rent_cronograma,
				 'rent_por_cobrar':rent_por_cobrar,
				 'rent_efectivo':rent_efectivo,
				 'servicios':servicios,
				 'mantenimientos':mantenimientos,
				 'dias_ocupados':dias_ocupados,
				 'procetaje_ocupado':procetaje_ocupado,
				 'dias_libres':dias_libres,
				 'porcent_libre':porcent_libre,
				 'ingresos_netos':rent_efectivo-(totalgastos),
				 'mes_estado':self.mes_find(fecha_actual.month),
				 'mes_num':fecha_actual.month,
				 'estado':dict_state[pd.state],
				 'foreport':True,
				 'totalgastos_full':totalgastos,
				 'preview':True,
				 'recervaciones':html,
				}
				estados_lista=datfor.search([('property_id','=',pd.id),('foreport','=',True)])
				if len(estados_lista)>=1:
					estados_lista.update(data_save)
					if pd.send_state_result:
						self.action_state_property_send(estados_lista)
				else:
					linea_values=self.create(data_save)
					if pd.send_state_result:
						self.action_state_property_send(linea_values)

			else:
				self.rent_cobradas=rent_cobradas
				self.rent_cronograma=rent_cronograma
				self.rent_por_cobrar=rent_por_cobrar
				self.rent_efectivo=rent_efectivo
				self.servicios=servicios
				self.mantenimientos=mantenimientos
				self.dias_ocupados=dias_ocupados
				self.procetaje_ocupado=procetaje_ocupado
				self.dias_libres=dias_libres
				self.porcent_libre=porcent_libre
				self.ingresos_netos=rent_efectivo-(totalgastos)
				self.foreport=True
				self.totalgastos_full=totalgastos
				self.reservaciones=html
				#self.preview=False


			#cargar informacion para la graficar


			graphmonth=self.env['graph.state.result'].search([('mes_cargado','=',str(fecha_actual.month))])
		
			if len(graphmonth):
				graphmonth.update({
					'ingreso_neto':rent_efectivo-(totalgastos),
					'total_gastos':totalgastos,
					'rentas_efectivas':rent_efectivo,
					'fecha_report':fecha_actual,
					'mes_cargado':fecha_actual.month
					})
			else:
				self.env['graph.state.result'].create({
					'property_id':pd.id,
					'ingreso_neto':rent_efectivo-(totalgastos),
					'total_gastos':totalgastos,
					'rentas_efectivas':rent_efectivo,
					'fecha_report':fecha_actual,
					'mes_cargado':fecha_actual.month
					})

		
#si en  dado caso se el reporte de hace cada dia 1 de mes entonce hay que restarle uno al mes