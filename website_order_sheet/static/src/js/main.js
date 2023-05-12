odoo.define('website_order_sheet.order_sheet', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var ajax = require('web.ajax')
    // var window.localStorage = require('web.local_storage');
    var _t = core._t;


    publicWidget.registry.AddProduct = publicWidget.Widget.extend({
        selector: '#addProduct',
        events: {

            // 'click .next_set,.prev_set': '_getSet',
            'click .add_prod': '_addProd',

        },
        _addProd: function (ev) {
            var section_key = window.localStorage.getItem("sectionKey");
            var selec_prod = []
            $('.selected_section_product .card').each(function () {
                selec_prod.push($(this).attr('product_id'))
            }).promise().done(function () {
                ajax.jsonRpc('/add/section/product', 'call', { 'section_key': section_key, 'prod_ids': selec_prod }).then(function (data) {
                    window.location.reload()
                    // $target.parents('.o_wsale_product_grid_wrapper').find('.oe_product_image img').attr('src', data);
                });
                
            })
        
        }
    })


    publicWidget.registry.BrowseHistory = publicWidget.Widget.extend({
        selector: '#browseHistory',
        events: {

            'click .next_set,.prev_set': '_getSet',
            'click .add_prod': '_addProd',

        },
        setprod: function () {
            var offset = $(this.$target).find('.next_set').attr('data-offset')
            offset = parseInt(offset, 10) - 1
            var section_key = window.localStorage.getItem("sectionKey");
            var key = 'section-' + section_key + '-' + offset
            var selec_prod = []
            $('input.prod_selec:checked').each(function () {
                selec_prod.push($(this).attr('data-id'))
            }).promise().done(function () {
                window.localStorage.setItem(key, JSON.stringify(selec_prod));
            })
        },
        getprod: function (offset = false, all = false) {
            // console.log(all)
            var section_key = window.localStorage.getItem("sectionKey");
            if (!offset) {

            }
            if (all) {
                // console.log("section_key", window.localStorage)
                var key = 'section-' + section_key + '-'
                var arr = []; // Array to hold the keys
                // Iterate over window.localStorage and insert the keys that meet the condition into arr
                for (var i = 0; i < window.localStorage.length; i++) {
                    // console.log('hh')
                    // console.log(window.localStorage.key(i))
                    if (window.localStorage.key(i).startsWith(key)) {
                        arr.push(window.localStorage.key(i));
                    }
                }
                var main_ids = []
                // Iterate over arr and remove the items by key
                for (var i = 0; i < arr.length; i++) {
                    var arr_2 = JSON.parse(window.localStorage.getItem(arr[i]))
                    console.log("ma", arr_2)
                    Array.prototype.push.apply(main_ids, arr_2)
                    // console.log('rrrrr',arr)
                    // window.localStorage.removeItem(arr[i]);
                }

                return main_ids


            }
            else {


                var key = 'section-' + section_key + '-' + offset
                return JSON.parse(window.localStorage.getItem(key))
            }


        },
        _addProd: function (ev) {
            var section_key = window.localStorage.getItem("sectionKey");
            var prod_ids = this.getprod(false, true)
            this._rpc({
                route: '/sheet/add/prod',
                params: {
                    section_key: section_key,
                    prod_ids: prod_ids
                }
            }).then(function (res) {
                console.log($(document).find('li[data-id=' + section_key + ']'))
                $('#browseHistory').modal('hide')
                $(document).find('li[data-id=' + section_key + ']').after(res.prod_li)
            })
        },
        _getSet: function (ev) {
            this.setprod()
            var $self = this
            var offset = $(ev.currentTarget).attr('data-offset')

            this._rpc({
                route: '/sheet/browse/set',
                params: {
                    offset: offset,
                }
            }).then(function (res) {
                $(document).find('.main_history').replaceWith(res.history_table)

                var history = $self.getprod(offset)


                if (history) {

                    history.forEach(element => {
                        $('input.prod_selec[data-id=' + element + ']').prop('checked', true)

                    });
                }

            });

        }
    })
    publicWidget.registry.OrderSheet = publicWidget.Widget.extend({
        selector: '.order_sheet',
        events: {
            'click .section_edit': '_editSection',
            'click .input-group-prepend': '_minusQuantity',
            'click .input-group-append': '_addQuantity',
            'click .create_section': "_createSection",
            'click .save_data': "_saveSheet",
            'click .browse_product': "_browseProduct",
            'click .add_product': "_addProduct",


        },
        _saveSheet: function (ev) {
            var main_ul = $(document).find($('.main_ul>li'))
            var sheet_data = {}
            var new_data = []
            main_ul.each(function () {
                var sub_ul = $(this).find('.sub_ul>li:not(.main_element)')
                var main_element = $(this).find('.sub_ul>li.main_element')
                var product_ids = []
                sub_ul.each(function () {
                    var product_id = $(this).attr('data-id')
                    console.log(product_id)
                    product_ids.push(product_id)
                }).promise().done(function () {
                    var main_id = main_element.attr('data-id')

                    var section_name = main_element.find('.section_name').text()
                    if (main_id == 'new') {
                        new_data.push({ 'section': section_name, 'product_ids': product_ids })
                    }
                    else {
                        sheet_data[main_id] = { name: section_name, product_ids: product_ids }
                    }
                }).promise().done(function () {
                    ajax.jsonRpc('/save/sheet', 'call', { 'sheet_data': sheet_data, 'new_data': new_data }).then(function (data) {
                        window.location.reload()
                        // $target.parents('.o_wsale_product_grid_wrapper').find('.oe_product_image img').attr('src', data);
                    });
                })

            })
        },
        _createSection: function (ev) {
            Swal.fire({
                title: "Add Section",
                text: "Enter the section name:",
                input: 'text',
                inputAttributes: {
                    placeholder: "Name",
                    // pattern: '[0-9]{3}-[0-9]{3}-[0-9]{4}',
                    required: true
                },
                showCancelButton: true
            }).then((result) => {
                if (result.value) {
                    ajax.jsonRpc('/create/section', 'call', { 'section_name': result.value }).then(function (data) {
                        $(".main_ul").append(data.section_li);
                        initsortable()
                        // $target.parents('.o_wsale_product_grid_wrapper').find('.oe_product_image img').attr('src', data);
                    });

                    initsortable()
                }
            });

        },
        _addQuantity: function (ev) {
            var quantiy_input = $(ev.currentTarget).parents('.css_quantity').find('.quantity')
            var current = quantiy_input.val()
            quantiy_input.val(parseInt(current) + 1)

        },
        _minusQuantity: function (ev) {
            var quantiy_input = $(ev.currentTarget).parents('.css_quantity').find('.quantity')
            var current = quantiy_input.val()
            if (parseInt(current) > 0) {
                quantiy_input.val(parseInt(current) - 1)
            }

        },
        _editSection: function (ev) {
            var old_name = $(ev.currentTarget).siblings('.section_name')
            Swal.fire({
                title: "Update Section",
                text: "Enter the new name:",
                input: 'text',
                inputAttributes: {
                    placeholder: old_name.text(),
                    // pattern: '[0-9]{3}-[0-9]{3}-[0-9]{4}',
                    required: true
                },
                showCancelButton: true
            }).then((result) => {
                if (result.value) {
                    old_name.text(result.value)
                    console.log("Result: " + result.value);
                }
            });
        },
        _browseProduct: function (ev) {
            var section_line = $(ev.currentTarget).attr('data-line')
            window.localStorage.setItem("sectionKey", section_line);
        },
        _addProduct: function (ev) {
            var section_line = $(ev.currentTarget).attr('data-line')
            window.localStorage.setItem("sectionKey", section_line);
        },
    })

    function initsortable() {
        $('.main_ul').sortable({
            placeholder: 'ui-state-highlight',

        })
        $('.sub_ul').sortable({
            items: 'li:not(li.main_element)',
            connectWith: '.sub_ul',
            placeholder: 'ui-state-highlight',

        })
    }

    $(document).ready(function (ev) {
        $('.main_ul').sortable({
            placeholder: 'ui-state-highlight',

        })
        $('.sub_ul').sortable({
            items: 'li:not(li.main_element)',
            connectWith: '.sub_ul',
            placeholder: 'ui-state-highlight',

        })



    })

})