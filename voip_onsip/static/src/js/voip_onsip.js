odoo.define('voip.onsip', function(require) {
"use strict";

var VoipUserAgent = require('voip.user_agent');

VoipUserAgent.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _getUaConfig: function (result) {
        var config = this._super.apply(this, arguments);
        config.authorizationUser = result.onsip_auth_user;
        return config;
    },
});

});
