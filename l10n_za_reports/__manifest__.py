# -*- encoding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

# Copyright (C) 2011 Paradigm Digital  (<http://www.paradigmdigital.co.za>).

{
    'name': 'South Africa - Accounting Reports',
    'version': '1.1',
    'category': 'Localization',
    'description': """
        Accounting reports for South Africa
    """,
    'author': 'Paradigm Digital ',
    'website': 'https://www.paradigmdigital.co.za',
    'depends': [
        'l10n_za', 'account_reports'
    ],
    'data': [
        'data/account_financial_html_report_data.xml',
    ],
    'auto_install': True,
    'license': 'OEEL-1',
}
