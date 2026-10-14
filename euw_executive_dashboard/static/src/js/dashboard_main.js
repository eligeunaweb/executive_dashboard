odoo.define("executive_dashboard", function(require) {
"use strict";
const { Component, useState } = owl;
const { onWillStart } = owl.hooks;
const AbstractAction  = require("web.AbstractAction");
const core            = require("web.core");
const { KPICard }     = require("euw_executive_dashboard.kpi_card");
const { ChartWidget } = require("euw_executive_dashboard.chart_widget");
// Periodos de la versión gratuita (hoy, semana, año anterior y rangos a medida: versión Pro)
const FREE_PERIODS = ["month", "quarter", "year"];
let _qweb = null;
function _getQWeb() {
    if (_qweb) return Promise.resolve(_qweb);
    _qweb = new owl.QWeb();
    return fetch("/euw_executive_dashboard/static/src/xml/dashboard_templates.xml")
        .then(function(r) { return r.text(); })
        .then(function(xml) { _qweb.addTemplates(xml); return _qweb; });
}
class ExecutiveDashboard extends Component {
    constructor(...args) {
        super(...args);
        this.state = useState({ loading:false, error:null, data:null, editMode:false, currentPeriod:"month", companyName:"", lastUpdated:"", configId:null, theme:localStorage.getItem("ed_theme") || "dark" });
        this._cache = new Map();
        this._refreshTimer = null;
        // Odoo 15 monta el componente antes de insertarlo en la página y onMounted no llega a ejecutarse:
        // los datos se cargan antes del primer pintado.
        onWillStart(async () => { await this._loadConfig(); await this._loadData(); });
    }
    async _fetchData(period, forceRefresh) {
        var key = "dashboard_" + period, cached = this._cache.get(key);
        if (!forceRefresh && cached && Date.now() - cached.ts < 120000) return cached.data;
        var result = await this.env.services.rpc("/executive_dashboard/data", { period: period });
        if (result && result.success) this._cache.set(key, { data: result, ts: Date.now() });
        return result;
    }
    async _loadConfig() {
        try { var c = await this.env.services.rpc("/executive_dashboard/config", {}); this.state.configId = c.config_id; this.state.currentPeriod = FREE_PERIODS.includes(c.default_period) ? c.default_period : "month"; }
        catch(e) { console.error("Config error:", e); }
    }
    async _loadData(forceRefresh) {
        this.state.loading = true; this.state.error = null;
        try {
            var result = await this._fetchData(this.state.currentPeriod, forceRefresh);
            if (result && result.success) { this.state.data = result; this.state.lastUpdated = new Date().toLocaleTimeString("es-ES"); }
            else { this.state.error = (result && result.error) || "Error al cargar datos"; }
        } catch(e) { this.state.error = "Error: " + e.message; }
        finally { this.state.loading = false; }
    }
    toggleTheme() {
        const theme = this.state.theme === "dark" ? "light" : "dark";
        this.state.theme = theme;
        localStorage.setItem("ed_theme", theme);
    }

    async onPeriodChange(ev) { this.state.currentPeriod = ev.target.value; await this._loadData(true); }
    async refreshData() { this._cache.clear(); await this._loadData(true); }
}
ExecutiveDashboard.template   = "euw_executive_dashboard.Dashboard";
ExecutiveDashboard.components = { KPICard, ChartWidget };
const ExecutiveDashboardAction = AbstractAction.extend({
    hasControlPanel: false,
    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            return _getQWeb().then(function(qweb) { self._qweb = qweb; });
        });
    },
    // Odoo 15: el componente se monta cuando la acción ya está en la página; si se monta antes,
    // OWL no ejecuta onMounted (ni la carga del gráfico).
    on_attach_callback: function() {
        if (this._edMounted) return;
        this._edMounted = true;
        var self = this;
        var env = { qweb: this._qweb, services: {
            rpc: function(route, params) { return self._rpc({ route: route, params: params || {} }); },
            notification: { add: function(msg, opts) { self.displayNotification({ message: msg, type: (opts && opts.type) || "info" }); } },
        }};
        owl.mount(ExecutiveDashboard, { target: self.el, env: env });
    },
});
core.action_registry.add("executive_dashboard", ExecutiveDashboardAction);
});
