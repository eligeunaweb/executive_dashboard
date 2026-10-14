/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { KPICard } from "./widgets/kpi_card";
import { ChartWidget } from "./widgets/chart_widget";

// Periodos de la versión gratuita (hoy, semana, año anterior y rangos a medida: versión Pro)
const FREE_PERIODS = ["month", "quarter", "year"];

class ExecutiveDashboard extends Component {
    static template = "euw_executive_dashboard.Dashboard";
    static components = { KPICard, ChartWidget };

    setup() {
        this.notification = useService("notification");

        this.state = useState({
            loading:       false,
            error:         null,
            data:          null,
            currentPeriod: "month",
            companyName:   "",
            lastUpdated:   "",
            configId:      null,
            theme:         localStorage.getItem("ed_theme") || "dark",
        });

        this._cache        = new Map();

        onMounted(async () => {
            await this._loadConfig();
            await this._loadData();
        });
    }

    toggleTheme() {
        const theme = this.state.theme === "dark" ? "light" : "dark";
        this.state.theme = theme;
        localStorage.setItem("ed_theme", theme);
    }

    async _post(url, params = {}) {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: params,
            }),
        });
        const json = await response.json();
        return json.result;
    }

    async _fetchData(period, forceRefresh = false) {
        const key    = `dashboard_${period}`;
        const cached = this._cache.get(key);
        if (!forceRefresh && cached && Date.now() - cached.ts < 2 * 60 * 1000) {
            return cached.data;
        }
        const result = await this._post("/executive_dashboard/data", { period });
        if (result?.success) {
            this._cache.set(key, { data: result, ts: Date.now() });
        }
        return result;
    }

    async _loadConfig() {
        try {
            const config = await this._post("/executive_dashboard/config", {});
            this.state.configId      = config.config_id;
            this.state.currentPeriod = FREE_PERIODS.includes(config.default_period) ? config.default_period : "month";
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
                this.state.companyName = odoo?.session_info?.user_companies?.current_company?.name || "";
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

    async onPeriodChange(event) {
        this.state.currentPeriod = event.target.value;
        await this._loadData(true);
    }

    async refreshData() {
        this._cache.clear();
        await this._loadData(true);
        this.notification.add("Dashboard actualizado", { type: "success" });
    }
}

registry.category("actions").add("executive_dashboard", ExecutiveDashboard);
