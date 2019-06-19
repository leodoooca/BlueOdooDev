# -*- coding: utf-8 -*-
import requests
import json
import logging
import datetime
import time

from odoo import models, api, fields
from odoo.tools.translate import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ProviderAccount(models.Model):
    _inherit = ['account.online.provider']

    provider_type = fields.Selection(selection_add=[('ponto', 'Ponto')])
    ponto_token = fields.Char(readonly=True, help='Technical field that contains the ponto token')

    @api.multi
    def _get_available_providers(self):
        ret = super(ProviderAccount, self)._get_available_providers()
        ret.append('ponto')
        return ret

    def _build_ponto_headers(self):
        authorization = "Bearer " + self.ponto_token
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": authorization
        }

    def _ponto_fetch(self, method, url, params, data):
        base_url = 'https://api.myponto.com'
        if not url.startswith(base_url):
            url = base_url + url
        try:
            if data:
                data = json.dumps(data)
            headers = self._build_ponto_headers()
            resp = requests.request(method=method, url=url, params=params, data=data, headers=headers, timeout=60)
            resp_json = resp.json()
            if resp_json.get('errors') or resp.status_code >= 400:
                message = ('%s for route %s') % (json.dumps(resp_json.get('errors')), url)
                if resp_json.get('errors', [{}])[0].get('code', '') == 'authorizationCodeInvalid':
                    message = _('Invalid access token')
                self.log_ponto_message(message)
            return resp_json
        except requests.exceptions.Timeout as e:
            _logger.exception(e)
            raise UserError(_('Timeout: the server did not reply within 60s'))
        except requests.exceptions.ConnectionError as e:
            _logger.exception(e)
            raise UserError(_('Server not reachable, please try again later'))
        except ValueError as e:
            _logger.exception(e)
            self.log_ponto_message('%s for route %s' % (resp.text, url))

    @api.multi
    def get_login_form(self, site_id, provider, beta=False):
        if provider != 'ponto':
            return super(ProviderAccount, self).get_login_form(site_id, provider, beta)
        return {
            'type': 'ir.actions.client',
            'tag': 'ponto_online_sync_widget',
            'name': _('Link your Ponto account'),
            'target': 'new',
            'context': self._context,
        }

    def log_ponto_message(self, message):
        # We need a context check because upon first synchronization the account_online_provider record is created and just after
        # we call api to get accounts but this call can result on an error (token not correct or else) and the transaction
        # would be rollbacked causing an error if we try to post a message on the deleted record with a new cursor. Solution 
        # is to not try to log message in that case.
        if not self._context.get('no_post_message'):
            subject = _("An error occurred during online synchronization")
            message = _('The following error happened during the synchronization: %s' % (message,))
            with self.pool.cursor() as cr:
                self.with_env(self.env(cr=cr)).message_post(body=message, subject=subject)
                self.with_env(self.env(cr=cr)).write({'status': 'FAILED', 'action_required': True})
        raise UserError('An error has occurred: %s' % (message,))


    def _update_ponto_accounts(self, method='add'):
        resp_json = self._ponto_fetch('GET', '/accounts', {}, {})
        res = {'added': self.env['account.online.journal']}
        for account in resp_json.get('data', {}):
            # Fetch accounts
            vals = {
                'balance': account.get('attributes', {}).get('currentBalance', 0)
            }
            account_search = self.env['account.online.journal'].search([('account_online_provider_id', '=', self.id), ('online_identifier', '=', account.get('id'))], limit=1)
            if len(account_search) == 0:
                # Since we just create account, set last sync to 15 days in the past to retrieve transaction from latest 15 days
                last_sync = self.last_refresh - datetime.timedelta(days=15)
                vals.update({
                    'name': account.get('attributes', {}).get('description', _('Account')),
                    'online_identifier': account.get('id'),
                    'account_online_provider_id': self.id,
                    'account_number': account.get('attributes', {}).get('reference', {}),
                    'last_sync': last_sync,
                })
                acc = self.env['account.online.journal'].create(vals)
                res['added'] += acc
        self.write({'status': 'SUCCESS', 'action_required': False})
        res.update({'status': 'SUCCESS',
            'message': '',
            'method': method,
            'number_added': len(res['added']),
            'journal_id': self.env.context.get('journal_id', False)})
        return self.show_result(res)

    def success_callback(self, token):
        # Create account.provider and fetch account
        vals = {
            'name': _('Ponto'),
            'ponto_token': token,
            'provider_identifier': 'ponto',
            'status': 'SUCCESS',
            'status_code': 0,
            'message': '',
            'last_refresh': fields.Datetime.now(),
            'action_required': False,
            'provider_type': 'ponto',
        }
        new_provider_account = self.create(vals)
        return new_provider_account.with_context(no_post_message=True)._update_ponto_accounts()

    @api.multi
    def manual_sync(self):
        if self.provider_type != 'ponto':
            return super(ProviderAccount, self).manual_sync()
        transactions = []
        for account in self.account_online_journal_ids:
            if account.journal_ids:
                tr = account.retrieve_transactions()
                transactions.append({'journal': account.journal_ids[0].name, 'count': tr})
        self.write({'status': 'SUCCESS', 'action_required': False})
        result = {'status': 'SUCCESS', 'transactions': transactions, 'method': 'refresh', 'added': self.env['account.online.journal']}
        return self.show_result(result)

    @api.multi
    def update_credentials(self):
        if self.provider_type != 'ponto':
            return super(ProviderAccount, self).update_credentials()
        # Fetch new accounts if needed
        return self._update_ponto_accounts(method='edit')

    @api.model
    def cron_fetch_online_transactions(self):
        if self.provider_type != 'ponto':
            return super(ProviderAccount, self).cron_fetch_online_transactions()
        self.manual_sync()


