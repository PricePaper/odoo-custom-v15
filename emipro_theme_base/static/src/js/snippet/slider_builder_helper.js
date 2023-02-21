odoo.define('slider.builder.helper', function (require) {
'use strict';
var Wysiwyg = require('web_editor.wysiwyg');
var rpc = require('web.rpc');

     Wysiwyg.include({

            start: function () {
                $(document).on('change', '#snippets_list_allproduct .form-control, #snippets_list_product .form-control,#snippets_list_category .form-control,#snippets_list_best_seller .form-control,#snippets_list_new_product .form-control,#snippets_list_category_products .form-control',function(){
                    $(this).parents("form").find(".te_style_image_block").attr("class","te_style_image_block style-"+this.value);
                });
                $('.common_carousel_emp_ept').carousel();
                $('.common_carousel_emp_ept').carousel({
                  interval: 3000
                });
                $('.common_carousel_emp_ept .carousel-item').each(function(){
                    $(this).children().not(':first').remove();

                    for (var i=0;i<2;i++) {
                        $(this).children().not(':first').remove();
                    }
                });

                $("#top_menu > .dropdown").each(function() {
                    $(this).hover(function() {
                        $(this).removeClass('open');
                    });
                });

                if($('#id_lazyload').length) {
                    $('img.lazyload').each(function(){
                        var getDataSrcVal = $(this).attr('data-src');
                        if(getDataSrcVal == undefined || getDataSrcVal != ''){
                            $(this).attr('src', getDataSrcVal);
                            $(this).attr('data-src', '');
                        }
                    });
                }

                return this._super.apply(this, arguments);
            },
        /**
         * @override
         */
            _saveElement: async function ($el, context, withLang) {
                var promises = [];

                var oldHtml = $el;
                oldHtml.find("[data-isemipro='true'],.te_brand_slider,.te_category_slider").empty();
                /* Apply Lazyload for all snippet images*/
                if($('#id_lazyload').length) {
                    if(oldHtml){
                        $.each(oldHtml.find('img.lazyload'), function(index, value){
                            var getDataSrcVal = $(value).attr('data-src');
                            var getSrcVal = $(value).attr('src');
                            var getClass = $(value).attr('class');
                            var getWeb = $('.current_website_id').val();
                            if(getDataSrcVal == undefined || getDataSrcVal != ''){
                                $(value).attr('src', '/web/image/website/'+ getWeb +'/lazy_load_image');
                                $(value).attr('data-src', getSrcVal);
                            }
                        });
                    }
                }
                var updateHtml = oldHtml[0].outerHTML;
                // Saving a view content
                await this._super.apply(this, arguments);
            }
        });
});
