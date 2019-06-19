odoo.define('account_invoice_extract.FieldsTests', function (require) {
"use strict";

var InvoiceExtractFields = require('account_invoice_extract.Fields');

var testUtils = require('web.test_utils');

QUnit.module('account_invoice_extract', {}, function () {
QUnit.module('Fields', {}, function () {

    QUnit.test('render buttons', function (assert) {
        assert.expect(7);
        var parent = testUtils.createParent({});
        var fields = new InvoiceExtractFields(parent);

        fields.renderButtons({ $container: $('#qunit-fixture') });

        var $buttons = $('.o_invoice_extract_button');
        assert.strictEqual($buttons.length, 6,
            "should display 6 field buttons");
        // check each button label
        assert.strictEqual($buttons.eq(0).text().trim(),
            'VAT',
            "1st button should have correct text");
        assert.strictEqual($buttons.eq(1).text().trim(),
            'Vendor',
            "2nd button should have correct text");
        assert.strictEqual($buttons.eq(2).text().trim(),
            'Currency',
            "3rd button should have correct text");
        assert.strictEqual($buttons.eq(3).text().trim(),
            'Date',
            "4th button should have correct text");
        assert.strictEqual($buttons.eq(4).text().trim(),
            'Due Date',
            "5th button should have correct text");
        assert.strictEqual($buttons.eq(5).text().trim(),
            'Vendor Reference',
            "6th button should have correct text");

        parent.destroy();
    });

    QUnit.test('get button', function (assert) {
        assert.expect(6);
        var parent = testUtils.createParent({});
        var fields = new InvoiceExtractFields(parent);

        fields.renderButtons({ $container: $('#qunit-fixture') });

        var $buttons = $('.o_invoice_extract_button');
        assert.hasClass($buttons.eq(0),'active', "1st button should be active by default");
        assert.doesNotHaveClass($buttons.eq(1), 'active', "2nd button should be inactive by default");
        assert.doesNotHaveClass($buttons.eq(2), 'active', "3rd button should be inactive by default");
        assert.doesNotHaveClass($buttons.eq(3), 'active', "4th button should be inactive by default");
        assert.doesNotHaveClass($buttons.eq(4), 'active', "5th button should be inactive by default");
        assert.doesNotHaveClass($buttons.eq(5), 'active', "6th button should be inactive by default");

        parent.destroy();
    });

    QUnit.test('get active field', function (assert) {
        assert.expect(1);
        var parent = testUtils.createParent({});
        var fields = new InvoiceExtractFields(parent);

        fields.renderButtons({ $container: $('#qunit-fixture') });

        var activeField = fields.getActiveField();
        assert.strictEqual(activeField.getName(), 'VAT_Number',
            "should have correct active field");

        parent.destroy();
    });

    QUnit.test('get field (provided name)', function (assert) {
        assert.expect(1);
        var parent = testUtils.createParent({});
        var fields = new InvoiceExtractFields(parent);

        fields.renderButtons({ $container: $('#qunit-fixture') });

        var field = fields.getField({ name: 'VAT_Number' });
        assert.strictEqual(field.getName(), 'VAT_Number',
            "should get the correct field");

        parent.destroy();
    });

    QUnit.test('get field (no provide name)', function (assert) {
        assert.expect(1);
        var parent = testUtils.createParent({});
        var fields = new InvoiceExtractFields(parent);

        fields.renderButtons({ $container: $('#qunit-fixture') });
        assert.strictEqual(fields.getField(), fields.getActiveField(),
            "should get the active field when no field name is provided");

        parent.destroy();
    });

    QUnit.test('click field button', function (assert) {
        assert.expect(10);
        var parent = testUtils.createParent({
            intercepts: {
                active_invoice_extract_field: function (ev) {
                    ev.stopPropagation();
                    assert.step('new active field: ' + ev.data.fieldName);
                },
            },
        });
        var fields = new InvoiceExtractFields(parent);

        fields.renderButtons({ $container: $('#qunit-fixture') });

        var vatField = fields.getField({ name: 'VAT_Number' });
        var invoiceIdField = fields.getField({ name: 'invoice_id' });
        var $vatButton = $('.o_invoice_extract_button[data-field-name="VAT_Number"]');
        var $InvoiceIdButton = $('.o_invoice_extract_button[data-field-name="invoice_id"]');
        // check fields
        assert.ok(vatField.isActive(),
            "VAT field should be active by default");
        assert.notOk(invoiceIdField.isActive(),
            "InvoiceId field should be inactive by default");
        // check buttons
        assert.hasClass($vatButton,'active',
            "field button 'VAT' should be active by default");
        assert.doesNotHaveClass($InvoiceIdButton, 'active',
            "field button 'invoice_id' should be inactive by default");

        testUtils.dom.click($InvoiceIdButton);
        assert.verifySteps(['new active field: invoice_id']);

        // check fields
        assert.notOk(vatField.isActive(),
            "VAT field should become inactive");
        assert.ok(invoiceIdField.isActive(),
            "InvoiceId field should become active");
        // check buttons
        assert.doesNotHaveClass($vatButton, 'active',
            "field button 'VAT' should become inactive");
        assert.hasClass($InvoiceIdButton,'active',
            "field button 'invoice_id' should become active");

        parent.destroy();
    });

    QUnit.test('reset active', function (assert) {
        assert.expect(6);
        var parent = testUtils.createParent({
            intercepts: {
                active_invoice_extract_field: function (ev) {
                    ev.stopPropagation();
                },
            },
        });
        var fields = new InvoiceExtractFields(parent);

        fields.renderButtons({ $container: $('#qunit-fixture') });

        var $vatButton = $('.o_invoice_extract_button[data-field-name="VAT_Number"]');
        var $invoiceIdButton = $('.o_invoice_extract_button[data-field-name="invoice_id"]');

        assert.hasClass($vatButton,'active',
            "field button 'VAT' should be active by default");
        assert.doesNotHaveClass($invoiceIdButton, 'active',
            "field button 'invoice_id' should be inactive by default");

        testUtils.dom.click($invoiceIdButton);
        assert.doesNotHaveClass($vatButton, 'active',
            "field button 'VAT' should become inactive");
        assert.hasClass($invoiceIdButton,'active',
            "field button 'invoice_id' should become active");

        fields.resetActive();
        assert.hasClass($vatButton,'active',
            "field button 'VAT' should become active after resetting active field");
        assert.doesNotHaveClass($invoiceIdButton, 'active',
            "field button 'invoice_id' should become inactive after resetting active field");

        parent.destroy();
    });

});
});
});
