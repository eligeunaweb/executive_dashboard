odoo.define("euw_executive_dashboard.kpi_card", function(require) {
"use strict";
const { Component } = owl;
class KPICard extends Component {}
KPICard.template = "euw_executive_dashboard.KPICard";
KPICard.defaultProps = { color: "blue", icon: "📊", editMode: false };
return { KPICard };
});
