//--------------------------------------------------------------------------
// Add value of hotspots in full width image snippet
//--------------------------------------------------------------------------
odoo.define('theme_clarico_vega.image_hotspot_snippet_backend',function(require) {
'use strict';
    const options = require('web_editor.snippets.options');
    var ajax = require('web.ajax');
    const publicWidget = require('web.public.widget');
    const weSnippetEditor = require('web_editor.snippet.editor');
    var {ColorpickerDialog} = require('web.Colorpicker');

    options.registry.image_hotspot_inner_div = options.Class.extend({

        onFocus : function () {
            var res = this._super.apply(this, arguments);
            if($(this.el).parent().find('.snippet-option-image_hotspot_inner_div').length && this.$target.hasClass('hotspot_element')) {
                $(this.el).parent().find('we-title:first>span').html('Hotspot Block')
                $(this.el).parent().find('.oe_snippet_clone').addClass('hidden_option')
                $(this.el).parent().find('we-customizeblock-option:not(".snippet-option-image_hotspot_inner_div")').addClass('hidden_option')
            }
        },

        edit_hotspot : function () {
            var self = this;
            if(this.$target.hasClass('hotspot_element')){
                var parentSnippet = this.$target.parent().find('img').parent()
            } else {
                var parentSnippet = this.$target.parent()
            }
            this.$target.trigger('click',{'parentSnippet': parentSnippet});
        },

        onBuilt: function () {
            this._super();
            if(this.$target.closest('.product_banner_list').length > 0) {
                return
            }
            this.edit_hotspot()
        },
    })

    // Override snippet remove event in order to remove hotspot while removing the image with Hotspot on it
    weSnippetEditor.SnippetEditor.include({
        _onRemoveClick: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            if(this.$target.hasClass('image_hotspot_drop')) {
                this.$target.parent().find('.hotspot_element').remove()
            }
            this.trigger_up('request_history_undo_record', {$target: this.$target});
            this.removeSnippet();
        },
    });

    publicWidget.registry.popupEditorEpt = publicWidget.Widget.extend({
        selector: "#wrapwrap",
        disabledInEditableMode: false,
        edit_events: {
            'click .hotspot_element, img.o_we_selected_image, .image_hotspot_drop' : 'showHotspotPopup', // Show The Hotspot Configuration Popup
            'click #hotspotShape a' : '_selectHotspotShape',
            'click #hotspotAnimation a' : '_selectHotspotAnimation',
            'click #hotspot_action a' : '_selectHotspotAction',
            'click .btn-hotspot-save' : '_saveHotspot',
            'keyup .hotspot_product' : '_onKeyupInput',
            'click #colorPicker': 'getcolrPicker',
            'click .hotspot_configure_section .card-header': 'collapseConfiguration',
        },

        getcolrPicker: function(e) {
            var self = this
            const colorpicker = new ColorpickerDialog(this, {
                defaultColor: self.color,
            });
            colorpicker.on('colorpicker:saved', this, (ev) => {
                $('#colorPicker').css('background-color',ev.data.cssColor)
                self.color = ev.data.cssColor
                if(this.animation != 'none') {
                    this.element_selector.find('svg').children()[1].setAttribute('stroke',self.color)
                }
                this.element_selector.find('svg').children()[0].setAttribute('fill',self.color)
            });
            colorpicker.open();
        },

        showHotspotPopup: function(e, parentSnippet) {
            var self = this;
            if(!parentSnippet) {
                return
            }
            $('#oe_snippets').append('<div class="o_we_ui_loading d-flex justify-content-center align-items-center"><i class="fa fa-circle-o-notch fa-spin fa-4x"></i></div>')
            self.hotspot = e.currentTarget.hasAttribute('id') ? e.currentTarget.cloneNode(true) : ''

            /* Hotspot element values */
            self.element_id = self.hotspot ? self.hotspot.id : 'imageHotspot' + Date.now(); //Set/get id of hotspot Element
            self.color = !self.hotspot ? '#2b68ff' : $(self.hotspot).data('color') //Set color of hotspot Element
            self.shape = !self.hotspot ? 'circle' : $(self.hotspot).data('shape') //Set shape of hotspot Element
            self.animation  = !self.hotspot ? 'none' : $(self.hotspot).data('animation') //Set animation of hotspot Element
            self.event = 'click'

            /* Hotspot parent container */
            self.parentImageSnippet = parentSnippet.parentSnippet

            $('.cus_theme_loader_layout').removeClass('d-none') // Add loader
            $("#hotspot_configure_model_main").empty()

            ajax.jsonRpc('/get-image-hotspot-template', 'call').then(function(data) {
                $("#hotspot_configure_model_main").html(data) // add model popup data
                $('.cus_theme_loader_layout').addClass('d-none') // Remove loader
                $('#colorPicker').css('background-color',self.color)
                //Set values in Hotspot Configuration pop up.
                if(self.hotspot) {
                    $('.preview-image-section').append(self.hotspot)
                    self.element_selector = $('.hotspot_preview_section #'+self.element_id)
                    // Set Hotspot Mouse event to toggle button
                    if($(self.hotspot).data('event') == 'mouseenter'){
                        $('.hotspot_configure_section .product_hotspot_event').prop("checked", true);
                        self.event = 'mouseenter'
                    }
                    // Set Hotspot action to drop-down
                    $('#hotspot_action a').each((i,j) => {
                        if($(j).data('action') == $(self.hotspot).data('action')){
                            j.click()
                        }
                    })

                    // Set Page Url to Page Url input
                    $('.hotspot_configure_section .hotspot_page_url').val($(self.hotspot).data('url'))

                    // Set Product values to product input
                    $('.hotspot_configure_section .hotspot_product').val($(self.hotspot).data('product_name')).attr({'data-product_id':$(self.hotspot).data('product_id'), 'data-product_name':$(self.hotspot).data('product_name')})

                    // Set Hotspot Shape to drop-down
                    $('#hotspotShape a').each((i,j) => {
                        if($(j).attr('id') == $(self.hotspot).data('shape')){
                            j.click()
                        }
                    })

                    // Set Hotspot animation to drop-down
                    $('#hotspotAnimation a').each((i,j) => {
                        if($(j).attr('id') == $(self.hotspot).data('animation')){
                            j.click()
                        }
                    })
                    // Convert selected hotspot image or new image to SVG
                    self.convertImgtoSvg(self.element_selector)
                } else {
                      $('.preview-image-section').append('<section contenteditable="false" name="Hotspot-Block" data-exclude=".s_col_no_resize, .s_col_no_bgcolor" id='+self.element_id+' data-color="" data-url="" data-event="" data-animation="" data-shape="" data-product_name="" data-url="" data-action="" data-product_id="" style="top:50%;left:50%;" class="hotspot_element o_not_editable s_col_no_resize s_col_no_bgcolor"><svg height="25" width="25" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="50" fill="#2b68ff"></circle></svg></section>')
                      self.element_selector = $('.hotspot_preview_section #'+self.element_id)
                }

                // Show Hotspot configuration pop up with all Hot Spot values in it
                $('#image_hotspot_configure_model').modal({backdrop: "static"});
                $('.hotspot_configure_section').click(()=>{
                    if($("#js_item").length) {
                        $("#js_item").empty().removeClass('show')
                    }
                })

                $('#image_hotspot_configure_model').on('shown.bs.modal', function (ev) {
                    $('.image_hotspot_configure_model .hotspot-configure').click()
                    $('#oe_manipulators .oe_overlay.oe_active').hide()
                })
                $('#image_hotspot_configure_model').on('hidden.bs.modal', function (e) {
                    $('#oe_snippets .o_we_ui_loading').remove()
                    $('body').removeClass('modal-open')
                })
                $('.ui-configuration input[type="checkbox"]').on('click', function(ev) {
                    ev.stopImmediatePropagation();
                    var checked = (ev.currentTarget.checked) ? false : true;
                    ev.currentTarget.checked=(checked) ? false : checked.toString();
                    self.event = ev.currentTarget.checked ? 'mouseenter' : 'click'
                });
            })
        },
        _onKeyupInput: _.debounce( function(ev) {
            var val = $(ev.currentTarget).val().trim()
            if(!val.length){
                $("#js_item").empty().removeClass('show')
            }
            if(val.length && ev.keyCode  != 13) {
                this.appendData(val)
                var child_height = $('.product_slider_configure_template').height();
                var parent_height = $('.hotspot-configure').height() + 60;
                if(child_height > parent_height) {
                    $(this).parents('.product-box').addClass('custom-height')
                }
            }
        },200),
        appendData: function(key) {
            var self = this;
            ajax.jsonRpc('/get-suggested-products-for-hotspot', 'call',{'key':key}).then(function(data) {
                $('#image_hotspot_configure_model').find("#js_item").empty().removeClass('show').addClass('dropdown-menu show').html(data)
                // Set the product to Input
                $(".input-item-link").on('click',async function (ev) {
                    $('.hotspot_product').val($(this).data('item_name')).attr({'data-product_id':$(this).data('item_id'), 'data-product_name':$(this).data('item_name')})
                    $("#js_item").empty().removeClass('show')
                });
                self.$menu = $('#js_item.dropdown-menu')
                $('#collapseOne').animate({
                    scrollTop: $(".product-box").offset().top - $(".product-box").parent().offset().top
                }, 500);
            })
        },
        _selectHotspotAction: function (ev) {
            var self = this
            $(ev.currentTarget).parentsUntil( ".slider-dropdown" ).find("a").removeClass('active');
            $(ev.currentTarget).addClass('active');
            $(ev.currentTarget).parentsUntil( ".dropdown_div" ).find('.slider-dropdown-button').text($(ev.currentTarget).text());
            var data_action = $(ev.currentTarget).attr('data-action') || false
            $('#hotspot_action').attr('data-action', data_action)
            if($(ev.currentTarget).data('action') == 'redirect_url') {
                $('.hotspot_product').val('').removeAttr('data-product_id data-product_name');
                $('.hotspot_page_url').parents('.configure-sub').removeClass('d-none')
                $('.hotspot_product').parents('.configure-sub').addClass('d-none')
            } else {
                $('.hotspot_page_url').val('')
                $('.hotspot_page_url').parents('.configure-sub').addClass('d-none')
                $('.hotspot_product').parents('.configure-sub').removeClass('d-none')
            }
        },

        _selectHotspotShape: function (ev) {
            var self = this
            $(ev.currentTarget).parentsUntil( ".slider-dropdown" ).find("a").removeClass('active');
            $(ev.currentTarget).addClass('active');
            $(ev.currentTarget).parentsUntil( ".dropdown_div" ).find('.slider-dropdown-button').text($(ev.currentTarget).text());
            if($(ev.currentTarget).attr('id') == "square") {
                if(self.animation == 'fade'){
                    self.set_fade_square(ev);
                } else if(self.animation == 'blink'){
                    self.set_blink_square(ev);
                } else {
                    self.element_selector.find('svg').html('<rect fill="'+self.color+'" height="100" width="100"></rect>')
                }
            } else {
                if(self.animation == 'fade'){
                    self.set_fade_circle(ev);
                } else if(self.animation == 'blink'){
                    self.set_blink_circle(ev);
                } else {
                    self.element_selector.find('svg').html('<circle cx="50" cy="50" r="50" fill="'+self.color+'"></circle>');
                }
            }
            self.shape = $(ev.currentTarget).attr('id')
        },

        _selectHotspotAnimation: function (ev) {
            var self = this
            $(ev.currentTarget).parentsUntil( ".slider-dropdown" ).find("a").removeClass('active');
            $(ev.currentTarget).addClass('active');
            $(ev.currentTarget).parentsUntil( ".dropdown_div" ).find('.slider-dropdown-button').text($(ev.currentTarget).text());
            if($(ev.currentTarget).attr('id') == "fade") {
                if(self.shape.includes('square')) {
                    self.set_fade_square(ev);
                } else {
                    self.set_fade_circle(ev);
                }
            } else if($(ev.currentTarget).attr('id') == "blink") {
                if(self.shape.includes('square')) {
                    self.set_blink_square(ev);
                } else {
                    self.set_blink_circle(ev);

                }
            } else {
                if(self.shape == 'square'){
                    self.element_selector.find('svg').html('<rect fill="'+self.color+'" height="100" width="100"></rect>');
                } else {
                    self.element_selector.find('svg').html('<circle cx="50" cy="50" r="50" fill="'+self.color+'"></circle>');
                }
            }
            self.animation = $(ev.currentTarget).attr('id')
        },

        set_fade_square: function(ev) {
            var self = this;
            self.element_selector.find('svg').html('<rect fill="'+self.color+'" height="50" width="50" x="25" y="25"></rect><rect fill="none" height="50" width="50" stroke="'+self.color+'" stroke-width="5" x="25" y="25"><animate attributeName="stroke-width" begin="0s" dur="1.8s" values="10; 50" calcMode="spline" keyTimes="0; 1" keySplines="0.165, 0.84, 0.44, 1" repeatCount="indefinite"></animate><animate attributeName="stroke-opacity" begin="0s" dur="1.8s" values="1; 0" calcMode="spline" keyTimes="0; 1" keySplines="0.3, 0.61, 0.355, 1" repeatCount="indefinite"></animate></rect>');
        },

        set_fade_circle: function(ev) {
            var self = this;
            self.element_selector.find('svg').html('<circle cx="50" cy="50" r="30" fill="'+self.color+'"></circle><circle cx="50" cy="50" r="30" fill="none" stroke="'+self.color+'" stroke-width="5"><animate attributeName="stroke-width" begin="0s" dur="1.8s" values="20; 45" calcMode="spline" keyTimes="0; 1" keySplines="0.165, 0.84, 0.44, 1" repeatCount="indefinite"></animate><animate attributeName="stroke-opacity" begin="0s" dur="1.8s" values="1; 0" calcMode="spline" keyTimes="0; 1" keySplines="0.3, 0.61, 0.355, 1" repeatCount="indefinite"></animate></circle>');
        },

        set_blink_square: function(ev) {
            var self = this;
            self.element_selector.find('svg').html('<rect fill="'+self.color+'" height="50" width="50" x="25" y="25"></rect><rect fill="none" height="100" width="100" stroke="'+self.color+'" stroke-width="30"><animate attributeName="stroke-opacity" begin="0s" dur="1.5s" values="1; 0" calcMode="spline" keyTimes="0; 1" repeatCount="indefinite" keySplines="0.3, 0.61, 0.355, 1"></animate></rect>');
        },

        set_blink_circle: function(ev) {
            var self = this;
            self.element_selector.find('svg').html('<circle cx="50" cy="50" r="20" fill="'+self.color+'"></circle><circle cx="50" cy="50" r="40" fill="none" stroke="'+self.color+'" stroke-width="20"><animate attributeName="stroke-opacity" begin="0s" dur="1.5s" values="1; 0" calcMode="spline" keyTimes="0; 1" keySplines="0.3, 0.61, 0.355, 1" repeatCount="indefinite"></animate></circle>')
        },

        _saveHotspot: function (str) {
            var self = this;
            self.convertSvgtoImg(self.element_selector)
            $.each( $(self.element_selector).data(), function (i) { $(self.element_selector).attr('data-'+i,'') });

            var page_url_input = $('.hotspot_configure_section .hotspot_page_url')
            var product_input = $('.hotspot_configure_section .hotspot_product')

            self.element_selector.attr('data-color',self.color) // Set color in attribute
            self.element_selector.attr('data-shape',self.shape) // Set shape in attribute
            self.element_selector.attr('data-animation',self.animation) // Set animation in attribute
            self.element_selector.attr('data-event',self.event) // Set mouse event in attribute
            self.element_selector.attr('data-action',$('#hotspot_action').data('action'))

            // Set page URL in attribute
            if(page_url_input.val().trim()) {
               var url_protocol = new RegExp(/^https?:\/\/|^\/\//i)
               self.page_url = url_protocol.test(page_url_input.val().trim()) ? page_url_input.val() : 'http://'+page_url_input.val()
               self.element_selector.attr({'data-url':self.page_url})
            }
            // Set product name/id in attribute
            if(product_input && product_input.val().trim()) {
               self.element_selector.attr({'data-product_name':$(product_input).data('product_name'),'data-product_id':parseInt($(product_input).data('product_id'))})
            }
            // Clone and set Hotspot on actual image
            var cloneHotspot = self.element_selector[0].cloneNode(true);

            if($(self.parentImageSnippet).find('#'+self.element_id).length) {
                $(self.parentImageSnippet).find('#'+self.element_id).replaceWith(cloneHotspot)
            } else {
                self.parentImageSnippet.append(cloneHotspot)
            }
            var updated_hotspot = $(self.parentImageSnippet).find('#'+self.element_id)
            updated_hotspot.draggable({
                containment: 'parent',
                opacity: 0.4,
                scroll: false,
                revertDuration: 200,
                refreshPositions: true,
                stop: function () {
                    var l = ( 100 * parseFloat($(this).position().left / parseFloat($(this).parent().width())) ) + "%" ;
                    var t = ( 100 * parseFloat($(this).position().top / parseFloat($(this).parent().height())) ) + "%" ;
                    $(this).css("left", l);
                    $(this).css("top", t);
                    $(this).find('img').click()
                }
            })
            $('#image_hotspot_configure_model').modal('hide');
            $('#image_hotspot_configure_model').remove()
            $('body').removeClass('modal-open')
            $('#oe_snippets .o_we_ui_loading').remove()
        },

        _isValidUrl: function (str) {
            var self = this;
            var regexp =  /^(?:(?:https?|ftp):\/\/)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})))(?::\d{2,5})?(?:\/\S*)?$/;
            var url_protocol = new RegExp(/^https?:\/\/|^\/\//i)
            if (!regexp.test(str)) {
                self.page_url = ''
                return false
            }
            self.page_url = url_protocol.test(str) ? str : 'http://'+str
            return self.page_url
        },

        // Convert the Image to SVG(html)
        convertImgtoSvg: function (e) {
            var img = e.children()[0]
            var imgURL = img.src;
            var self = this;
            fetch(imgURL).then(function(response) {
                return response.text();
            }).then(function(text){
                var parser = new DOMParser();
                var xmlDoc = parser.parseFromString(text, "text/xml");
                var svg = xmlDoc.getElementsByTagName('svg')[0]; // Get the SVG tag, ignore the rest
                if(svg) {
                    svg.removeAttribute('xmlns:a'); // Remove any invalid XML tags as per http://validator.w3.org
                } else {
                    alert('invalid Hotspot Image')
                    self._saveHotspot()
                    return;
                }
                // Check if the viewport is set, if the viewport is not set the SVG wont't scale.
                if(!svg.getAttribute('viewBox') && svg.getAttribute('height') && svg.getAttribute('width')) {
                    svg.setAttribute('viewBox', '0 0 ' + svg.getAttribute('height') + ' ' + svg.getAttribute('width'))
                }
                img.parentNode.replaceChild(svg, img); // Replace image with new SVG
            });
        },

        convertSvgtoImg: function (e) {
            var svg = e.children()[0];
            var xml = new XMLSerializer().serializeToString(svg);
            var svg64 = btoa(xml); //for utf8: btoa(unescape(encodeURIComponent(xml)))
            var b64start = 'data:image/svg+xml;base64,';
            var image64 = b64start + svg64;
            var base64img = document.createElement('img')
            base64img.src = image64
            base64img.className = "o_not_editable hotspotImage img img-fluid align-top"
            $(base64img).attr('contenteditable','false')
            svg.parentNode.replaceChild(base64img, svg); // Replace image with new SVG
        },

        collapseConfiguration: _.debounce(function(e) {
            var target = $(e.target).parents('.ui-configuration').find('.collapse')
            if(target.hasClass('show')){
                target.collapse('hide');
                $('.hotspot_configure_section .collapse:not('+target.attr('id')+')').collapse('show')
            } else {
                target.collapse('show');
                $('.hotspot_configure_section .collapse:not('+target.attr('id')+')').collapse('hide')
            }
            $('.hotspot_configure_section .card-header .fa').toggleClass('fa-plus fa-minus')
        },200),

    })
    return publicWidget.registry.popupEditorEpt;
});
