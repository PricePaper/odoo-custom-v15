# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf

from .ups_request import UPSRequest, Package



class ProviderUPS(models.Model):
    _inherit = 'delivery.carrier'

    def ups_rate_shipment(self, order):
        superself = self.sudo()
        srm = UPSRequest(self.log_xml, superself.ups_username, superself.ups_passwd, superself.ups_shipper_number, superself.ups_access_number, self.prod_environment)
        ResCurrency = self.env['res.currency']
        max_weight = self.ups_default_package_type_id.max_weight
        packages = []
        total_qty = 0
        total_weight = order._get_estimated_weight()
        for line in order.order_line.filtered(lambda line: not line.is_delivery and not line.display_type):
            total_qty += line.product_uom_qty

        if max_weight and total_weight > max_weight:
            total_package = int(total_weight / max_weight)
            last_package_weight = total_weight % max_weight

            for seq in range(total_package):
                packages.append(Package(self, max_weight))
            if last_package_weight:
                packages.append(Package(self, last_package_weight))
        else:
            packages.append(Package(self, total_weight))

        shipment_info = {
            'total_qty': total_qty  # required when service type = 'UPS Worldwide Express Freight'
        }

        if self.ups_cod:
            cod_info = {
                'currency': order.partner_id.country_id.currency_id.name,
                'monetary_value': order.amount_total,
                'funds_code': self.ups_cod_funds_code,
            }
        else:
            cod_info = None

        for pack in packages:
            pack.dimension['length'] = 0
            pack.dimension['height'] = 0
            pack.dimension['width'] = 0
            pack.dimension['volume'] = order.total_volume * 1728

        check_value = srm.check_required_value(order.company_id.partner_id, order.warehouse_id.partner_id, order.partner_shipping_id, order=order)
        if check_value:
            return {'success': False,
                    'price': 0.0,
                    'error_message': check_value,
                    'warning_message': False}

        ups_service_type = self.ups_default_service_type
        result = srm.get_shipping_price(
            shipment_info=shipment_info, packages=packages, shipper=order.company_id.partner_id, ship_from=order.warehouse_id.partner_id,
            ship_to=order.partner_shipping_id, packaging_type=self.ups_default_package_type_id.shipper_package_code, service_type=ups_service_type,
            saturday_delivery=self.ups_saturday_delivery, cod_info=cod_info)

        if result.get('error_message'):
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error:\n%s', result['error_message']),
                    'warning_message': False}

        if order.currency_id.name == result['currency_code']:
            price = float(result['price'])
        else:
            quote_currency = ResCurrency.search([('name', '=', result['currency_code'])], limit=1)
            price = quote_currency._convert(
                float(result['price']), order.currency_id, order.company_id, order.date_order or fields.Date.today())

        if self.ups_bill_my_account and order.partner_ups_carrier_account:
            # Don't show delivery amount, if ups bill my account option is true
            price = 0.0

        return {'success': True,
                'price': price,
                'error_message': False,
                'warning_message': False}
    def ups_send_shipping(self, pickings):
        res = []
        superself = self.sudo()
        srm = UPSRequest(self.log_xml, superself.ups_username, superself.ups_passwd, superself.ups_shipper_number, superself.ups_access_number, self.prod_environment)
        ResCurrency = self.env['res.currency']
        for picking in pickings:
            packages = []
            package_names = []
            if picking.package_ids:
                # Create all packages
                for package in picking.package_ids:
                    packages.append(Package(self, package.shipping_weight, quant_pack=package.package_type_id, name=package.name))
                    package_names.append(package.name)
            # Create one package with the rest (the content that is not in a package)
            if picking.weight_bulk:
                packages.append(Package(self, picking.weight_bulk))
                for pack in packages:
                    pack.dimension['length'] = 0
                    pack.dimension['height'] = 0
                    pack.dimension['width'] = 0
                    pack.dimension['volume'] = picking.sale_id.total_volume * 1728

            shipment_info = {
                'description': picking.origin,
                'total_qty': sum(sml.qty_done for sml in picking.move_line_ids),
                'ilt_monetary_value': '%d' % sum(sml.sale_price for sml in picking.move_line_ids),
                'itl_currency_code': self.env.company.currency_id.name,
                'phone': picking.partner_id.mobile or picking.partner_id.phone or picking.sale_id.partner_id.mobile or picking.sale_id.partner_id.phone,
            }
            if picking.sale_id and picking.sale_id.carrier_id != picking.carrier_id:
                ups_service_type = picking.carrier_id.ups_default_service_type or self.ups_default_service_type
            else:
                ups_service_type = self.ups_default_service_type
            ups_carrier_account = False
            if self.ups_bill_my_account:
                ups_carrier_account = picking.partner_id.with_company(picking.company_id).property_ups_carrier_account

            if picking.carrier_id.ups_cod:
                cod_info = {
                    'currency': picking.partner_id.country_id.currency_id.name,
                    'monetary_value': picking.sale_id.amount_total,
                    'funds_code': self.ups_cod_funds_code,
                }
            else:
                cod_info = None

            check_value = srm.check_required_value(picking.company_id.partner_id, picking.picking_type_id.warehouse_id.partner_id, picking.partner_id, picking=picking)
            if check_value:
                raise UserError(check_value)

            package_type = picking.package_ids and picking.package_ids[0].package_type_id.shipper_package_code or self.ups_default_package_type_id.shipper_package_code
            srm.send_shipping(
                shipment_info=shipment_info, packages=packages, shipper=picking.company_id.partner_id, ship_from=picking.picking_type_id.warehouse_id.partner_id,
                ship_to=picking.partner_id, packaging_type=package_type, service_type=ups_service_type, duty_payment=picking.carrier_id.ups_duty_payment,
                label_file_type=self.ups_label_file_type, ups_carrier_account=ups_carrier_account, saturday_delivery=picking.carrier_id.ups_saturday_delivery,
                cod_info=cod_info)
            result = srm.process_shipment()
            if result.get('error_message'):
                raise UserError(result['error_message'].__str__())

            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.company
            currency_order = picking.sale_id.currency_id
            if not currency_order:
                currency_order = picking.company_id.currency_id

            if currency_order.name == result['currency_code']:
                price = float(result['price'])
            else:
                quote_currency = ResCurrency.search([('name', '=', result['currency_code'])], limit=1)
                price = quote_currency._convert(
                    float(result['price']), currency_order, company, order.date_order or fields.Date.today())

            package_labels = []
            for track_number, label_binary_data in result.get('label_binary_data').items():
                package_labels = package_labels + [(track_number, label_binary_data)]

            carrier_tracking_ref = "+".join([pl[0] for pl in package_labels])
            logmessage = _("Shipment created into UPS<br/>"
                           "<b>Tracking Numbers:</b> %s<br/>"
                           "<b>Packages:</b> %s") % (carrier_tracking_ref, ','.join(package_names))
            if self.ups_label_file_type != 'GIF':
                attachments = [('LabelUPS-%s.%s' % (pl[0], self.ups_label_file_type), pl[1]) for pl in package_labels]
            if self.ups_label_file_type == 'GIF':
                attachments = [('LabelUPS.pdf', pdf.merge_pdf([pl[1] for pl in package_labels]))]
            if picking.sale_id:
                for pick in picking.sale_id.picking_ids:
                    pick.message_post(body=logmessage, attachments=attachments)
            else:
                picking.message_post(body=logmessage, attachments=attachments)
            shipping_data = {
                'exact_price': price,
                'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
            if self.return_label_on_delivery:
                self.ups_get_return_label(picking)
        return res

    def ups_get_return_label(self, picking, tracking_number=None, origin_date=None):
        res = []
        superself = self.sudo()
        srm = UPSRequest(self.log_xml, superself.ups_username, superself.ups_passwd, superself.ups_shipper_number, superself.ups_access_number, self.prod_environment)
        ResCurrency = self.env['res.currency']
        packages = []
        package_names = []
        if picking.is_return_picking:
            weight = picking._get_estimated_weight()
            packages.append(Package(self, weight))
        else:
            if picking.package_ids:
                # Create all packages
                for package in picking.package_ids:
                    packages.append(Package(self, package.shipping_weight, quant_pack=package.package_type_id, name=package.name))
                    package_names.append(package.name)
            # Create one package with the rest (the content that is not in a package)
            if picking.weight_bulk:
                packages.append(Package(self, picking.weight_bulk))
                for pack in packages:
                    pack.dimension['length'] = 0
                    pack.dimension['height'] = 0
                    pack.dimension['width'] = 0
                    pack.dimension['volume'] = picking.sale_id.total_volume * 1728


        invoice_line_total = 0
        for move in picking.move_lines:
            invoice_line_total += picking.company_id.currency_id.round(move.product_id.lst_price * move.product_qty)

        shipment_info = {
            'description': picking.origin,
            'total_qty': sum(sml.qty_done for sml in picking.move_line_ids),
            'ilt_monetary_value': '%d' % invoice_line_total,
            'itl_currency_code': self.env.company.currency_id.name,
            'phone': picking.partner_id.mobile or picking.partner_id.phone or picking.sale_id.partner_id.mobile or picking.sale_id.partner_id.phone,
        }
        if picking.sale_id and picking.sale_id.carrier_id != picking.carrier_id:
            ups_service_type = picking.carrier_id.ups_default_service_type or self.ups_default_service_type
        else:
            ups_service_type = self.ups_default_service_type
        ups_carrier_account = False
        if self.ups_bill_my_account:
            ups_carrier_account = picking.partner_id.with_company(picking.company_id).property_ups_carrier_account

        if picking.carrier_id.ups_cod:
            cod_info = {
                'currency': picking.partner_id.country_id.currency_id.name,
                'monetary_value': picking.sale_id.amount_total,
                'funds_code': self.ups_cod_funds_code,
            }
        else:
            cod_info = None

        check_value = srm.check_required_value(picking.partner_id, picking.partner_id, picking.picking_type_id.warehouse_id.partner_id)
        if check_value:
            raise UserError(check_value)

        package_type = picking.package_ids and picking.package_ids[0].package_type_id.shipper_package_code or self.ups_default_package_type_id.shipper_package_code
        srm.send_shipping(
            shipment_info=shipment_info, packages=packages, shipper=picking.partner_id, ship_from=picking.partner_id,
            ship_to=picking.picking_type_id.warehouse_id.partner_id, packaging_type=package_type, service_type=ups_service_type, duty_payment='RECIPIENT', label_file_type=self.ups_label_file_type, ups_carrier_account=ups_carrier_account,
            saturday_delivery=picking.carrier_id.ups_saturday_delivery, cod_info=cod_info)
        srm.return_label()
        result = srm.process_shipment()
        if result.get('error_message'):
            raise UserError(result['error_message'].__str__())

        order = picking.sale_id
        company = order.company_id or picking.company_id or self.env.company
        currency_order = picking.sale_id.currency_id
        if not currency_order:
            currency_order = picking.company_id.currency_id

        if currency_order.name == result['currency_code']:
            price = float(result['price'])
        else:
            quote_currency = ResCurrency.search([('name', '=', result['currency_code'])], limit=1)
            price = quote_currency._convert(
                float(result['price']), currency_order, company, order.date_order or fields.Date.today())

        package_labels = []
        for track_number, label_binary_data in result.get('label_binary_data').items():
            package_labels = package_labels + [(track_number, label_binary_data)]

        carrier_tracking_ref = "+".join([pl[0] for pl in package_labels])
        logmessage = _("Return label generated<br/>"
                       "<b>Tracking Numbers:</b> %s<br/>"
                       "<b>Packages:</b> %s") % (carrier_tracking_ref, ','.join(package_names))
        if self.ups_label_file_type != 'GIF':
            attachments = [('%s-%s-%s.%s' % (self.get_return_label_prefix(), pl[0], index, self.ups_label_file_type), pl[1]) for index, pl in enumerate(package_labels)]
        if self.ups_label_file_type == 'GIF':
            attachments = [('%s-%s-%s.%s' % (self.get_return_label_prefix(), package_labels[0][0], 1, 'pdf'), pdf.merge_pdf([pl[1] for pl in package_labels]))]
        picking.message_post(body=logmessage, attachments=attachments)
        shipping_data = {
            'exact_price': price,
            'tracking_number': carrier_tracking_ref}
        res = res + [shipping_data]
        return res
