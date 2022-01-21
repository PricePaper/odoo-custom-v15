from odoo import fields, models, api


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    def _get_table(self, options):
        headers,lines = super(ReportAccountFinancialReport, self.with_context(print_mode=False))._get_table(options)

        income = {}
        for line in lines:
            if line.get('name') == 'Operating Income' or line.get('id') == 5:
                income = line
                break
        if income:
            t = income['columns'][0].get('no_format')

            for l in lines:
                if l.get('caret_options') or l.get('id') == 'total_6' or l.get('name') == 'Total Gross Profit' or l.get('id') == 4 and l.get('class') == 'total':
                    s = l['columns'][0].get('no_format')
                    p = t> 0.0 and (s / t) * 100 or 0.0
                    l['columns'].append({
                        'name': '{0:0.2f}%'.format(p),
                        'no_format': p,
                        'class': 'number'
                    })
                    headers[0].append({'name': '%', 'class': 'number', 'colspan': 1})
        return headers,lines

