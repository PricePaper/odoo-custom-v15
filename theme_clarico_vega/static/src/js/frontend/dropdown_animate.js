odoo.define('theme_clarico_vega.dropdown_animate', function(require) {
    "use strict";

    const publicWidget = require('web.public.widget');
    var sAnimations = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var menu_state = [];
    var menuData = [];
    var catArray = [];
    var allMenuData = [];
    var catAllMenuData = [];

    publicWidget.registry.ScrollTop = sAnimations.Animation.extend({
        selector: '#wrapwrap',
        effects: [{
            startEvents: 'scroll',
            update: '_scrollTop',
        }],
        _scrollTop: function(scroll) {
            if (scroll > 300) {
                $('.scrollup-div').fadeIn();
            } else {
                $('.scrollup-div').fadeOut();
            }
        },
    });

    //------------------------------------------
    // Dynamic Category Mega Menu
    //------------------------------------------
    publicWidget.registry.dynamicCategoryMegaMenu = publicWidget.Widget.extend({
        selector: '#wrapwrap',
        read_events: {
            'mouseenter .o_hoverable_dropdown .te_dynamic_ept': '_onHoverNestedMenuLi',
            'mouseenter .o_hoverable_dropdown .te_all_dynamic_ept': '_onHoverAllMenuLi',
            'mouseenter .o_hoverable_dropdown .te_mega_menu_ept': '_onHoverMegaMenuLi',
            'mouseleave .o_hoverable_dropdown .te_dynamic_ept': '_onLeaveMenuLi',
            'mouseleave .o_hoverable_dropdown .te_all_dynamic_ept': '_onLeaveMenuLi',
        },
        start: function() {
            var self = this;
            $('.te_mega_menu_ept').find('.dropdown-menu.o_mega_menu').html('');
            /* Make parent menu clickable while on_hover option selected */
            if ($(window).innerWidth() > 992) {
                $('header.o_hoverable_dropdown .te_dynamic_ept .nav-link, header.o_hoverable_dropdown .te_mega_menu_ept .nav-link').click(function() {
                    location.href = this.href;
                });
            } else {
                $('#top_menu .te_mega_menu_ept').find('.nav-link').attr('href', '#');
            }

            $("#top_menu li.te_mega_menu_ept").each(function(ev) {
                var $target = $(ev.currentTarget);
                var self = this;
                if ($(this).find('.nav-link').attr('data-id')) {
                    var curr_menu_id = $(this).find('.nav-link').attr('data-id');
                    ajax.jsonRpc('/dynamic_category_mega_menu', 'call', {
                        'menu_id': curr_menu_id
                    }).then(function(data) {
                        if (data) {
                            var menu_id = $(data).attr('menu_id');
                            menuData.push({
                                menu_id,
                                data
                            });
                            if ($(data).hasClass('menu-categories-container')) {
                                $($(data).find('.parent-category')).each(function(ev) {
                                    if ($(this).attr('data-id')) {
                                        var category_id = $(this).attr('data-id');
                                        catArray.push(category_id);
                                    }
                                });
                                $.each(catArray, function(key, value) {
                                    ajax.jsonRpc('/dynamic_mega_menu_child', 'call', {
                                        'category_id': value
                                    }).then(function(data) {
                                        if (data) {
                                            var menu_id = $(data).attr('menu_id');
                                            catAllMenuData.push({
                                                menu_id,
                                                data
                                            });
                                        }
                                    })
                                });
                            }
                        }
                    })
                }
            });

            self._callScript();
        },
        _onLeaveMenuLi: function(ev) {
            var self = $(ev.currentTarget);
            if ($(window).width() >= 992) {
                $(self).find('.dropdown-menu').removeClass('show');
            }
        },
        _onHoverNestedMenuLi: function(ev) {
            var self = this;
            if ($(window).width() < 768) {
                self._onClickMegaMenuLi(ev);
            }
            self._onClickNestedMenuLi(ev);
            self._callScript(ev);
            if ($(window).width() >= 992) {
                self._removeShowClass();
                $(ev.currentTarget).addClass('show');
                $(ev.currentTarget).find("#custom_menu").addClass('show');
            }
        },
        _onHoverAllMenuLi: function(ev) {
            var self = this;
            if ($(window).width() < 768) {
                self._onClickMegaMenuLi(ev);
            }
            self._onClickAllMenuLi(ev);
            if ($(window).width() >= 992) {
                self._removeShowClass();
                $(ev.currentTarget).addClass('show');
                $(ev.currentTarget).find("#all_dynamic_menu").addClass('show');
            }
        },
        _onHoverMegaMenuLi: function(ev) {
            var self = this;
            self._onClickMegaMenuLi(ev);
            if ($(window).width() >= 992) {
                self._removeShowClass();
                $(ev.currentTarget).addClass('show');
                $(ev.currentTarget).find(".dropdown-menu").addClass('show');
            }
        },
        _removeShowClass: function() {
            $('#top_menu').find('li.dropdown').removeClass('show');
            $('#top_menu').find('li.dropdown .dropdown-menu').removeClass('show');
        },
        _onClickMegaMenuLi: function(ev) {
            ev.stopPropagation();
            var self = $(ev.currentTarget)
            var this_s = this
            var menu_id = $(self).find('.nav-link').attr('data-id');
            if (menu_id) {
                if (self.find('.dropdown-menu').is(':empty')) {
//                if ($.inArray(menu_id, menu_state) == -1) {
                    if ($(self).attr('id')) {
                        var getId = $(self).attr('id');
                        $.each(menuData, function() {
                            if (this.menu_id === getId) {
                                self.find('.dropdown-menu.o_mega_menu').html(this.data);
                            }
                        });
                        //menu_state.push(menu_id);
                    }
                }
                this_s._callScript(ev);
            }
            if ($(window).width() >= 992) {
                if (!$(self).hasClass('show')) {
                    this_s._removeShowClass();
                }
                self.toggleClass('show');
                self.find(".dropdown-menu").toggleClass('show');
            }
            this_s._callFirstEle();
        },
        _onClickNestedMenuLi: function(ev) {
            ev.stopPropagation();
            var self = $(ev.currentTarget)
            var this_s = this
            var event = ev
            var menu_id = $(self).find('.nav-link').attr('data-id');
            if (menu_id) {
                if (self.find('.dropdown-menu').is(':empty')) {
//                if ($.inArray(menu_id, menu_state) == -1) {
                    if ($(self).attr('id')) {
                        var getId = $(self).attr('id');
                        $.each(menuData, function() {
                            if (this.menu_id === getId) {
                                self.find('.dropdown-menu.o_mega_menu').html(this.data);
                                self.find('.dropdown-menu.o_mega_menu').addClass('show');
                            }
                        });
                        //menu_state.push(menu_id);
                    }
                }
            }
            if ($(window).width() >= 992) {
                if (!$(self).hasClass('show')) {
                    this_s._removeShowClass();
                }
                self.toggleClass('show');
                self.find(".dropdown-menu").toggleClass('show');
            }
            this_s._callScript(ev);
        },
        _onClickAllMenuLi: function(ev) {
            ev.stopPropagation();
            var self = $(ev.currentTarget)
            var this_s = this
            var event = ev
            var menu_id = $(self).find('.nav-link').attr('data-id');
            var dynamicCat = new publicWidget.registry.dynamicCategory();
            this_s._callFirstEle();
            dynamicCat.scrollCategory(ev);
            if (menu_id) {
                if (self.find('.dropdown-menu').is(':empty')) {
                    if ($(self).attr('id')) {
                        var getId = $(self).attr('id');
                        $.each(menuData, function() {
                            if (this.menu_id === getId) {
                                self.find('.dropdown-menu.o_mega_menu').html(this.data);
                                this_s._callFirstEle();
                                self.find('.dropdown-menu.o_mega_menu').addClass('show');
                            }
                        });
                    }
                }
            }
            if ($(window).width() >= 992) {
                if (!$(self).hasClass('show')) {
                    this_s._removeShowClass();
                }
                self.toggleClass('show');
                self.find(".dropdown-menu").toggleClass('show');
            }
        },
        _callFirstEle: function() {
            if ($(window).width() >= 992) {
                var has_parent_content = $('.menu-categories-container li.nav-item.parent-category').find('.main_category_child').first()
                var get_parent = $(has_parent_content).parents('.parent-category');
                $(get_parent).trigger('mouseenter');
                $(get_parent).find('.sub-menu-dropdown').css({
                    "visibility": "visible",
                    "opacity": "1",
                });
            }
        },
        _callScript: function(ev) {
            var li_count = $("#top_menu_collapse >#top_menu >li").length;
            var li_pos = $('.te_dynamic_ept').index() + 1;
            $("#custom_menu li").each(function() {
                var has_ctg = $(this).find("ul.t_custom_subctg").length > 0
                if (has_ctg) {
                    var ul_index = 0;
                    if (li_pos > li_count / 2) {
                        $(this).children("#custom_recursive").css({
                            "transform": "translateX(-20px)",
                        });
                    }
                    if ($(document).find('#wrapwrap').hasClass('o_rtl')) {
                        if (li_pos > li_count / 2) {
                            $(this).children("#custom_recursive").css({
                                "transform": "translateX(20px)",
                            });
                        } else {
                            $(this).children("#custom_recursive").css({
                                "transform": "translateX(-20px)",
                            });
                        }
                    }
                    $(document).on('mouseenter', "#custom_menu_li", function(ev) {
                        var li_place = $(this).position().top;
                        $(this).children("#custom_recursive").css("top", li_place);
                        var self = $(this).children("#custom_recursive");
                        if ($(this).children("#custom_recursive").length > 0) {
                            ul_index = $(self).parents("ul").length == 0 ? $(self).parents("ul").length : ul_index + 1;
                            $(self).css({
                                "opacity": "1",
                                "visibility": "visible",
                                "transform": "translateX(-10px)",
                                "transition": "all 0.2s",
                            });
                            if ($(window).width() <= 991) {
                                $(self).css({
                                    "position": "relative",
                                    "left": "0",
                                    "width": "100%",
                                    "max-width": "100%",
                                    "overflow": "hidden",
                                });
                            }
                            if (li_pos > li_count / 2) {
                                $(self).css({
                                    "left": "100%",
                                    "right": "auto",
                                    "transform": "translateX(-10px)",

                                });
                            }
                            if ($(document).find('#wrapwrap').hasClass('o_rtl')) {
                                $(self).css({
                                    "transform": "translateX(12px)",
                                });
                                if (li_pos > li_count / 2) {
                                    $(self).css({
                                        "right": "100%",
                                        "left": "auto",
                                        "transform": "translateX(12px)",
                                    });
                                }
                            }
                        }
                    });
                    $(document).on('mouseleave', "#custom_menu_li", function(ev) {
                        $(this).children("ul#custom_recursive").css({
                            "opacity": "0",
                            "visibility": "hidden",
                            "transform": "translateX(20px)",
                        });
                        if (li_pos > li_count / 2) {
                            $(this).children("ul#custom_recursive").css({
                                "transform": "translateX(-20px)",
                            });
                        }
                    });
                }
            })
        },
    });

    $(document).ready(function($) {
        //Category mega menu
        setTimeout(function() {
            if ($(window).width() >= 992) {
                $('header.o_hoverable_dropdown .te_dynamic_ept >.dropdown-toggle, header.o_hoverable_dropdown .te_mega_menu_ept >.dropdown-toggle').removeAttr('data-toggle');
                $('header.o_hoverable_dropdown .te_dynamic_ept >.dropdown-toggle, header.o_hoverable_dropdown .te_mega_menu_ept >.dropdown-toggle').removeAttr('aria-expanded');
                if ($('header.o_hoverable_dropdown').length == 0) {
                    $('.te_dynamic_ept > a.dropdown-toggle, .te_mega_menu_ept > a.dropdown-toggle').attr('href', '#');
                    $('.te_dynamic_ept > a.dropdown-toggle, .te_mega_menu_ept > a.dropdown-toggle').attr('aria-expanded');
                }
            }
        }, 100);

        if ($(window).width() <= 991) {
            $(".te_dynamic_ept >a").append('<span class = "fa fa-chevron-down te_icon" />');
            $('.te_icon').attr('data-toggle', 'true');
            $('.te_icon').attr('aria-expanded', 'true');
            $(document).on('click', "span.te_icon", function(ev) {
                if ($(ev.target).is('.te_icon')) {
                    ev.preventDefault();
                    $(this).parent("a").siblings('.te_custom_submenu').slideDown('slow');
                    $(this).addClass('te_icon_ctg');
                }
            });
            $(document).mouseup(function(e) {
                var container = $(".te_dynamic_ept");
                if (!container.is(e.target) && container.has(e.target).length === 0) {
                    $('.te_icon').parent("a").siblings('.te_custom_submenu').slideUp('slow');
                }
            });
            $(document).keyup(function(e) {
                if (e.keyCode == 27) {
                    $('.te_icon').parent("a").siblings('.te_custom_submenu').slideUp('slow');
                }
            })
            $(document).on('click', "span.te_icon_ctg", function(ev) {
                $(this).parent("a").siblings('.te_custom_submenu').slideUp('slow');
                $(this).removeClass('te_icon_ctg');
            });
        }
    });

    publicWidget.registry.dropdown_animate = publicWidget.Widget.extend({
        selector: "#wrapwrap",
        start: function() {
            var self = this;
            self.showDropdown();
            self.showFooter();
            self.showDropdownCategory();
            setTimeout(function() {
                var addToCart = $('#product_details').find('#add_to_cart').attr('class');
                var buyNow = $('#product_details').find('.o_we_buy_now').attr('class');
                $('.prod_details_sticky_div #add_to_cart').attr('class', addToCart);
                $('.prod_details_sticky_div .o_we_buy_now').attr('class', buyNow);
            }, 800);
            /* Website description field attribute is removed while editor opening */
            $('#edit-page-menu a[data-action="edit"]').on('click', function() {
                if ($('body .product_full_description').length) {
                    $('.product_full_description').removeAttr('data-oe-expression');
                }
            });

        },
        showDropdown: function() {
            $('.te_advanced_search_div .dropdown, .dropdown, .te_header_before_overlay .js_language_selector .dropup, header .js_language_selector .dropup').on('show.bs.dropdown', function(ev) {
                $('.dropdown-menu').removeClass('show');
                if (!$(ev.currentTarget).parents('#top_menu').find('o_mega_menu_toggle')) {
                    $(this).find('.dropdown-menu').first().stop(true, true).slideDown(150);
                }
            });
            $('.te_advanced_search_div .dropdown, .dropdown, .te_header_before_overlay .js_language_selector .dropup, header .js_language_selector .dropup').on('hide.bs.dropdown', function(ev) {
                if (!$(ev.currentTarget).parents('#top_menu').find('o_mega_menu_toggle')) {
                    $(this).find('.dropdown-menu').first().stop(true, true).slideUp(150);
                }
            });
        },
        showFooter: function() {
            if ($(window).width() < 768) {
                $('#footer .row > .footer-column-2 .footer_top_title_div').click(function() {
                    $(this).siblings('.te_footer_info_ept').toggleClass('active');
                    $(this).toggleClass('active');
                });
            }
        },
        showDropdownCategory: function() {
            $(".te_advanced_search_div .dropdown-menu a.dropdown-item").on('click', function() {
                $(this).parents(".dropdown").find('.btn.ept-parent-category .span_category').html($(this).text());
                $('.te_advanced_search_div .dropdown-menu a.dropdown-item').removeClass('active');
                $(this).parents(".dropdown").find('.btn.ept-parent-category .span_category').val($(this).addClass('active').val());
            });
        },
    });

    //------------------------------------------
    // Dynamic Category Animation
    //------------------------------------------
    publicWidget.registry.dynamicCategory = publicWidget.Widget.extend({
        selector: '#top_menu_collapse',
        read_events: {
            'mouseenter .parent-category': '_onMouseEnter',
            'click .sub-menu-dropdown': '_preventClick',
            'click .main_category_child': '_onMouseEnter',
            'click .te_mega_menu_ept': '_onClickDynamicMenu',
            'click .ctg_arrow': '_onClickOnArrow',
        },
        start: function() {
            /* For horizontal category custom scroll */
            var horizontal_category = $('.te_horizontal_category');
            if (horizontal_category.length > 0 && horizontal_category[0].scrollWidth > horizontal_category[0].clientWidth) {
                if ($('#wrapwrap').hasClass('o_rtl')) {
                    $(".te_category_round_image").css({
                        "overflow-y": "scroll",
                        "justify-content": "unset",
                        "-webkit-overflow-scrolling": "touch",
                    });
                    $(".te_category_pills").css({
                        "margin-bottom": "10px",
                        "padding": "0px 3px",
                        "overflow-y": "scroll",
                        "-webkit-overflow-scrolling": "touch",
                    });
                    $(".te_category_round_image_style").css({
                        "margin-bottom": "5px",
                    });
                } else {
                    $('.te_horizontal_category').mCustomScrollbar({
                        axis: "x",
                        theme: "dark-thin",
                        alwaysShowScrollbar: 0
                    });
                }
            }
            /*---------------------------------------*/
        },
        _onMouseEnter: function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var self = $(ev.currentTarget)
            if (self.hasClass('main_category_child')) {
                self = self.parents('.parent-category')
            }
            var this_s = this
            var event = ev
            var category_id = self.attr('data-id');
            if (!self.find('.dynamic_mega_menu_child').length == 1) {
                if (self.find('.sub-menu-dropdown-content').is(':empty')){
                    $.each(catAllMenuData, function() {
                        if (this.menu_id === category_id) {
                            self.find('.sub-menu-dropdown-content').html(this.data);
                            this_s.scrollCategory(event);
                        }
                    });
                    this_s.showScrollSubContent(ev);
                    this_s.scrollCategory(event);
                }
                else {
                    self.find('.sub-menu-dropdown').css({'opacity':'1', 'z-index':'99'});
                }
            }

        },
        _preventClick: function(ev) {
            ev.stopPropagation();
        },
        showScrollSubContent: function(ev) {
             if ($(window).width() > 991) {
                  var self = $(ev.currentTarget);
                  var scrollDiv = self.find('.sub-menu-dropdown-content');
                  var content = $(scrollDiv).prop("scrollHeight");
                  if (content > 338) {
                       $(scrollDiv).mCustomScrollbar({
                           axis: "y",
                           theme: "dark-thin",
                           alwaysShowScrollbar: 1,
                       });
                  }
                  else {
                       $(scrollDiv).mCustomScrollbar("disable")
                  }
             }
        },
        scrollCategory: function(ev) {
            var self = $(ev.currentTarget);
            if (!$(ev.currentTarget).hasClass('parent-category')) {
                self = $(ev.currentTarget).parents('.parent-category')
            }
            self.find(".category_ul").each(function(ev) {
                var li_count = $(this)[0].scrollHeight;
                if (li_count > 184) {
                    $(this).mCustomScrollbar({
                        axis: "y",
                        theme: "dark-thin",
                        alwaysShowScrollbar: 1
                    });
                } else {
                    $(this).mCustomScrollbar("disable")
                }
            });
        },
        _onClickDynamicMenu: function(ev) {
            var self = $(ev.currentTarget)
            if ($(window).width() < 768) {
                if ($(self).hasClass('show')) {
                    self.removeClass('show');
                    self.find(".dropdown-menu").removeClass('show');
                } else {
                    self.addClass('show');
                    self.find(".dropdown-menu").addClass('show');
                }
            }
            if ($(window).width() < 992) {
                if ($(self).hasClass('show')) {
                    self.removeClass('show');
                    self.find(".dropdown-menu").removeClass('show');
                }
            }
        },
        _onClickOnArrow: function(ev) {
            if ($(window).width() <= 991) {
                $(ev.currentTarget).toggleClass('te_down_ctg_icon');
                if ($(ev.currentTarget).hasClass('te_down_ctg_icon')) {
                    ev.preventDefault();
                    $(ev.currentTarget).siblings("ul#custom_recursive").slideDown('slow');
                    return false;
                } else {
                    $(ev.currentTarget).siblings("ul#custom_recursive").slideUp('slow');
                    return false;
                }
            }
        },
    });
});
