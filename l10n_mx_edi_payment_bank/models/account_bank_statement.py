from odoo import api, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _l10n_mx_edi_get_payment_extra_data(self, invoice_ids=None):
        res = super(AccountBankStatementLine,
                    self)._l10n_mx_edi_get_payment_extra_data(invoice_ids)
        res.update({
            'l10n_mx_edi_partner_bank_id': self.bank_account_id.id,
        })
        return res

    @api.onchange('partner_id')
    def _l10n_mx_onchange_partner_bank_id(self):
        self.bank_account_id = False
        if len(self.partner_id.bank_ids) == 1:
            self.bank_account_id = self.partner_id.bank_ids
