/** @odoo-module **/
/**
 * KPI Service
 * ===========
 * Simple Odoo service that wraps dashboard API calls with caching.
 * Registered correctly for Odoo 16 service registry.
 */

import { registry } from "@web/core/registry";

const CACHE_TTL_MS = 2 * 60 * 1000; // 2 minutes cache

const kpiServiceDefinition = {
    start(env) {
        const cache = new Map();

        async function _rpc(route, params = {}) {
            return await env.services.rpc(route, params);
        }

        async function getDashboardData(period = "month", forceRefresh = false) {
            const cacheKey = `dashboard_${period}`;
            const cached = cache.get(cacheKey);
            if (!forceRefresh && cached && Date.now() - cached.ts < CACHE_TTL_MS) {
                return cached.data;
            }
            const result = await _rpc("/executive_dashboard/data", { period });
            if (result && result.success) {
                cache.set(cacheKey, { data: result, ts: Date.now() });
            }
            return result;
        }

        async function getConfig() {
            return await _rpc("/executive_dashboard/config", {});
        }

        async function saveLayout(configId, layoutJson) {
            return await _rpc("/executive_dashboard/save_layout", {
                config_id: configId,
                layout_json: layoutJson,
            });
        }

        function invalidateCache(period = null) {
            if (period) {
                cache.delete(`dashboard_${period}`);
            } else {
                cache.clear();
            }
        }

        return { getDashboardData, getConfig, saveLayout, invalidateCache };
    },
};

registry.category("services").add("executive_dashboard.kpi_service", kpiServiceDefinition);
