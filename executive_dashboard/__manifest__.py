# -*- coding: utf-8 -*-
{
    'name': 'Executive Dashboard for Odoo Community',
    'version': '17.0.1.3.0',
    'category': 'Reporting/Dashboard',
    'summary': 'Real-time executive KPIs, charts and alerts — no Enterprise license needed',
    'description': """
Executive Dashboard for Odoo Community
=======================================
A professional real-time executive dashboard for Odoo Community.
Get instant visibility into sales, invoicing, purchases, stock and more —
all in one screen with live alerts and trend indicators.

Features
--------
- 8 KPI cards with trend vs prior period
- Sales vs Invoicing comparison chart (bar/line toggle)
- Sales by Category donut chart
- Smart alerts: overdue invoices, low stock, late POs
- Top Customers table with payment status
- Period selector: today, week, month, quarter, year
- Live auto-refresh
- Dark mode native
- Multi-company support

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
        'purchase',
        'stock',
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
            'executive_dashboard/static/src/css/dashboard.css',
            'executive_dashboard/static/src/xml/dashboard_templates.xml',
            'executive_dashboard/static/src/js/widgets/kpi_card.js',
            'executive_dashboard/static/src/js/widgets/chart_widget.js',
            'executive_dashboard/static/src/js/dashboard_main.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'support': 'soporte@eligeunaweb.com',
}