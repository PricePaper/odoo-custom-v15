/** @odoo-module */

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

async function executeXlsxReportDownload({ env, action }) {
    env.services.ui.block();
    const url = "/xlsx_reports";
    const data = action.data;
    try {
      await download({ url, data });
    } finally {
      env.services.ui.unblock();
    }
}

registry
    .category("action_handlers")
    .add('ir_actions_xlsx_download', executeXlsxReportDownload);











