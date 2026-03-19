odoo.define("executive_dashboard", function(require) {
"use strict";
const { Component, useState } = owl;
const { onMounted, onWillUnmount } = owl.hooks;
const AbstractAction  = require("web.AbstractAction");
const core            = require("web.core");
const { KPICard }     = require("executive_dashboard.kpi_card");
const { ChartWidget } = require("executive_dashboard.chart_widget");
const AUTO_REFRESH_MS = 5 * 60 * 1000;
let _qweb = null;
function _getQWeb() {
    if (_qweb) return Promise.resolve(_qweb);
    _qweb = new owl.QWeb();
    return fetch("/executive_dashboard/static/src/xml/dashboard_templates.xml")
        .then(function(r) { return r.text(); })
        .then(function(xml) { _qweb.addTemplates(xml); return _qweb; });
}
class ExecutiveDashboard extends Component {
    constructor(...args) {
        super(...args);
        this.state = useState({ loading:false, error:null, data:null, editMode:false, currentPeriod:"month", companyName:"", lastUpdated:"", configId:null });
        this._cache = new Map();
        this._refreshTimer = null;
        onMounted(async () => { await this._loadConfig(); await this._loadData(); this._startAutoRefresh(); });
        onWillUnmount(() => this._stopAutoRefresh());
    }
    async _fetchData(period, forceRefresh) {
        var key = "dashboard_" + period, cached = this._cache.get(key);
        if (!forceRefresh && cached && Date.now() - cached.ts < 120000) return cached.data;
        var result = await this.env.services.rpc("/executive_dashboard/data", { period: period });
        if (result && result.success) this._cache.set(key, { data: result, ts: Date.now() });
        return result;
    }
    async _loadConfig() {
        try { var c = await this.env.services.rpc("/executive_dashboard/config", {}); this.state.configId = c.config_id; this.state.currentPeriod = c.default_period || "month"; }
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
    async onPeriodChange(ev) { this.state.currentPeriod = ev.target.value; await this._loadData(true); }
    async refreshData() { this._cache.clear(); await this._loadData(true); }
    async toggleEditMode() { this.state.editMode = !this.state.editMode; }
    _startAutoRefresh() { this._refreshTimer = setInterval(async () => { this._cache.clear(); await this._loadData(true); }, AUTO_REFRESH_MS); }
    _stopAutoRefresh() { if (this._refreshTimer) { clearInterval(this._refreshTimer); this._refreshTimer = null; } }
}
ExecutiveDashboard.template   = "executive_dashboard.Dashboard";
ExecutiveDashboard.components = { KPICard, ChartWidget };
const ExecutiveDashboardAction = AbstractAction.extend({
    hasControlPanel: false,
    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            return _getQWeb().then(function(qweb) {
                var env = { qweb: qweb, services: {
                    rpc: function(route, params) { return self._rpc({ route: route, params: params || {} }); },
                    notification: { add: function(msg, opts) { self.displayNotification({ message: msg, type: (opts && opts.type) || "info" }); } },
                }};
                return owl.mount(ExecutiveDashboard, { target: self.el, env: env });
            });
        });
    },
});
core.action_registry.add("executive_dashboard", ExecutiveDashboardAction);
});
