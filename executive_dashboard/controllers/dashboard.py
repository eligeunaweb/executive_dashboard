# -*- coding: utf-8 -*-
"""
Dashboard Controller
====================
All KPI data is computed here and returned as JSON to the OWL frontend.
Designed to work even when optional modules (stock_account, sale_margin, etc.)
are not installed — every query gracefully falls back to zero.
"""
import logging
from datetime import date, timedelta
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
                    'purchases':   self._get_purchases_kpi(df, dt, prev_df, prev_dt, company_id),
                    'stock':       self._get_stock_kpi(company_id),
                    'margin':      self._get_margin_kpi(df, dt, prev_df, prev_dt, company_id),
                    'overdue':     self._get_overdue_kpi(company_id),
                    'orders_open': self._get_open_orders_kpi(company_id),
                },
                'charts': {
                    'sales_evolution':   self._get_sales_evolution(df, dt, company_id),
                    'sales_by_category': self._get_sales_by_category(df, dt, company_id),
                },
                'tables': {
                    'top_customers': self._get_top_customers(df, dt, company_id),
                },
                'alerts': self._get_alerts(company_id),
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

    @http.route('/executive_dashboard/save_layout', type='json', auth='user', methods=['POST'])
    def save_layout(self, config_id, layout_json):
        config = request.env['executive.dashboard.config'].browse(config_id)
        if config.user_id.id != request.env.uid:
            return {'success': False, 'error': 'Permiso denegado'}
        config.save_layout(layout_json)
        return {'success': True}

    # ─── Helpers: table/column existence ──────────────────────────────────────

    def _table_exists(self, table):
        request.env.cr.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        """, (table,))
        return request.env.cr.fetchone() is not None

    def _column_exists(self, table, column):
        request.env.cr.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        """, (table, column))
        return request.env.cr.fetchone() is not None

    # ─── KPIs ──────────────────────────────────────────────────────────────────

    def _get_sales_kpi(self, df, dt, prev_df, prev_dt, company_id):
        currency = request.env.company.currency_id.symbol
        if not self._table_exists('sale_order'):
            return self._empty_kpi('Ventas', currency)
        try:
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
                                   'Ventas', currency)
        except Exception as e:
            _logger.warning('Sales KPI error: %s', e)
            return self._empty_kpi('Ventas', currency)

    def _get_invoicing_kpi(self, df, dt, prev_df, prev_dt, company_id):
        currency = request.env.company.currency_id.symbol
        if not self._table_exists('account_move'):
            return self._empty_kpi('Facturación', currency)
        try:
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
                                     'Facturación', currency)
            result['overdue'] = float(current['overdue'])
            return result
        except Exception as e:
            _logger.warning('Invoicing KPI error: %s', e)
            return self._empty_kpi('Facturación', currency)

    def _get_purchases_kpi(self, df, dt, prev_df, prev_dt, company_id):
        currency = request.env.company.currency_id.symbol
        if not self._table_exists('purchase_order'):
            return self._empty_kpi('Compras', currency)
        try:
            cr = request.env.cr
            cr.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(amount_total), 0) as total
                FROM purchase_order
                WHERE state IN ('purchase', 'done') AND company_id = %s
                  AND date_order::date BETWEEN %s AND %s
            """, (company_id, df, dt))
            current = cr.dictfetchone()
            cr.execute("""
                SELECT COALESCE(SUM(amount_total), 0) as total
                FROM purchase_order
                WHERE state IN ('purchase', 'done') AND company_id = %s
                  AND date_order::date BETWEEN %s AND %s
            """, (company_id, prev_df, prev_dt))
            previous = cr.dictfetchone()
            return self._build_kpi(current['total'], current['count'], previous['total'],
                                   'Compras', currency)
        except Exception as e:
            _logger.warning('Purchases KPI error: %s', e)
            return self._empty_kpi('Compras', currency)

    def _get_stock_kpi(self, company_id):
        currency = request.env.company.currency_id.symbol
        if not self._table_exists('stock_valuation_layer'):
            return {
                'value': 0, 'count': 0,
                'formatted': self._format_currency(0, currency),
                'trend_pct': None,
                'label': 'Valor Stock',
                'note': 'Requiere módulo Inventario con valoración',
            }
        try:
            cr = request.env.cr
            cr.execute("""
                SELECT COALESCE(SUM(svl.value), 0) AS total_value,
                       COUNT(DISTINCT svl.product_id) AS product_count
                FROM stock_valuation_layer svl
                WHERE svl.company_id = %s
            """, (company_id,))
            result = cr.dictfetchone()
            value = float(result['total_value']) if result else 0.0
            count = int(result['product_count']) if result else 0
            return {
                'value': value, 'count': count,
                'formatted': self._format_currency(value, currency),
                'trend_pct': None,
                'label': 'Valor Stock',
            }
        except Exception as e:
            _logger.warning('Stock KPI error: %s', e)
            return self._empty_kpi('Valor Stock', currency)

    def _get_margin_kpi(self, df, dt, prev_df, prev_dt, company_id):
        env = request.env
        currency = env.company.currency_id.symbol
        if not self._table_exists('sale_order'):
            return self._empty_kpi('Ventas Netas', currency)
        try:
            if self._column_exists('sale_order_line', 'margin'):
                env.cr.execute("""
                    SELECT COALESCE(SUM(sol.margin), 0) AS margin
                    FROM sale_order_line sol JOIN sale_order so ON so.id = sol.order_id
                    WHERE so.state IN ('sale','done') AND so.company_id = %s
                      AND so.date_order::date BETWEEN %s AND %s
                """, (company_id, df, dt))
                cur_m = float(env.cr.fetchone()[0] or 0)
                env.cr.execute("""
                    SELECT COALESCE(SUM(sol.margin), 0) AS margin
                    FROM sale_order_line sol JOIN sale_order so ON so.id = sol.order_id
                    WHERE so.state IN ('sale','done') AND so.company_id = %s
                      AND so.date_order::date BETWEEN %s AND %s
                """, (company_id, prev_df, prev_dt))
                prev_m = float(env.cr.fetchone()[0] or 0)
                env.cr.execute("""
                    SELECT COALESCE(SUM(sol.price_subtotal), 0)
                    FROM sale_order_line sol JOIN sale_order so ON so.id = sol.order_id
                    WHERE so.state IN ('sale','done') AND so.company_id = %s
                      AND so.date_order::date BETWEEN %s AND %s
                """, (company_id, df, dt))
                revenue = float(env.cr.fetchone()[0] or 0)
                margin_pct = (cur_m / revenue * 100) if revenue > 0 else 0.0
                kpi = self._build_kpi(cur_m, 0, prev_m, 'Margen Bruto', currency)
                kpi['margin_pct_label'] = f"{margin_pct:.1f}% de margen"
                return kpi

            env.cr.execute("""
                SELECT COALESCE(SUM(sol.price_subtotal), 0)
                FROM sale_order_line sol JOIN sale_order so ON so.id = sol.order_id
                WHERE so.state IN ('sale','done') AND so.company_id = %s
                  AND so.date_order::date BETWEEN %s AND %s
            """, (company_id, df, dt))
            revenue = float(env.cr.fetchone()[0] or 0)
            env.cr.execute("""
                SELECT COALESCE(SUM(sol.price_subtotal), 0)
                FROM sale_order_line sol JOIN sale_order so ON so.id = sol.order_id
                WHERE so.state IN ('sale','done') AND so.company_id = %s
                  AND so.date_order::date BETWEEN %s AND %s
            """, (company_id, prev_df, prev_dt))
            prev_revenue = float(env.cr.fetchone()[0] or 0)
            kpi = self._build_kpi(revenue, 0, prev_revenue, 'Ventas Netas', currency)
            kpi['margin_pct_label'] = 'Instala sale_margin para margen real'
            return kpi
        except Exception as e:
            _logger.warning('Margin KPI error: %s', e)
            return self._empty_kpi('Ventas Netas', currency)

    def _get_overdue_kpi(self, company_id):
        currency = request.env.company.currency_id.symbol
        if not self._table_exists('account_move'):
            return self._empty_kpi('Cobros Vencidos', currency)
        try:
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
            return {
                'value': value, 'count': int(row['count'] or 0),
                'formatted': self._format_currency(value, currency),
                'trend_pct': None,
                'trend_direction': 'down' if value > 0 else 'up',
                'label': 'Cobros Vencidos',
            }
        except Exception as e:
            _logger.warning('Overdue KPI error: %s', e)
            return self._empty_kpi('Cobros Vencidos', currency)

    def _get_open_orders_kpi(self, company_id):
        currency = request.env.company.currency_id.symbol
        if not self._table_exists('sale_order'):
            return self._empty_kpi('Pedidos Abiertos', currency)
        try:
            cr = request.env.cr
            cr.execute("""
                SELECT COUNT(*) AS count, COALESCE(SUM(amount_total), 0) AS total
                FROM sale_order
                WHERE state IN ('sale', 'done') AND invoice_status != 'invoiced'
                  AND company_id = %s
            """, (company_id,))
            row = cr.dictfetchone()
            value = float(row['total'] or 0)
            return {
                'value': value, 'count': int(row['count'] or 0),
                'formatted': self._format_currency(value, currency),
                'trend_pct': None, 'trend_direction': 'up',
                'label': 'Pedidos Abiertos',
            }
        except Exception as e:
            _logger.warning('Open orders KPI error: %s', e)
            return self._empty_kpi('Pedidos Abiertos', currency)

    # ─── Charts ────────────────────────────────────────────────────────────────

    def _get_sales_evolution(self, df, dt, company_id):
        try:
            cr = request.env.cr
            three_months_back = dt - relativedelta(months=2)
            chart_from = min(df, three_months_back.replace(day=1))
            chart_to   = dt

            has_sales = self._table_exists('sale_order')
            has_invoicing = self._table_exists('account_move')

            if has_sales:
                sales_cte = """
                sales_by_month AS (
                    SELECT DATE_TRUNC('month', date_order) AS month_date,
                           COALESCE(SUM(amount_total), 0) AS total
                    FROM sale_order
                    WHERE state IN ('sale', 'done') AND company_id = %s
                      AND date_order::date BETWEEN %s AND %s
                    GROUP BY 1
                ),"""
                sales_params = (company_id, chart_from, chart_to)
            else:
                sales_cte = "sales_by_month AS (SELECT NULL::date AS month_date, 0::numeric AS total WHERE false),"
                sales_params = ()

            if has_invoicing:
                inv_cte = """
                invoices_by_month AS (
                    SELECT DATE_TRUNC('month', invoice_date) AS month_date,
                           COALESCE(SUM(amount_total_signed), 0) AS total
                    FROM account_move
                    WHERE move_type = 'out_invoice' AND state = 'posted'
                      AND company_id = %s AND invoice_date BETWEEN %s AND %s
                    GROUP BY 1
                )"""
                inv_params = (company_id, chart_from, chart_to)
            else:
                inv_cte = "invoices_by_month AS (SELECT NULL::date AS month_date, 0::numeric AS total WHERE false)"
                inv_params = ()

            all_params = (chart_from, chart_to) + sales_params + inv_params
            cr.execute(f"""
                WITH months AS (
                    SELECT DATE_TRUNC('month', gs) AS month_date
                    FROM generate_series(%s::date, %s::date, '1 month'::interval) gs
                ),
                {sales_cte}
                {inv_cte}
                SELECT
                    TO_CHAR(m.month_date, 'Mon YY') AS month_label,
                    COALESCE(s.total, 0) AS sales_total,
                    COALESCE(i.total, 0) AS invoice_total
                FROM months m
                LEFT JOIN sales_by_month    s ON s.month_date = m.month_date
                LEFT JOIN invoices_by_month i ON i.month_date = m.month_date
                ORDER BY m.month_date
            """, all_params)

            rows = cr.dictfetchall()
            labels    = [r['month_label']         for r in rows]
            sales     = [float(r['sales_total'])   for r in rows]
            invoicing = [float(r['invoice_total']) for r in rows]

            if sum(sales) == 0:
                return {'labels': labels, 'values': invoicing, 'label': 'Facturación'}
            return {'labels': labels, 'sales': sales, 'invoicing': invoicing}
        except Exception as e:
            _logger.warning('Sales evolution chart error: %s', e)
            return {'labels': [], 'values': [], 'label': 'Facturación'}

    def _get_sales_by_category(self, df, dt, company_id):
        try:
            cr = request.env.cr
            if self._table_exists('sale_order'):
                cr.execute("""
                    SELECT COALESCE(pc.complete_name, 'Sin categoría') AS category,
                           COALESCE(SUM(sol.price_subtotal), 0) AS total
                    FROM sale_order_line sol
                    JOIN sale_order so      ON so.id  = sol.order_id
                    JOIN product_product pp ON pp.id  = sol.product_id
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    LEFT JOIN product_category pc ON pc.id = pt.categ_id
                    WHERE so.state IN ('sale', 'done') AND so.company_id = %s
                      AND so.date_order::date BETWEEN %s AND %s
                    GROUP BY pc.complete_name ORDER BY total DESC LIMIT 6
                """, (company_id, df, dt))
                rows = cr.dictfetchall()
                if rows and sum(float(r['total']) for r in rows) > 0:
                    return {
                        'labels': [r['category'] for r in rows],
                        'values': [float(r['total']) for r in rows],
                    }

            if self._table_exists('account_move'):
                cr.execute("""
                    SELECT rp.name AS category,
                           COALESCE(SUM(am.amount_total_signed), 0) AS total
                    FROM account_move am
                    JOIN res_partner rp ON rp.id = am.partner_id
                    WHERE am.move_type = 'out_invoice' AND am.state = 'posted'
                      AND am.company_id = %s AND am.invoice_date BETWEEN %s AND %s
                    GROUP BY rp.name ORDER BY total DESC LIMIT 6
                """, (company_id, df, dt))
                rows = cr.dictfetchall()
                return {
                    'labels': [r['category'] for r in rows],
                    'values': [float(r['total']) for r in rows],
                }
            return {'labels': [], 'values': []}
        except Exception as e:
            _logger.warning('Sales by category chart error: %s', e)
            return {'labels': [], 'values': []}

    # ─── Tables ────────────────────────────────────────────────────────────────

    def _get_top_customers(self, df, dt, company_id, limit=8):
        if not self._table_exists('account_move'):
            return []
        try:
            cr = request.env.cr
            cr.execute("""
                SELECT rp.name as customer_name,
                       COALESCE(SUM(am.amount_total_signed), 0) as total_invoiced,
                       COALESCE(SUM(am.amount_residual_signed), 0) as total_pending,
                       COUNT(am.id) as invoice_count,
                       MAX(am.payment_state) as payment_state
                FROM account_move am
                JOIN res_partner rp ON rp.id = am.partner_id
                WHERE am.move_type = 'out_invoice' AND am.state = 'posted'
                  AND am.company_id = %s AND am.invoice_date BETWEEN %s AND %s
                GROUP BY rp.name ORDER BY total_invoiced DESC LIMIT %s
            """, (company_id, df, dt, limit))
            rows = cr.dictfetchall()
            currency = request.env.company.currency_id.symbol
            return [{
                'name':            r['customer_name'],
                'total':           float(r['total_invoiced']),
                'total_formatted': self._format_currency(r['total_invoiced'], currency),
                'pending':         float(r['total_pending']),
                'invoice_count':   r['invoice_count'],
                'status':          self._payment_status_label(r['payment_state']),
            } for r in rows]
        except Exception as e:
            _logger.warning('Top customers error: %s', e)
            return []

    # ─── Alerts ────────────────────────────────────────────────────────────────

    def _get_alerts(self, company_id):
        alerts = []
        currency = request.env.company.currency_id.symbol

        if self._table_exists('account_move'):
            try:
                cr = request.env.cr
                cr.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount_residual_signed), 0) as total
                    FROM account_move
                    WHERE move_type = 'out_invoice' AND state = 'posted'
                      AND payment_state IN ('not_paid', 'partial')
                      AND invoice_date_due < CURRENT_DATE AND company_id = %s
                """, (company_id,))
                overdue = cr.dictfetchone()
                if overdue and overdue['count'] > 0:
                    alerts.append({
                        'type': 'critical', 'icon': '🚨',
                        'title': f"{overdue['count']} factura(s) vencida(s)",
                        'description': f"Total: {self._format_currency(overdue['total'], currency)}",
                        'action': 'open_overdue_invoices',
                    })
            except Exception as e:
                _logger.warning('Overdue alert error: %s', e)

        if self._table_exists('stock_warehouse_orderpoint') and self._table_exists('stock_quant'):
            try:
                cr = request.env.cr
                cr.execute("""
                    SELECT COUNT(DISTINCT ob.product_id) as count
                    FROM stock_warehouse_orderpoint ob
                    JOIN product_product pp ON pp.id = ob.product_id
                    LEFT JOIN (
                        SELECT sq.product_id, SUM(sq.quantity) as qty_on_hand
                        FROM stock_quant sq
                        JOIN stock_location sl ON sl.id = sq.location_id
                        WHERE sl.usage = 'internal' AND sl.company_id = %s
                        GROUP BY sq.product_id
                    ) quant ON quant.product_id = ob.product_id
                    WHERE ob.company_id = %s
                      AND COALESCE(quant.qty_on_hand, 0) < ob.product_min_qty
                      AND pp.active = true
                """, (company_id, company_id))
                low_stock = cr.dictfetchone()
                if low_stock and low_stock['count'] > 0:
                    alerts.append({
                        'type': 'warning', 'icon': '⚠️',
                        'title': f"{low_stock['count']} producto(s) bajo punto de reorden",
                        'description': 'Revisar y crear órdenes de compra',
                        'action': 'open_low_stock',
                    })
            except Exception as e:
                _logger.warning('Low stock alert error: %s', e)

        if self._table_exists('purchase_order'):
            try:
                cr = request.env.cr
                cr.execute("""
                    SELECT COUNT(*) as count FROM purchase_order
                    WHERE state = 'purchase' AND company_id = %s
                      AND date_planned::date < CURRENT_DATE
                """, (company_id,))
                late_po = cr.dictfetchone()
                if late_po and late_po['count'] > 0:
                    alerts.append({
                        'type': 'warning', 'icon': '📦',
                        'title': f"{late_po['count']} orden(es) de compra con retraso",
                        'description': 'La fecha de entrega esperada ha pasado',
                        'action': 'open_late_po',
                    })
            except Exception as e:
                _logger.warning('Late PO alert error: %s', e)

        if self._table_exists('account_move'):
            try:
                cr = request.env.cr
                cr.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount_total), 0) as total
                    FROM account_move
                    WHERE move_type = 'out_invoice' AND state = 'draft' AND company_id = %s
                """, (company_id,))
                draft_inv = cr.dictfetchone()
                if draft_inv and draft_inv['count'] > 0:
                    alerts.append({
                        'type': 'info', 'icon': 'ℹ️',
                        'title': f"{draft_inv['count']} factura(s) en borrador",
                        'description': f"Valor total: {self._format_currency(draft_inv['total'], currency)}",
                        'action': 'open_draft_invoices',
                    })
            except Exception as e:
                _logger.warning('Draft invoices alert error: %s', e)

        return alerts

    # ─── Date helpers ──────────────────────────────────────────────────────────

    def _get_date_range(self, period, date_from=None, date_to=None):
        from datetime import datetime
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

    # ─── Value helpers ─────────────────────────────────────────────────────────

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

    def _empty_kpi(self, label, currency):
        return {
            'value': 0, 'count': 0,
            'formatted': self._format_currency(0, currency),
            'previous_value': 0,
            'trend_pct': 0.0,
            'trend_direction': 'up',
            'label': label,
        }

    def _format_currency(self, value, symbol='€'):
        value = float(value or 0)
        if value >= 1_000_000:  return f"{symbol}{value/1_000_000:.1f}M"
        elif value >= 1_000:    return f"{symbol}{value/1_000:.1f}k"
        else:                   return f"{symbol}{value:,.0f}"

    def _payment_status_label(self, state):
        mapping = {
            'paid':             {'label': 'Cobrado',   'color': 'green'},
            'in_payment':       {'label': 'En pago',   'color': 'blue'},
            'partial':          {'label': 'Parcial',   'color': 'amber'},
            'not_paid':         {'label': 'Pendiente', 'color': 'amber'},
            'reversed':         {'label': 'Revertido', 'color': 'gray'},
            'invoicing_legacy': {'label': 'Legado',    'color': 'gray'},
        }
        return mapping.get(state, {'label': state or '', 'color': 'gray'})