# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'U.A.E. - Accounting Reports',
    'version': '1.1',
    'category': 'Accounting',
    'description': """
        Accounting reports for United Arab Emirates
    """,
    'depends': [
        'l10n_ae', 'account_reports'
    ],
    'data': [
        'data/account_financial_html_report_data.xml'
    ],
    'auto_install': True,
    'website': 'https://www.odoo.com/page/accounting',
    'license': 'OEEL-1',
}
