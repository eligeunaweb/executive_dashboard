# -*- coding: utf-8 -*-
{
    'name': 'Executive Dashboard for Odoo Community',
    'version': '19.0.2.0.0',
    'category': 'Reporting/Dashboard',
    'summary': 'Free executive dashboard: sales, invoicing, overdue invoices and open orders with trends — no Enterprise license needed',
    'description': """
Executive Dashboard for Odoo Community
=======================================
A free real-time executive dashboard for Odoo Community.
See your key sales and invoicing figures in one screen, with trends against the previous period.

Features
--------
- 4 KPI cards with trend vs prior period: sales, invoicing, overdue invoices and open sales orders
- Sales vs Invoicing monthly chart
- Period selector: month, quarter, year
- Dark mode native
- Multi-company support
- Only requires Sales and Invoicing

Upgrade to Executive Dashboard Pro for margin, purchases, stock value and up to 15 KPIs,
sales by category, top customers, smart alerts, custom date ranges, auto-refresh and
configurable drag & drop widgets.

No Enterprise license required.
Compatible with Odoo 15, 16, 17, 18 and 19 Community.
    """,
    'author': 'Álvaro Martínez',
    'website': 'https://eligeunaweb.es',
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'EUR',
    'images': [
        'static/description/banner.png',
    ],
    'depends': [
        'base',
        'web',
        'sale_management',
        'account',
    ],
    'data': [
        'security/dashboard_security.xml',
        'security/ir.model.access.csv',
        'views/dashboard_menus.xml',
        'data/dashboard_default_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'euw_executive_dashboard/static/src/css/dashboard.css',
            'euw_executive_dashboard/static/src/xml/dashboard_templates.xml',
            'euw_executive_dashboard/static/src/js/widgets/kpi_card.js',
            'euw_executive_dashboard/static/src/js/widgets/chart_widget.js',
            'euw_executive_dashboard/static/src/js/dashboard_main.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'support': 'soporte@eligeunaweb.com',
}