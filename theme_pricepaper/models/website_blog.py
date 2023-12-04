from odoo import fields,api,models
from odoo.addons.website.tools import text_from_html
import re
class BlogPost(models.Model):
    _inherit = 'blog.post'

    def _default_content(self):
        import pdb 
        pdb.set_trace()
        return '''
            
        '''
    @api.depends('content', 'teaser_manual')
    def _compute_teaser(self):
        for blog_post in self:
            if blog_post.teaser_manual:
                blog_post.teaser = blog_post.teaser_manual
            else:
                content = text_from_html(blog_post.content)
                content = re.sub('\\s+', ' ', content).strip()
                blog_post.teaser = content[:100] + '...'
