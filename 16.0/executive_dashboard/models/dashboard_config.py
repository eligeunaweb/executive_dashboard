# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DashboardConfig(models.Model):
    """
    Stores the dashboard layout and widget configuration per user/company.
    Each user can have their own layout independently.
    """
    _name = 'executive.dashboard.config'
    _description = 'Executive Dashboard Configuration'

    name = fields.Char(
        string='Name',
        default='My Dashboard',
        required=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
        index=True,
    )
    # GridStack serialized layout: JSON array of {id, x, y, w, h}
    layout_json = fields.Text(
        string='Layout JSON',
        default='[]',
        help='Serialized GridStack layout. Do not edit manually.',
    )
    widget_ids = fields.One2many(
        'executive.dashboard.widget',
        'config_id',
        string='Widgets',
    )
    # Default period shown on load
    default_period = fields.Selection([
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('quarter', 'This Quarter'),
        ('year', 'This Year'),
    ], string='Default Period', default='month')

    _sql_constraints = [
        (
            'unique_user_company',
            'UNIQUE(user_id, company_id)',
            'Each user can only have one dashboard configuration per company.'
        ),
    ]

    @api.model
    def get_or_create_for_current_user(self):
        """
        Called by the frontend on load.
        Returns the existing config or creates a default one.
        """
        config = self.search([
            ('user_id', '=', self.env.uid),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if not config:
            config = self.create({
                'user_id': self.env.uid,
                'company_id': self.env.company.id,
            })
            # Create default widgets for new users
            config._create_default_widgets()

        return config

    def _create_default_widgets(self):
        """Create the default set of widgets when a user opens the dashboard for the first time."""
        default_widgets = self.env['executive.dashboard.widget'].get_default_widgets()
        for widget_data in default_widgets:
            widget_data['config_id'] = self.id
            self.env['executive.dashboard.widget'].create(widget_data)

    def save_layout(self, layout_json):
        """Called by frontend when user finishes dragging widgets."""
        self.ensure_one()
        self.layout_json = layout_json
        return True
