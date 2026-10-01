# Executive Dashboard for Odoo Community

**Author:** Álvaro Martínez  
**Website:** [eligeunaweb.es](https://eligeunaweb.es)  
**Support:** soporte@eligeunaweb.com  
**License:** OPL-1  

---

## Description

Real-time executive dashboard for Odoo Community. Get instant visibility into sales, invoicing, purchases, stock and more — all in one screen with live alerts and trend indicators. No Enterprise license required.

---

## Installation

1. Copy the `executive_dashboard` folder to your Odoo addons directory
2. Restart Odoo
3. Go to **Settings → Apps → Update Apps List**
4. Search for "Executive Dashboard" and install

---

## Compatibility

| Odoo Version | Status |
|---|---|
| 15.0 Community | ✅ Supported |
| 16.0 Community | ✅ Supported |
| 17.0 Community | ✅ Supported |
| 18.0 Community | ✅ Supported |
| 19.0 Community | ✅ Supported |

---

## Features

- 8 KPI cards with trend vs prior period
- Sales vs Invoicing comparison chart (bar/line toggle)
- Sales by Category donut chart
- Smart alerts: overdue invoices, low stock, late POs
- Top Customers table with payment status
- Period selector: today, week, month, quarter, year
- Live auto-refresh every 5 minutes
- Native dark mode
- Multi-company support

---

## File Map

```
controllers/dashboard.py       ← All KPI data endpoints
models/dashboard_config.py     ← Per-user config storage
models/dashboard_widget.py     ← Widget definitions
static/src/js/
  dashboard_main.js            ← Root Owl component
  widgets/kpi_card.js          ← KPI card component
  widgets/chart_widget.js      ← Chart.js wrapper
static/src/xml/
  dashboard_templates.xml      ← Owl templates
static/src/css/
  dashboard.css                ← All styles (scoped under .ed-root)
```

---

## Support

For questions or issues, contact: soporte@eligeunaweb.com

---

## Pro Version

Need more? The **Executive Dashboard Pro** adds:
- Configurable widgets with drag & drop
- 15 KPIs including Net Margin and CRM Pipeline
- Per-widget date ranges
- Custom colors and sizes per widget

Available at [eligeunaweb.es](https://eligeunaweb.es)
