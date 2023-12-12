from odoo import fields,api,models
from odoo.addons.website.tools import text_from_html
from odoo.tools.translate import html_translate
import re
class BlogPost(models.Model):
    _inherit = 'blog.post'

    def _default_content(self):
        # res = super(BlogPost,self)._default_content()
        print('hellooo')
        return '''
            
        '''
    def _default_content_summary(self):
        return'''
        Some of our customers are transitioning to paper bags regardless due to public opinion. This is a business choice; they are concerned that their customers will believe they are breaking the law or they are choosing what is perceived to be more environmentally friendly solution . However, it is not mandatory if your business falls into one of the above categories.
        '''
    def _default_content_summary1(self):
        return'''
        A large portion of our customers are exempt from the ban and may continue to use plastic bags if they so choose.
        '''

    def _default_content_subtitle2(self):
        return'''
        Executive Summary :
        '''

    def _default_content_test(self):
        return'''
          <img class="img-fluid" width="642" height="773" src="/theme_pricepaper/static/src/img/paper-bags.webp" alt=""/>
        '''
    content = fields.Html('Content', default=_default_content, translate=html_translate, sanitize=False)
    summary = fields.Html('Summary', default=_default_content_summary, translate=html_translate, sanitize=False)
    summary1 = fields.Html('Summary', default=_default_content_summary1, translate=html_translate, sanitize=False)
    subtitle2 = fields.Html('subtitle2', default=_default_content_subtitle2, translate=html_translate, sanitize=False)
    img_cover = fields.Html('subtitle2', default=_default_content_test, translate=html_translate, sanitize=False)
    @api.depends('content', 'teaser_manual')
    def _compute_teaser(self):
        for blog_post in self:
            if blog_post.teaser_manual:
                blog_post.teaser = blog_post.teaser_manual
            else:
                content = text_from_html(blog_post.content)
                content = re.sub('\\s+', ' ', content).strip()
                blog_post.teaser = content[:100] + '...'