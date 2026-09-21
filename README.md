# Executive Dashboard for Odoo Community

Multi-version executive dashboard module for **Odoo Community 15, 16, 17, 18 and 19**, created by Álvaro Martínez.

It brings sales, invoicing, purchasing and inventory information together in a single executive view without requiring an Odoo Enterprise license.

## Highlights

- 8 KPI cards with comparison against the previous period
- Sales vs. invoicing chart with bar/line toggle
- Sales by category donut chart
- Smart alerts for overdue invoices, low stock and late purchase orders
- Top customers table with payment status
- Period selector: today, week, month, quarter and year
- Live auto-refresh
- Dark mode
- Multi-company support

## Supported versions

The repository keeps a dedicated module tree for each supported Odoo Community release:

- `15.0/executive_dashboard`
- `16.0/executive_dashboard`
- `17.0/executive_dashboard`
- `18.0/executive_dashboard`
- `19.0/executive_dashboard`

## Odoo dependencies

The module integrates with:

- Base
- Web
- Sales
- Purchase
- Inventory
- Accounting

## Installation

1. Choose the directory matching your Odoo version.
2. Copy the `executive_dashboard` directory into your custom addons path.
3. Restart Odoo.
4. Update the Apps list.
5. Install **Executive Dashboard for Odoo Community**.

Always test custom modules in a staging environment before deploying them to production.

## Technical structure

The module uses Odoo models, controllers, views, security rules, data files and backend assets. The frontend dashboard is built with JavaScript, XML templates and CSS integrated into `web.assets_backend`.

## License

The module manifests declare **OPL-1**. See the individual version manifest for module metadata and compatibility details.

## Author

**Álvaro Martínez**  
Web development · E-commerce · Odoo · Accessibility

- [GitHub profile](https://github.com/eligeunaweb)
- [Elige Una Web](https://www.eligeunaweb.es)
- [Personal website](https://alvaromh.com)
