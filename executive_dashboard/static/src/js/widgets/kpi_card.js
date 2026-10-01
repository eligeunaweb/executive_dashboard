/** @odoo-module **/
/**
 * KPI Card Component
 * ==================
 * Displays a single KPI metric with trend indicator and sparkline.
 *
 * Props:
 *   kpi: { value, formatted, trend_pct, trend_direction, label, count }
 *   color: 'blue' | 'green' | 'amber' | 'purple'
 *   icon: emoji string
 *   editMode: boolean
 */

import { Component } from "@odoo/owl";

export class KPICard extends Component {
    static template = "executive_dashboard.KPICard";
    static props = {
        kpi: Object,
        color: { type: String, optional: true },
        icon: { type: String, optional: true },
        editMode: { type: Boolean, optional: true },
    };
    static defaultProps = {
        color: 'blue',
        icon: '📊',
        editMode: false,
    };
}
