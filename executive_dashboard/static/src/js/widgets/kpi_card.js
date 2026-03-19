odoo.define("executive_dashboard.kpi_card", function(require) {
"use strict";
const { Component } = owl;
class KPICard extends Component {}
KPICard.template = "executive_dashboard.KPICard";
KPICard.defaultProps = { color: "blue", icon: "📊", editMode: false };
return { KPICard };
});
