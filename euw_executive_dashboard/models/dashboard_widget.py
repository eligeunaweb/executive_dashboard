# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DashboardWidget(models.Model):
    """
    Each widget on the dashboard. Defines type, position, and display options.
    The actual data is always fetched live from the controller — never stored here.
    """
    _name = 'executive.dashboard.widget'
    _description = 'Executive Dashboard Widget'
    _order = 'sequence, id'

    config_id = fields.Many2one(
        'executive.dashboard.config',
        string='Dashboard Config',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(string='Widget Name', required=True)
    widget_type = fields.Selection([
        # KPI Cards
        ('kpi_sales', 'KPI — Sales'),
        ('kpi_invoicing', 'KPI — Invoicing'),
        ('kpi_purchases', 'KPI — Purchases'),
        ('kpi_stock_value', 'KPI — Stock Value'),
        ('kpi_overdue', 'KPI — Overdue Invoices'),
        ('kpi_orders_pending', 'KPI — Pending Orders'),
        # Charts
        ('chart_sales_evolution', 'Chart — Sales Evolution'),
        ('chart_sales_by_category', 'Chart — Sales by Category'),
        ('chart_top_customers', 'Chart — Top Customers'),
        # Tables
        ('table_top_customers', 'Table — Top Customers'),
        ('table_top_products', 'Table — Top Products'),
        # Alerts
        ('alerts_panel', 'Alerts Panel'),
    ], string='Widget Type', required=True)

    # GridStack position — kept in sync with layout_json in config
    grid_x = fields.Integer(default=0)
    grid_y = fields.Integer(default=0)
    grid_w = fields.Integer(default=3)  # GridStack units (12-column grid)
    grid_h = fields.Integer(default=2)

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # Display options
    show_trend = fields.Boolean(default=True, string='Show Trend vs Previous Period')
    show_sparkline = fields.Boolean(default=True, string='Show Sparkline')

    @api.model
    def get_default_widgets(self):
        """
        Returns the default widget configuration for a new user.
        This is what they see on first open.
        """
        return [
            # Row 1: KPI cards (each takes 3 of 12 columns)
            {'name': 'Sales', 'widget_type': 'kpi_sales',
             'grid_x': 0, 'grid_y': 0, 'grid_w': 3, 'grid_h': 2, 'sequence': 1},
            {'name': 'Invoicing', 'widget_type': 'kpi_invoicing',
             'grid_x': 3, 'grid_y': 0, 'grid_w': 3, 'grid_h': 2, 'sequence': 2},
            {'name': 'Purchases', 'widget_type': 'kpi_purchases',
             'grid_x': 6, 'grid_y': 0, 'grid_w': 3, 'grid_h': 2, 'sequence': 3},
            {'name': 'Stock Value', 'widget_type': 'kpi_stock_value',
             'grid_x': 9, 'grid_y': 0, 'grid_w': 3, 'grid_h': 2, 'sequence': 4},
            # Row 2: Charts
            {'name': 'Sales Evolution', 'widget_type': 'chart_sales_evolution',
             'grid_x': 0, 'grid_y': 2, 'grid_w': 8, 'grid_h': 4, 'sequence': 5},
            {'name': 'Sales by Category', 'widget_type': 'chart_sales_by_category',
             'grid_x': 8, 'grid_y': 2, 'grid_w': 4, 'grid_h': 4, 'sequence': 6},
            # Row 3
            {'name': 'Top Customers', 'widget_type': 'table_top_customers',
             'grid_x': 0, 'grid_y': 6, 'grid_w': 6, 'grid_h': 4, 'sequence': 7},
            {'name': 'Alerts', 'widget_type': 'alerts_panel',
             'grid_x': 6, 'grid_y': 6, 'grid_w': 6, 'grid_h': 4, 'sequence': 8},
        ]
