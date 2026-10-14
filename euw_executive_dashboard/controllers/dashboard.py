# -*- coding: utf-8 -*-
"""
Dashboard Controller
====================
All KPI data is computed here and returned as JSON to the OWL frontend.
"""
import json
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ExecutiveDashboardController(http.Controller):

    @http.route('/executive_dashboard/data', type='json', auth='user', methods=['POST'])
    def get_dashboard_data(self, period='month', date_from=None, date_to=None):
        try:
            df, dt = self._get_date_range(period, date_from, date_to)
            prev_df, prev_dt = self._get_previous_period(df, dt)
            company_id = request.env.company.id

            return {
                'success': True,
                'period': {'from': df.isoformat(), 'to': dt.isoformat()},
                'kpis': {
                    'sales':       self._get_sales_kpi(df, dt, prev_df, prev_dt, company_id),
                    'invoicing':   self._get_invoicing_kpi(df, dt, prev_df, prev_dt, company_id),
                    'overdue':     self._get_overdue_kpi(company_id),
                    'orders_open': self._get_open_orders_kpi(company_id),
                },
                'charts': {
                    'sales_evolution': self._get_sales_evolution(df, dt, company_id),
                },
            }
        except Exception as e:
            _logger.error('Dashboard data error: %s', str(e), exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/executive_dashboard/config', type='json', auth='user', methods=['POST'])
    def get_or_create_config(self):
        config = request.env['executive.dashboard.config'].get_or_create_for_current_user()
        return {
            'config_id':      config.id,
            'layout_json':    config.layout_json or '[]',
            'default_period': config.default_period,
            'widgets': [{
                'id': w.id, 'name': w.name, 'widget_type': w.widget_type,
                'grid_x': w.grid_x, 'grid_y': w.grid_y, 'grid_w': w.grid_w, 'grid_h': w.grid_h,
            } for w in config.widget_ids if w.active],
        }

    # ─── KPIs ──────────────────────────────────────────────────────────────────

    def _get_sales_kpi(self, df, dt, prev_df, prev_dt, company_id):
        cr = request.env.cr
        cr.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(amount_total), 0) as total
            FROM sale_order
            WHERE state IN ('sale', 'done') AND company_id = %s
              AND date_order::date BETWEEN %s AND %s
        """, (company_id, df, dt))
        current = cr.dictfetchone()
        cr.execute("""
            SELECT COALESCE(SUM(amount_total), 0) as total
            FROM sale_order
            WHERE state IN ('sale', 'done') AND company_id = %s
              AND date_order::date BETWEEN %s AND %s
        """, (company_id, prev_df, prev_dt))
        previous = cr.dictfetchone()
        return self._build_kpi(current['total'], current['count'], previous['total'],
                               'Ventas', request.env.company.currency_id.symbol)

    def _get_invoicing_kpi(self, df, dt, prev_df, prev_dt, company_id):
        cr = request.env.cr
        cr.execute("""
            SELECT COUNT(*) as count,
                   COALESCE(SUM(amount_total_signed), 0) as total,
                   COALESCE(SUM(CASE WHEN payment_state IN ('not_paid','partial')
                               AND invoice_date_due < CURRENT_DATE
                               THEN amount_residual_signed ELSE 0 END), 0) as overdue
            FROM account_move
            WHERE move_type = 'out_invoice' AND state = 'posted' AND company_id = %s
              AND invoice_date BETWEEN %s AND %s
        """, (company_id, df, dt))
        current = cr.dictfetchone()
        cr.execute("""
            SELECT COALESCE(SUM(amount_total_signed), 0) as total
            FROM account_move
            WHERE move_type = 'out_invoice' AND state = 'posted' AND company_id = %s
              AND invoice_date BETWEEN %s AND %s
        """, (company_id, prev_df, prev_dt))
        previous = cr.dictfetchone()
        result = self._build_kpi(current['total'], current['count'], previous['total'],
                                 'Facturación', request.env.company.currency_id.symbol)
        result['overdue'] = float(current['overdue'])
        return result

    def _get_overdue_kpi(self, company_id):
        cr = request.env.cr
        cr.execute("""
            SELECT COUNT(*) AS count, COALESCE(SUM(amount_residual_signed), 0) AS total
            FROM account_move
            WHERE move_type = 'out_invoice' AND state = 'posted'
              AND payment_state IN ('not_paid', 'partial')
              AND invoice_date_due < CURRENT_DATE AND company_id = %s
        """, (company_id,))
        row = cr.dictfetchone()
        value = float(row['total'] or 0)
        currency = request.env.company.currency_id.symbol
        return {
            'value': value, 'count': int(row['count'] or 0),
            'formatted': self._format_currency(value, currency),
            'trend_pct': None,
            'trend_direction': 'down' if value > 0 else 'up',
            'label': 'Cobros Vencidos',
        }

    def _get_open_orders_kpi(self, company_id):
        cr = request.env.cr
        cr.execute("""
            SELECT COUNT(*) AS count, COALESCE(SUM(amount_total), 0) AS total
            FROM sale_order
            WHERE state IN ('sale', 'done') AND invoice_status != 'invoiced'
              AND company_id = %s
        """, (company_id,))
        row = cr.dictfetchone()
        value = float(row['total'] or 0)
        currency = request.env.company.currency_id.symbol
        return {
            'value': value, 'count': int(row['count'] or 0),
            'formatted': self._format_currency(value, currency),
            'trend_pct': None, 'trend_direction': 'up',
            'label': 'Pedidos Abiertos',
        }

    # ─── Charts ────────────────────────────────────────────────────────────────

    def _get_sales_evolution(self, df, dt, company_id):
        """
        Monthly sales vs invoicing chart.
        Si no hay ventas, muestra solo facturación — el gráfico nunca queda vacío.
        """
        cr = request.env.cr
        three_months_back = dt - relativedelta(months=2)
        chart_from = min(df, three_months_back.replace(day=1))
        chart_to   = dt

        cr.execute("""
            WITH months AS (
                SELECT DATE_TRUNC('month', gs) AS month_date
                FROM generate_series(%s::date, %s::date, '1 month'::interval) gs
            ),
            sales_by_month AS (
                SELECT DATE_TRUNC('month', date_order) AS month_date,
                       COALESCE(SUM(amount_total), 0) AS total
                FROM sale_order
                WHERE state IN ('sale', 'done') AND company_id = %s
                  AND date_order::date BETWEEN %s AND %s
                GROUP BY 1
            ),
            invoices_by_month AS (
                SELECT DATE_TRUNC('month', invoice_date) AS month_date,
                       COALESCE(SUM(amount_total_signed), 0) AS total
                FROM account_move
                WHERE move_type = 'out_invoice' AND state = 'posted'
                  AND company_id = %s AND invoice_date BETWEEN %s AND %s
                GROUP BY 1
            )
            SELECT
                TO_CHAR(m.month_date, 'Mon YY') AS month_label,
                COALESCE(s.total, 0) AS sales_total,
                COALESCE(i.total, 0) AS invoice_total
            FROM months m
            LEFT JOIN sales_by_month    s ON s.month_date = m.month_date
            LEFT JOIN invoices_by_month i ON i.month_date = m.month_date
            ORDER BY m.month_date
        """, (chart_from, chart_to, company_id, chart_from, chart_to,
              company_id, chart_from, chart_to))

        rows = cr.dictfetchall()
        labels    = [r['month_label']         for r in rows]
        sales     = [float(r['sales_total'])   for r in rows]
        invoicing = [float(r['invoice_total']) for r in rows]

        # Si no hay ventas en absoluto, devolver solo facturación como serie única
        if sum(sales) == 0:
            return {
                'labels': labels,
                'values': invoicing,
                'label':  'Facturación',
            }

        return {
            'labels':    labels,
            'sales':     sales,
            'invoicing': invoicing,
        }

    # ─── Helpers ───────────────────────────────────────────────────────────────

    def _get_date_range(self, period, date_from=None, date_to=None):
        today = date.today()
        if period == 'custom' and date_from and date_to:
            return (datetime.strptime(date_from, '%Y-%m-%d').date(),
                    datetime.strptime(date_to, '%Y-%m-%d').date())
        elif period == 'today':   return today, today
        elif period == 'week':    return today - timedelta(days=today.weekday()), today
        elif period == 'month':   return today.replace(day=1), today
        elif period == 'quarter':
            qm = ((today.month - 1) // 3) * 3 + 1
            return today.replace(month=qm, day=1), today
        elif period == 'year':      return today.replace(month=1, day=1), today
        elif period == 'last_year':
            ly = today.year - 1
            return date(ly, 1, 1), date(ly, 12, 31)
        else: return today.replace(day=1), today

    def _get_previous_period(self, df, dt):
        delta = dt - df
        return df - delta - timedelta(days=1), df - timedelta(days=1)

    def _build_kpi(self, value, count, previous_value, label, currency):
        value = float(value or 0)
        previous_value = float(previous_value or 0)
        if previous_value > 0:
            trend_pct = ((value - previous_value) / previous_value) * 100
        else:
            trend_pct = 0.0 if value == 0 else 100.0
        return {
            'value': value, 'count': int(count or 0),
            'formatted': self._format_currency(value, currency),
            'previous_value': previous_value,
            'trend_pct': round(trend_pct, 1),
            'trend_direction': 'up' if trend_pct >= 0 else 'down',
            'label': label,
        }

    def _format_currency(self, value, symbol='€'):
        value = float(value or 0)
        if value >= 1_000_000:  return f"{symbol}{value/1_000_000:.1f}M"
        elif value >= 1_000:    return f"{symbol}{value/1_000:.1f}k"
        else:                   return f"{symbol}{value:,.0f}"

