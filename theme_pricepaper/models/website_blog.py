from odoo import fields,api,models

class BlogPost(models.Model):
    _inherit = 'blog.post'

    def _default_content(self):
        import pdb 
        pdb.set_trace()
        return '''
            
        '''