class OnlineAccount(models.Model):
    _inherit = 'account.online.journal'

    ponto_last_synchronization_identifier = fields.Char(readonly=True, help='id of ponto synchronization')

    def _ponto_synchronize(self):
        # To fetch the latest transactions and balance of accounts we have to call a special
        # url on ponto to tell him to refresh the data, this ressource is called "synchronization"
        # We have to call it for both "account" and "transactions" as ponto does not have the option
        # to have both in one. Once the "synchronization" are finished, their status will changed to "success"
        # and we know we can now continue and fetch the latest transactions and account balance.
        subtype = 'accountDetails'
        data = {
            'data': {
                'type': 'synchronization',
                'attributes': {
                    'resourceType': 'account',
                    'resourceId': self.online_identifier,
                    'subtype': subtype
                }
            }
        }
        # Synchronization ressource for account
        resp_json_accounts = self.account_online_provider_id._ponto_fetch('POST', '/synchronizations', {}, data)
        subtype = 'accountTransactions'
        # Synchronization ressource for transaction
        resp_json_transactions = self.account_online_provider_id._ponto_fetch('POST', '/synchronizations', {}, data)
        # Get id of synchronization ressources
        sync_account_id = resp_json_accounts.get('data', {}).get('id')
        sync_account = resp_json_accounts.get('data', {}).get('attributes', {})
        sync_transaction_id = resp_json_transactions.get('data', {}).get('id')
        sync_transaction = resp_json_transactions.get('data', {}).get('attributes', {})
        # Fetch synchronization ressources until it has been updated
        count = 0
        while True:
            if count == 180:
                raise UserError(_('Fetching transactions took too much time.'))
            if sync_account.get('status') not in ('success', 'error'):
                resp_json_accounts = self.account_online_provider_id._ponto_fetch('GET', '/synchronizations/' + sync_account_id, {}, {})
            if sync_transaction.get('status') not in ('success', 'error'):
                resp_json_transactions = self.account_online_provider_id._ponto_fetch('GET', '/synchronizations/' + sync_transaction_id, {}, {})
            sync_account = resp_json_accounts.get('data', {}).get('attributes', {})
            sync_transaction = resp_json_transactions.get('data', {}).get('attributes', {})
            if sync_account.get('status') in ('success', 'error') and sync_transaction.get('status') in ('success', 'error'):
                # If we are in error, log the error and stop
                if sync_account.get('status') == 'error':
                    self.account_online_provider_id.log_ponto_message(json.dumps(sync_account.get('errors')))
                elif sync_transaction.get('status') == 'error':
                    self.account_online_provider_id.log_ponto_message(json.dumps(sync_transaction.get('errors')))
                break
            count += 1
            time.sleep(2)
        return

    @api.multi
    def retrieve_transactions(self):
        if (self.account_online_provider_id.provider_type != 'ponto'):
            return super(OnlineAccount, self).retrieve_transactions()
        # actualize the data in ponto
        self._ponto_synchronize()
        transactions = []
        # Update account balance
        url = '/accounts/%s' % (self.online_identifier,)
        resp_json = self.account_online_provider_id._ponto_fetch('GET', url, {}, {})
        end_amount = resp_json.get('data', {}).get('attributes', {}).get('currentBalance', 0)
        self.balance = end_amount
        # Fetch transactions.
        # Transactions are paginated so we need to loop to ensure we have every transactions, we keep
        # in memory the id of the last transaction fetched in order to start over from there.
        url = url + '/transactions'
        first_sync = True
        last_sync = self.last_sync or fields.Datetime.now() - datetime.timedelta(days=15)
        if self.ponto_last_synchronization_identifier:
            url += '?after=' + self.ponto_last_synchronization_identifier
            first_sync = False
        last_transaction = self.ponto_last_synchronization_identifier
        while True:
            resp_json = self.account_online_provider_id._ponto_fetch('GET', url, {}, {})
            url = resp_json.get('links', {}).get('next', False)
            for transaction in resp_json.get('data', []):
                last_transaction = transaction.get('id')
                tr_date = fields.Date.from_string(transaction.get('attributes', {}).get('valueDate'))
                # If we are synchronizing for the first time, ignore transactions older than specified last_sync date.
                if first_sync and tr_date < last_sync:
                    continue
                trans = {
                    'online_identifier': transaction.get('id'),
                    'date': fields.Date.from_string(transaction.get('attributes', {}).get('valueDate')),
                    'name': transaction.get('attributes', {}).get('remittanceInformation'),
                    'amount': transaction.get('attributes', {}).get('amount'),
                    'account_number': transaction.get('attributes', {}).get('counterpartReference'),
                    'end_amount': end_amount
                }
                if transaction.get('attributes', {}).get('counterpartName'):
                    trans['online_partner_vendor_name'] = transaction['attributes']['counterpartName']
                    trans['partner_id'] = self._find_partner([('online_partner_vendor_name', '=', transaction['attributes']['counterpartName'])])
                transactions.append(trans)
            if not url or not transaction:
                self.ponto_last_synchronization_identifier = last_transaction
                break
        # Create the bank statement with the transactions
        return self.env['account.bank.statement'].online_sync_bank_statement(transactions, self.journal_ids[0])
