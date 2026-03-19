/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { KPICard } from "./widgets/kpi_card";
import { ChartWidget } from "./widgets/chart_widget";

const AUTO_REFRESH_MS = 5 * 60 * 1000;

class ExecutiveDashboard extends Component {
    static template = "executive_dashboard.Dashboard";
    static components = { KPICard, ChartWidget };

    setup() {
        this.rpc           = useService("rpc");
        this.notification  = useService("notification");
        this.company       = useService("company");

        this.state = useState({
            loading:       false,
            error:         null,
            data:          null,
            isLive:        true,
            editMode:      false,
            currentPeriod: "month",
            companyName:   "",
            lastUpdated:   "",
            configId:      null,
        });

        this._cache        = new Map();
        this._refreshTimer = null;

        onMounted(async () => {
            await this._loadConfig();
            await this._loadData();
            this._startAutoRefresh();
        });

        onWillUnmount(() => this._stopAutoRefresh());
    }

    // ─── RPC with 2-min cache ──────────────────────────────────────────────────

    async _fetchData(period, forceRefresh = false) {
        const key    = `dashboard_${period}`;
        const cached = this._cache.get(key);
        if (!forceRefresh && cached && Date.now() - cached.ts < 2 * 60 * 1000) {
            return cached.data;
        }
        const result = await this.rpc("/executive_dashboard/data", { period });
        if (result?.success) {
            this._cache.set(key, { data: result, ts: Date.now() });
        }
        return result;
    }

    // ─── Load ──────────────────────────────────────────────────────────────────

    async _loadConfig() {
        try {
            const config = await this.rpc("/executive_dashboard/config", {});
            this.state.configId      = config.config_id;
            this.state.currentPeriod = config.default_period || "month";
        } catch (e) {
            console.error("Config load error:", e);
        }
    }

    async _loadData(forceRefresh = false) {
        this.state.loading = true;
        this.state.error   = null;
        try {
            const result = await this._fetchData(this.state.currentPeriod, forceRefresh);
            if (result?.success) {
                this.state.data        = result;
                this.state.companyName = this.company.currentCompany?.name || "";
                this.state.lastUpdated = new Date().toLocaleTimeString("es-ES");
            } else {
                this.state.error = result?.error || "Error al cargar datos";
            }
        } catch (e) {
            this.state.error = "Error de conexión: " + e.message;
        } finally {
            this.state.loading = false;
        }
    }

    // ─── User interactions ─────────────────────────────────────────────────────

    async onPeriodChange(event) {
        this.state.currentPeriod = event.target.value;
        await this._loadData(true);
    }

    async refreshData() {
        this._cache.clear();
        await this._loadData(true);
        this.notification.add("Dashboard actualizado", { type: "success" });
    }

    async toggleEditMode() {
        if (this.state.editMode) {
            // Exiting edit mode — save layout
            try {
                await this.rpc("/executive_dashboard/save_layout", {
                    config_id:   this.state.configId,
                    layout_json: JSON.stringify([]),
                });
                this.notification.add("Layout guardado", { type: "success" });
            } catch (e) {
                this.notification.add("No se pudo guardar el layout", { type: "warning" });
            }
            this.state.editMode = false;
        } else {
            // Entering edit mode
            this.state.editMode = true;
            this.notification.add(
                "Modo edición — en la versión Pro podrás arrastrar los widgets",
                { type: "info", sticky: false }
            );
        }
    }

    // ─── Auto refresh ──────────────────────────────────────────────────────────

    _startAutoRefresh() {
        this._refreshTimer = setInterval(async () => {
            this._cache.clear();
            await this._loadData(true);
        }, AUTO_REFRESH_MS);
    }

    _stopAutoRefresh() {
        if (this._refreshTimer) {
            clearInterval(this._refreshTimer);
            this._refreshTimer = null;
        }
    }
}

registry.category("actions").add("executive_dashboard", ExecutiveDashboard);
