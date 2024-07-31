from odoo import api, fields, models, _
from odoo.exceptions import UserError

class RejectReason(models.TransientModel):

	_name="reject.reason"
	_description="Wizard for getting reason for rejecting the request"

	message = fields.Text(string="Reject Reason",required=True)


	
	def reject_request(self):
		request_id = self.env['sample.request'].browse([self._context.get('active_id')])
		request_id.message_post(body=f'Reason for rejection: {self.message}')
		request_id.state = 'reject'
		template_id = self.env.ref('sample_request.email_template_edi_sample_requst',raise_if_not_found=False)
		if template_id:
			template_id.with_context(reason=self.message).send_mail(request_id.id,force_send=False,raise_exception=False)
		return {'type': 'ir.actions.act_window_close'}