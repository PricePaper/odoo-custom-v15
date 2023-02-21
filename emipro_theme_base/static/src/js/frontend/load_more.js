odoo.define('emipro_theme_base.load_more', function(require) {
    'use strict';

    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    var sAnimations = require('website.content.snippets.animation');

    sAnimations.registry.loadMore = sAnimations.Animation.extend({
        selector: '#products_grid',
         effects: [{
            startEvents: 'scroll',
            update: 'startLoadMore',
        }],
        init: function () {
            this._super(...arguments);
            this.next_call = true;
            this.prev_call = true;
            // $('html').scrollTop(1);
        },

        start: function () {
            $('html').scrollTop(1);
            this._super(...arguments);
        },

        loadValues : function(){
            var page_url = $(".load_more_next_page").attr('next-page-url');
            var prev_page_url = $(".load_more_next_page").attr('prev-page-url');
            var first_page_url = $(".load_more_next_page").attr('first-page-url');
            var last_page_url = $(".load_more_next_page").attr('last-page-url');
            var current_url = $(".load_more_next_page").attr('current-page-url');
            var next_page_num = $(".load_more_next_page").attr('next-page-num');
            var prev_page_num = $(".load_more_next_page").attr('prev-page-num');
            var total_page = $(".load_more_next_page").attr('total-page');
            return {
                'page_url': page_url,'prev_page_url': prev_page_url,'first_page_url': first_page_url,'last_page_url': last_page_url,
                'current_url':current_url,'next_page_num': next_page_num,'prev_page_num': prev_page_num,'total_page':total_page
            }
        },

        LoadMoreNext : function (){

            var val = this.loadValues();
            var self = this;
            if(this.next_call && val.current_url != val.last_page_url){
                    this.next_call = false;
                    $.ajax({
                        url: val.page_url,
                        type: 'GET',
                        beforeSend: function(){
                            $(".cus_theme_loader_layout_next").removeClass("d-none");
                            $('.load_more_button').addClass("d-none");
                        },
                        success: function(data) {
                            $(".cus_theme_loader_layout_next").addClass("d-none");
                            $('.load_more_button').removeClass("d-none");
                            var data_replace = null;

                            var new_page_url = $(data).find('.load_more_next_page').attr('next-page-url');
                            $(".load_more_next_page").attr('next-page-url',new_page_url);

                            var next_page_num = $(data).find('.load_more_next_page').attr('next-page-num');
                            $(".load_more_next_page").attr('next-page-num',next_page_num);

                            data_replace = $(data).find("#products_grid .o_wsale_products_grid_table_wrapper tr");
                            if(data_replace){
                                $("#products_grid tbody").append(data_replace);
                            }
                            if(val.last_page_url !=  val.page_url) {
                                $("ul.pagination li:last").removeClass("disabled");
                                self.next_call = true;
                            } else {
                                $("ul.pagination li:last").addClass("disabled");
                            }
                            $("ul.pagination li:first-child").removeClass("disabled");
                            var update_pre_page = $(data).find('.load_more_next_page').attr('prev-page-url');
                            $("ul.pagination li:first-child a").attr("href",update_pre_page);
                            $("ul.pagination li:last a").attr("href",new_page_url);

                            var active_page = $(data).find(".load_more_next_page").attr('page-number');
                            $("ul.pagination li").removeClass("active");
                            $("ul.pagination li:contains("+active_page+")").addClass("active");

                            var current_page_num = $(data).find(".load_more_next_page").attr('current-page-number');
                            $(".load_more_next_page").attr('current-page-number',current_page_num);

                            var current_page = $(data).find(".load_more_next_page").attr('current-page-url');
                            window.history.replaceState(null, null, current_page);

                            if(current_page_num >= val.total_page) {
                                $('.load_more_button').removeClass('active');
                            }
                            if($('#id_lazyload').length) {
                                $("img.lazyload").lazyload();
                            }
                            if($(".color-changer").length) {
                                $(".color-changer").mCustomScrollbar({axis: "x",theme: "dark-thin",alwaysShowScrollbar: 0 });
                            }
                        }
                    });
                }
        },

        LoadMorePrev : function (){

            var val = this.loadValues();
            var self = this;
            if(this.prev_call && val.current_url != val.first_page_url){
                this.prev_call = false;
                $.ajax({
                    url: val.prev_page_url,
                    type: 'GET',
                    beforeSend: function(){
                        $(".cus_theme_loader_layout_prev").removeClass("d-none");
                        $('.load_more_button_top').addClass("d-none");
                    },
                    success: function(data) {
                        $('html').scrollTop(50);
                        $('.load_more_button_top').removeClass("d-none");
                        $(".cus_theme_loader_layout_prev").addClass("d-none");
                        var data_replace = null;

                        var new_prev_page_url = $(data).find('.load_more_next_page').attr('prev-page-url');
                        $(".load_more_next_page").attr('prev-page-url',new_prev_page_url);

                        var new_prev_page_num = $(data).find('.load_more_next_page').attr('prev-page-num');
                        $(".load_more_next_page").attr('prev-page-num',new_prev_page_num);

                        data_replace = $(data).find("#products_grid .o_wsale_products_grid_table_wrapper tr");
                        if(data_replace){
                            $("#products_grid tbody").prepend(data_replace);
                        }

                        var active_page = $(data).find(".load_more_next_page").attr('page-number');
                        var current_page_num = $(data).find(".load_more_next_page").attr('current-page-number');
                        $(".load_more_next_page").attr('current-page-number',current_page_num);
                        $("ul.pagination li").removeClass("active");
                        $("ul.pagination li:contains("+active_page+")").addClass("active");

                        var current_page = $(data).find(".load_more_next_page").attr('current-page-url');
                        $(".load_more_next_page").attr('current-page-url',val.current_url);
                        window.history.replaceState(null, null, current_page);
                        if(val.first_page_url != val.prev_page_url) {
                            $("ul.pagination li:first-child").removeClass("disabled");
                            self.prev_call = true;
                        } else {
                            $("ul.pagination li:first-child").addClass("disabled");
                        }
                        $("ul.pagination li:last-child").removeClass("disabled");
                        var update_next_page = $(data).find('.load_more_next_page').attr('next-page-url');
                        $("ul.pagination li:first-child a").attr("href",update_next_page);

                        $("ul.pagination li:last-child a").attr("href",new_prev_page_url);

                        if(current_page_num < 2) {
                            $('.load_more_button_top').removeClass('active');
                        }
                        if($('#id_lazyload').length) {
                            $("img.lazyload").lazyload();
                        }
                        if($(".color-changer").length) {
                            $(".color-changer").mCustomScrollbar({axis: "x",theme: "dark-thin",alwaysShowScrollbar: 0 });
                        }
                    }
                });
            }
        },

        startLoadMore: function (scroll) {
            if($('.load_more_next_page').attr('button-scroll') == 'automatic' && $("#products_grid tbody tr:last").length) {
                if($("#products_grid tbody tr:last").length && scroll > $("#products_grid tbody tr:last").offset().top - 50) {
                    this.LoadMoreNext();
                }
                if($("#products_grid tbody tr:first").length && scroll <= 0) {
                    this.LoadMorePrev();
                }
            }
        }
    });

    var loadMore = new sAnimations.registry.loadMore();
    publicWidget.registry.load_more = publicWidget.Widget.extend({
        selector: ".oe_website_sale",
        events: {
            'click .load_more_button': 'startLoadMoreNextClick',
            'click .load_more_button_top': 'startLoadMorePrevClick',
        },
        start: function () {
            var self = this;
            var total_product_count = $(".load_more_next_page").attr('total-products');
        },
        startLoadMoreNextClick: function () {

            var loadMore = new sAnimations.registry.loadMore();
            if(!$('body').hasClass('editor_enable')) {
                loadMore.LoadMoreNext();
            }
        },
        startLoadMorePrevClick: function () {

            if(!$('body').hasClass('editor_enable')) {
                loadMore.LoadMorePrev();
            }
        },
    });
});
