odoo.define("executive_dashboard.chart_widget", function(require) {
"use strict";
const { Component, useState } = owl;
const { useRef, onMounted, onWillUnmount } = owl.hooks;
const PALETTE = { blue:{bg:"rgba(79,142,247,.8)",border:"#4f8ef7"}, green:{bg:"rgba(34,197,94,.7)",border:"#22c55e"}, amber:{bg:"rgba(245,158,11,.7)",border:"#f59e0b"}, purple:{bg:"rgba(167,139,250,.7)",border:"#a78bfa"}, teal:{bg:"rgba(20,184,166,.7)",border:"#14b8a6"}, red:{bg:"rgba(239,68,68,.7)",border:"#ef4444"} };
const DONUT_COLORS = ["#4f8ef7","#22c55e","#f59e0b","#a78bfa","#14b8a6","#ef4444","#fb923c","#e879f9"];
class ChartWidget extends Component {
    constructor(...args) {
        super(...args);
        this.canvasRef = useRef("chartCanvas");
        this.chart = null;
        this.state = useState({ activeType: this.props.chartType || "bar" });
        onMounted(async () => {
            if (!window.Chart) await owl.utils.loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
            this._rebuild(this.props.chartData, this.state.activeType);
        });
        onWillUnmount(() => this._destroy());
    }
    async willUpdateProps(next) { if (next.chartData !== this.props.chartData) setTimeout(() => this._rebuild(next.chartData, this.state.activeType), 0); }
    setType(t) { this.state.activeType = t; this._rebuild(this.props.chartData, t); }
    _destroy() { if (this.chart) { this.chart.destroy(); this.chart = null; } }
    _rebuild(data, type) {
        if (!this.canvasRef.el || !data || !window.Chart) return;
        this._destroy();
        this.chart = new window.Chart(this.canvasRef.el.getContext("2d"), type === "doughnut" ? this._donut(data) : this._bar(data, type));
    }
    _bar(d, type) {
        var isM = d.sales !== undefined && d.invoicing !== undefined, isL = type === "line";
        var ds = isM ? [
            {label:"Ventas",data:d.sales,backgroundColor:isL?"rgba(79,142,247,.12)":PALETTE.blue.bg,borderColor:PALETTE.blue.border,borderWidth:isL?2:0,borderRadius:6,fill:isL,tension:.35,pointRadius:isL?4:0},
            {label:"Facturacion",data:d.invoicing,backgroundColor:isL?"rgba(34,197,94,.12)":PALETTE.green.bg,borderColor:PALETTE.green.border,borderWidth:isL?2:0,borderRadius:6,fill:isL,tension:.35,pointRadius:isL?4:0}
        ] : [{label:d.label||"Valor",data:d.values,backgroundColor:PALETTE.blue.bg,borderColor:PALETTE.blue.border,borderRadius:6}];
        return { type:isL?"line":"bar", data:{labels:d.labels,datasets:ds}, options:{responsive:true,maintainAspectRatio:false,animation:{duration:350},
            plugins:{legend:{labels:{color:"#94a3b8",boxWidth:12,padding:16,font:{size:12}}},tooltip:{backgroundColor:"#1a2133",borderColor:"#2d3a52",borderWidth:1,titleColor:"#e2e8f0",bodyColor:"#94a3b8",padding:10,callbacks:{label:function(c){return" "+c.dataset.label+": €"+Number(c.raw).toLocaleString("es-ES",{maximumFractionDigits:0});}}}},
            scales:{x:{grid:{color:"rgba(255,255,255,.04)"},ticks:{color:"#64748b",font:{size:11}}},y:{grid:{color:"rgba(255,255,255,.04)"},beginAtZero:true,ticks:{color:"#64748b",font:{size:11},callback:function(v){return v>=1000000?("€"+(v/1000000).toFixed(1)+"M"):v>=1000?("€"+(v/1000).toFixed(0)+"k"):("€"+v);}}}}}};
    }
    _donut(d) {
        return { type:"doughnut", data:{labels:d.labels,datasets:[{data:d.values,backgroundColor:DONUT_COLORS,borderWidth:2,borderColor:"#151c2c",hoverOffset:8}]},
            options:{responsive:true,maintainAspectRatio:false,cutout:"68%",animation:{duration:350},
            plugins:{legend:{position:"bottom",labels:{color:"#64748b",boxWidth:10,padding:12,font:{size:11}}},tooltip:{backgroundColor:"#1a2133",borderColor:"#2d3a52",borderWidth:1,titleColor:"#e2e8f0",bodyColor:"#94a3b8",callbacks:{label:function(c){return" "+c.label+": €"+Number(c.raw).toLocaleString("es-ES",{maximumFractionDigits:0});}}}}}}
    }
}
ChartWidget.template = "executive_dashboard.ChartWidget";
ChartWidget.defaultProps = { subtitle: "", chartType: "bar" };
return { ChartWidget };
});
