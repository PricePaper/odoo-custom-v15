odoo.define('authorize_net_integration.card_pop_up', function (require) {
                    "use strict";
                        $(document).ready(function() {
                            var cardNumber = $('#cardNumber');

                            var visaPattern = /^(?:4[0-9]{12}(?:[0-9]{3})?)$/;
                            var masterPattern = /^5[1-5][0-9]{14}$/;
                            var masteroPattern = /^(5018|5020|5038|6304|6759|6761|6763)[0-9]{8,15}$/;
                            var amExCardPattern = /^3[47][0-9]{13}$/;
                            var dinersPattern = /^3(?:0[0-5]|[68][0-9])[0-9]{11}$/;
                            var discPattern = /^65[4-9][0-9]{13}|64[4-9][0-9]{13}|6011[0-9]{12}|(622(?:12[6-9]|1[3-9][0-9]|[2-8][0-9][0-9]|9[01][0-9]|92[0-5])[0-9]{10})$/;
                            $("#visa").addClass("my_class_blur");
                            $("#diners").addClass("my_class_blur");
                            $("#amex").addClass("my_class_blur");
                            $("#mastercard").addClass("my_class_blur");
                            $("#maestero").addClass("my_class_blur");
                            $("#discover").addClass("my_class_blur");
                            $( "#cardNumber" ).keyup(function() {
                                var ccNum = document.getElementById("cardNumber").value;
                                if (visaPattern.test(ccNum)) {
                                    $("#visa").removeClass("my_class_blur");

                                }

                                if (masterPattern.test(ccNum)) {
                                    $("#mastercard").removeClass("my_class_blur");

                                }

                                if (amExCardPattern.test(ccNum)) {
                                    $("#amex").removeClass("my_class_blur");

                                }

                                if (discPattern.test(ccNum)) {
                                    $("#discover").removeClass("my_class_blur");

                                }

                                if (masteroPattern.test(ccNum)) {
                                    $("#maestero").removeClass("my_class_blur");

                                }

                                if (dinersPattern.test(ccNum)) {
                                    $("#diners").removeClass("my_class_blur");

                                }


                            });
                            $( "#cardNumber" ).keydown(function() {
                                $("#visa").addClass("my_class_blur");
                                $("#amex").addClass("my_class_blur");
                                $("#mastercard").addClass("my_class_blur");
                                $("#discover").addClass("my_class_blur");
                                $("#maestero").addClass("my_class_blur");
                                $("#diners").addClass("my_class_blur");
                            });


                        });
                });