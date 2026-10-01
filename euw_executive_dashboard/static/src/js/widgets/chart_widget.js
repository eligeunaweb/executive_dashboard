/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount, onWillUpdateProps, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

const PALETTE = {
    blue:   { bg: 'rgba(79,142,247,.8)',   border: '#4f8ef7' },
    green:  { bg: 'rgba(34,197,94,.7)',    border: '#22c55e' },
    amber:  { bg: 'rgba(245,158,11,.7)',   border: '#f59e0b' },
    purple: { bg: 'rgba(167,139,250,.7)',  border: '#a78bfa' },
    teal:   { bg: 'rgba(20,184,166,.7)',   border: '#14b8a6' },
    red:    { bg: 'rgba(239,68,68,.7)',    border: '#ef4444' },
};

const DONUT_COLORS = ['#4f8ef7','#22c55e','#f59e0b','#a78bfa','#14b8a6','#ef4444','#fb923c','#e879f9'];

export class ChartWidget extends Component {
    static template  = "executive_dashboard.ChartWidget";
    static props     = {
        title:     String,
        subtitle:  { type: String, optional: true },
        chartData: Object,
        chartType: { type: String, optional: true },
    };
    static defaultProps = { subtitle: '', chartType: 'bar' };

    setup() {
        this.canvasRef = useRef("chartCanvas");
        this.chart     = null;
        this.state     = useState({ activeType: this.props.chartType });

        onMounted(async () => {
            if (!window.Chart) {
                await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
            }
            this._rebuild(this.props.chartData, this.state.activeType);
        });

        onWillUpdateProps((next) => {
            if (next.chartData !== this.props.chartData) {
                setTimeout(() => this._rebuild(next.chartData, this.state.activeType), 0);
            }
        });

        onWillUnmount(() => this._destroy());
    }

    setType(type) {
        this.state.activeType = type;
        this._rebuild(this.props.chartData, type);
    }

    _destroy() {
        if (this.chart) { this.chart.destroy(); this.chart = null; }
    }

    _rebuild(data, type) {
        if (!this.canvasRef.el || !data || !window.Chart) return;
        this._destroy();
        const ctx    = this.canvasRef.el.getContext('2d');
        const config = (type === 'doughnut') ? this._donutConfig(data) : this._barLineConfig(data, type);
        this.chart   = new window.Chart(ctx, config);
    }

    /**
     * Build bar/line config.
     * Key fix: when we have a multi-series chart (sales + invoicing),
     * both datasets must share EXACTLY the same labels array.
     * The backend now returns aligned labels via generate_series,
     * but as a safety net we also merge here on the JS side.
     */
    _barLineConfig(rawData, type) {
        const isMulti = rawData.sales !== undefined && rawData.invoicing !== undefined;
        const isLine  = type === 'line';

        // ── Align labels ──────────────────────────────────────────
        // Both series must have a value for every label.
        // The backend already does this with generate_series,
        // but if for any reason they differ we merge here.
        let data = rawData;
        if (isMulti && rawData.labels) {
            data = { ...rawData }; // use as-is, backend aligns them
        }

        const commonScales = {
            x: {
                grid:  { color: 'rgba(255,255,255,.04)' },
                ticks: { color: '#64748b', font: { size: 11 } },
            },
            y: {
                grid:  { color: 'rgba(255,255,255,.04)' },
                beginAtZero: true,
                ticks: {
                    color: '#64748b',
                    font:  { size: 11 },
                    callback: (v) =>
                        v >= 1_000_000 ? `€${(v/1_000_000).toFixed(1)}M`
                        : v >= 1_000  ? `€${(v/1_000).toFixed(0)}k`
                        : `€${v}`,
                },
            },
        };

        const datasets = isMulti ? [
            {
                label:           'Ventas',
                data:            data.sales,
                backgroundColor: isLine ? 'rgba(79,142,247,.12)' : PALETTE.blue.bg,
                borderColor:     PALETTE.blue.border,
                borderWidth:     isLine ? 2 : 0,
                borderRadius:    isLine ? 0 : 6,
                borderSkipped:   false,
                fill:            isLine,
                tension:         0.35,
                pointRadius:     isLine ? 4 : 0,
                pointHoverRadius: isLine ? 6 : 0,
            },
            {
                label:           'Facturación',
                data:            data.invoicing,
                backgroundColor: isLine ? 'rgba(34,197,94,.12)' : PALETTE.green.bg,
                borderColor:     PALETTE.green.border,
                borderWidth:     isLine ? 2 : 0,
                borderRadius:    isLine ? 0 : 6,
                borderSkipped:   false,
                fill:            isLine,
                tension:         0.35,
                pointRadius:     isLine ? 4 : 0,
                pointHoverRadius: isLine ? 6 : 0,
            },
        ] : [{
            label:           data.label || 'Valor',
            data:            data.values,
            backgroundColor: PALETTE.blue.bg,
            borderColor:     PALETTE.blue.border,
            borderRadius:    6,
            borderSkipped:   false,
        }];

        return {
            type: isLine ? 'line' : 'bar',
            data: { labels: data.labels, datasets },
            options: {
                responsive:          true,
                maintainAspectRatio: false,
                animation:           { duration: 350 },
                interaction:         { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        labels: {
                            color:    '#94a3b8',
                            boxWidth: 12,
                            padding:  16,
                            font:     { size: 12 },
                        },
                    },
                    tooltip: {
                        backgroundColor: '#1a2133',
                        borderColor:     '#2d3a52',
                        borderWidth:     1,
                        titleColor:      '#e2e8f0',
                        bodyColor:       '#94a3b8',
                        padding:         10,
                        callbacks: {
                            label: (ctx) =>
                                ` ${ctx.dataset.label}: €${Number(ctx.raw).toLocaleString('es-ES', {maximumFractionDigits: 0})}`,
                        },
                    },
                },
                scales: commonScales,
            },
        };
    }

    _donutConfig(data) {
        return {
            type: 'doughnut',
            data: {
                labels:   data.labels,
                datasets: [{
                    data:            data.values,
                    backgroundColor: DONUT_COLORS,
                    borderWidth:     2,
                    borderColor:     '#151c2c',
                    hoverOffset:     8,
                }],
            },
            options: {
                responsive:          true,
                maintainAspectRatio: false,
                cutout:              '68%',
                animation:           { duration: 350 },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color:    '#64748b',
                            boxWidth: 10,
                            padding:  12,
                            font:     { size: 11 },
                        },
                    },
                    tooltip: {
                        backgroundColor: '#1a2133',
                        borderColor:     '#2d3a52',
                        borderWidth:     1,
                        titleColor:      '#e2e8f0',
                        bodyColor:       '#94a3b8',
                        callbacks: {
                            label: (ctx) =>
                                ` ${ctx.label}: €${Number(ctx.raw).toLocaleString('es-ES', {maximumFractionDigits: 0})}`,
                        },
                    },
                },
            },
        };
    }
}
