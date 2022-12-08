{
    'name': 'Custom Property',
    'version': '13.0.1.0.0',
    'category': 'Wb',
    'summary': """
            custom property:
            
     """,
    'author': '',
    'license': 'LGPL-3',
    'website': '',
    'depends': [
       'property_management',
       'property_landlord_management',
       'om_account_asset',
       'calendar',
    ],
    'data': [
       'security/ir.model.access.csv',
       'security/security.xml',
       'views/view_property_for_user.xml',
       'views/count_pago_view.xml',
       'views/Rent_type_view.xml',
       'views/calendary_property.xml',
       'views/balance_economico.xml',
       'views/estado_resultado.xml',
       'report/report_contrator_email.xml',
       'report/menu_report_contraro.xml',
       'report/report_invoice_pago.xml',
       'report/menu_report_estado.xml',
       'report/report_estado_email.xml',
       'data/crono_detalle_economico.xml',
       'data/email_template.xml',
       'data/email_template_estado.xml',
       'data/accones_server.xml'
    ],
   
}
