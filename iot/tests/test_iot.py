# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo.tests


@odoo.tests.tagged('post_install', '-at_install')
class TestUi(odoo.tests.HttpCase):
    def test_01_iot_token_tour(self):
        self.browser_js(
            "/web",
            "odoo.__DEBUG__.services['web_tour.tour'].run('iot_token_tour', 'test')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.iot_token_tour.ready", login="admin",
            timeout=100)
