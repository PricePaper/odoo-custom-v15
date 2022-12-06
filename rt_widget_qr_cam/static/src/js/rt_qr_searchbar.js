/** @odoo-module **/

	import SearchBar from "web.SearchBar";

	const components = { SearchBar };

import { patch } from 'web.utils';
import Dialog from 'web.Dialog';
import core from 'web.core';
const _t = core._t;
var qweb = core.qweb;



/*    var core = require("web.core");
    var qweb = core.qweb;
    var _t = core._t;
    var Dialog = require("web.Dialog");*/

    patch(components.SearchBar.prototype, "rt_widget_qr_cam/static/src/js/rt_qr_searchbar.js", {
        /**
         * @override
         */
        // _constructor() {
        //     this._super(...arguments);
        // },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Get Camera Selection.
         * @private
         */
        _get_camera_selection_rt_widget_qr_cam: async function () {
            var self = this;
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter((device) => device.kind === "videoinput");
            const options = videoDevices.map((videoDevice) => {
                var selected = "";
                var deviceId = videoDevice.deviceId || "";
                var label = videoDevice.label || "";
                if (self.selected_device_id_rt_widget_qr_cam == videoDevice.deviceId) {
                    selected = 'selected=""';
                }
                return "<option " + selected + ' value="' + deviceId + '">' + label + "</option>";
            });
            return options.join("");
        },

        willStart: function () {
            this._super(...arguments);
            var self = this;
            self.audio_beep_rt_widget_qr_cam = new Audio("/rt_widget_qr_cam/static/src/audio/beep.mp3");
            self.selected_device_id_rt_widget_qr_cam = localStorage.getItem("rt_widget_field_char_qr_cam_selected_device_id") || false;
            self._get_camera_selection_rt_widget_qr_cam()
                .then((value) => {
                    self.camera_options_rt_widget_qr_cam = value;
                })
                .catch((error) => {
                    console.error("onRejected function called: " + error.message);
                });
            self.constraints_rt_widget_qr_cam = { audio: false, video: { facingMode: "environment"  } };
            self.selected_device_id_rt_widget_qr_cam = localStorage.getItem("rt_widget_field_char_qr_cam_selected_device_id") || false;
            if (self.selected_device_id_rt_widget_qr_cam) {
                self.constraints_rt_widget_qr_cam = {
                    audio: false,
                    video: {  facingMode: "environment", deviceId: self.selected_device_id_rt_widget_qr_cam },
                };
            }
        },

        /**
         * Start Stream
         * @private
         */
        _start_stream_rt_widget_qr_cam: async function () {
            var self = this;
            let stream = null;
            try {
                stream = await navigator.mediaDevices.getUserMedia(self.constraints_rt_widget_qr_cam);
                self.video_rt_widget_qr_cam.srcObject = stream;
                self.video_rt_widget_qr_cam.setAttribute("playsinline", true); // required to tell iOS safari we don't want fullscreen
                self.video_rt_widget_qr_cam.play();
                /* use the stream */
            } catch (err) {
                /* handle the error */
                console.log(err.name + ": " + err.message);
                var wrap = self.dialog_element_rt_widget_qr_cam.find(".rt_widget_field_char_qr_cam_wrapper");
                if (wrap.length) {
                    var alert_div = '<div class="alert alert-danger" role="alert">' + err.name + ": " + err.message + "</div>";
                    wrap.html(alert_div);
                }
            }
            return stream;
        },

        _handle_detected_code_rt_widget_qr_cam: async function (detected_barcode_or_qr_code) {
            var self = this;
            if (detected_barcode_or_qr_code) {
                //self.is_searchbar_things_already_done_once = true;
                // std odoo code in order to show autocomplete dropdown
                self.state.inputValue = detected_barcode_or_qr_code;
                const wasVisible = self.state.sources.length;
                const query = self.state.inputValue.trim().toLowerCase();
                if (query.length) {
                    self.state.sources = self._filterSources(query);
                    var dont_select_autocomplete_result = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_select_autocomplete_result") || "false";
                    if (dont_select_autocomplete_result == "false") {
                        setTimeout(function () {
                            var autocomplete = self.el.querySelector(".o_searchview_autocomplete li.o_selection_focus a");
                            if (autocomplete) {
                                autocomplete.click();
                            }
                        }, 300);
                    }
                } else if (wasVisible) {
                    self._closeAutoComplete();
                }
                // std odoo code in order to show autocomplete dropdown

                // Change Color
                // ----------------
                var random_color = "#" + ("000000" + Math.floor(Math.random() * 16777215).toString(16)).slice(-6);
                var last_scan_result = self.dialog_element_rt_widget_qr_cam.find(".js_cls_rt_widget_field_char_qr_last_scan_result");
                last_scan_result.css({
                    "background-color": random_color,
                });
                last_scan_result.html("Last scanned: " + detected_barcode_or_qr_code);

                // Settings Implementation
                var dont_close_dialog = "false";
                //var dont_stop_stream = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_stop_stream") || 'false';
                var dont_play_audio = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_play_audio") || "false";
                var dont_stop_stream = "false";
                if (dont_play_audio == "false") {
                    self.audio_beep_rt_widget_qr_cam.play();
                }

                if (dont_stop_stream == "false") {
                    const tracks = self.video_rt_widget_qr_cam.srcObject ? self.video_rt_widget_qr_cam.srcObject.getTracks() : [];
                    for (const track of tracks) {
                        track.stop(); //  note that this will also automatically turn the flashlight off
                    }
                    self.video_rt_widget_qr_cam.srcObject = null;
                    self.scan_again_btn_rt_widget_qr_cam.show();
                } else {
                    self.scan_again_btn_rt_widget_qr_cam.hide();
                }
                if (dont_close_dialog == "false") {
                    self.dialog_object_rt_widget_qr_cam.close();
                }
            }
        },

        _handle_detected_code_rt_widget_qr_cam: async function (detected_barcode_or_qr_code) {
            var self = this;
            // std odoo code in order to show autocomplete dropdown
            self.state.inputValue = detected_barcode_or_qr_code;
            const wasVisible = self.state.sources.length;
            const query = self.state.inputValue.trim().toLowerCase();
            if (query.length) {
                self.state.sources = self._filterSources(query);
                var dont_select_autocomplete_result = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_select_autocomplete_result") || "false";
                if (dont_select_autocomplete_result == "false") {
	
            var search_view_delay = localStorage.getItem("rt_widget_field_char_qr_cam_setting_searchview_auto_selection_delay") || 300;
			search_view_delay = parseInt(search_view_delay);
				
	
                    setTimeout(function () {
                        var autocomplete = self.el.querySelector(".o_searchview_autocomplete li.o_selection_focus a");
                        if (autocomplete) {
                            autocomplete.click();
                        }
                    }, search_view_delay);
                }
            } else if (wasVisible) {
                self._closeAutoComplete();
            }
            // std odoo code in order to show autocomplete dropdown

            // Change Color
            // ----------------
            var random_color = "#" + ("000000" + Math.floor(Math.random() * 16777215).toString(16)).slice(-6);
            var last_scan_result = self.dialog_element_rt_widget_qr_cam.find(".js_cls_rt_widget_field_char_qr_last_scan_result");
            last_scan_result.css({
                "background-color": random_color,
            });
            last_scan_result.html("Last scanned: " + detected_barcode_or_qr_code);

            // Settings Implementation
            var dont_close_dialog = "false";
            //var dont_stop_stream = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_stop_stream") || 'false';
            var dont_play_audio = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_play_audio") || "false";
            var dont_stop_stream = "false";
            if (dont_play_audio == "false") {
                self.audio_beep_rt_widget_qr_cam.play();
            }

            if (dont_stop_stream == "false") {
                const tracks = self.video_rt_widget_qr_cam.srcObject ? self.video_rt_widget_qr_cam.srcObject.getTracks() : [];
                for (const track of tracks) {
                    track.stop(); //  note that this will also automatically turn the flashlight off
                }
                self.video_rt_widget_qr_cam.srcObject = null;
                self.scan_again_btn_rt_widget_qr_cam.show();
            } else {
                self.scan_again_btn_rt_widget_qr_cam.hide();
            }
            if (dont_close_dialog == "false") {
                self.dialog_object_rt_widget_qr_cam.close();
            }
        },

        /**
         * Run Scan
         * @private
         */
        _run_scan_rt_widget_qr_cam: async function () {
            var self = this;
            var detected_barcode_or_qr_code = false;
            var setting_type_code = localStorage.getItem("rt_widget_field_char_qr_cam_setting_type_code") || "both";

            // self.is_searchbar_things_already_done_once = false;
            if (self.video_rt_widget_qr_cam.readyState === self.video_rt_widget_qr_cam.HAVE_ENOUGH_DATA) {
                self.canvas_element_rt_widget_qr_cam.height = self.video_rt_widget_qr_cam.videoHeight;
                self.canvas_element_rt_widget_qr_cam.width = self.video_rt_widget_qr_cam.videoWidth;
                self.canvas_rt_widget_qr_cam.drawImage(self.video_rt_widget_qr_cam, 0, 0, self.canvas_element_rt_widget_qr_cam.width, self.canvas_element_rt_widget_qr_cam.height);
                var imageData = self.canvas_rt_widget_qr_cam.getImageData(0, 0, self.canvas_element_rt_widget_qr_cam.width, self.canvas_element_rt_widget_qr_cam.height);
                // var code = await jsQR(imageData.data, imageData.width, imageData.height, {
                //     inversionAttempts: "dontInvert",
                // });

                // ----------------------------------------------------------------
                // jsQR
                // ----------------------------------------------------------------
                if (["qrcode", "both"].indexOf(setting_type_code) != -1) {
                    try {
                        var code = await jsQR(imageData.data, imageData.width, imageData.height, {
                            inversionAttempts: "dontInvert",
                        });

                        if (code) {
                            //    std odoo code in order to show autocomplete dropdown
                            detected_barcode_or_qr_code = code.data;
                        }
                    } catch (e) {
                        console.error(e);
                    }
                }

                // ----------------------------------------------------------------
                // jsQR
                // ----------------------------------------------------------------

                // ----------------------------------------------------------------
                // Quagga
                // ----------------------------------------------------------------

                if (["barcode", "both"].indexOf(setting_type_code) != -1) {
                    try {
                        // Create the QuaggaJS config object for the live stream
                        var fullQuality = self.canvas_element_rt_widget_qr_cam.toDataURL("image/jpeg", 1.0);
                        var liveStreamConfig = {
                            src: fullQuality,
                            inputStream: {
                                type: "ImageStream",
                                size: 800,
                            },
                            locator: {
                                patchSize: "medium",
                                halfSample: true,
                            },
                            numOfWorkers: navigator.hardwareConcurrency ? navigator.hardwareConcurrency : 1,
                            decoder: {
                                readers: [
                                    "code_128_reader",
                                    "code_93_reader",
                                    "code_39_vin_reader",
                                    "code_39_reader",
                                    "ean_reader",
                                    "ean_8_reader",
                                    "codabar_reader",
                                    "i2of5_reader",
                                    "2of5_reader",
                                    // 'upc_reader',
                                    // 'upc_e_reader',
                                ],
                                multiple: false,
                            },
                            locate: false,
                            frequency: 20,
                        };

                        await Quagga.decodeSingle(liveStreamConfig, function (result) {
                            if (result.codeResult) {
                                var countDecodedCodes = 0,
                                    err = 0;
                                $.each(result.codeResult.decodedCodes, function (id, error) {
                                    if (error.error != undefined) {
                                        countDecodedCodes++;
                                        err += parseFloat(error.error);
                                    }
                                });
                                if (err / countDecodedCodes < 0.1) {
                                    if (result.codeResult.format == "upc_e" || result.codeResult.format == "upc_a") {
                                        if (result.codeResult.code) {
                                            //$('#scanner_input').val(result.codeResult.code);
                                        } else {
                                            //alert("Unable to detect correct code. Please try again.");
                                        }
                                    } else {
                                        var msg = "Incorrect barcode detected! Barcode format is: " + result.codeResult.format + " and Barcode number is: " + result.codeResult.code;
                                        detected_barcode_or_qr_code = result.codeResult.code;
                                        //code_detected_once = true
                                        //return false; // breaks
                                        //alert(code);
                                    }
                                }
                            }
                        });
                    } catch (e) {
                        console.error(e);
                    }
                }
                // ----------------------------------------------------------------
                // Quagga
                // ----------------------------------------------------------------

                if (!self.is_searchbar_things_already_done_once) {
                    if (detected_barcode_or_qr_code) {
                        self.is_searchbar_things_already_done_once = true;
                        await self._handle_detected_code_rt_widget_qr_cam(detected_barcode_or_qr_code);
                    }
                }
            }
        },

        _rt_widget_qr_cam_on_click_search_bar_qr_scan_btn(ev) {
            // ev.preventDefault();
            //ev.stopPropagation();
            var self = this;
            self.is_searchbar_things_already_done_once = false;
            var dialog = new Dialog(this, {
                size: "medium",
                buttons: [],
                dialogClass: "rt_widget_field_char_qr_cam_dialog",
                backdrop: "true",
                renderHeader: true,
                renderFooter: false,
                //fullscreen: true,
                title: _t("Scan Barcode and QR Code"),
                $content: qweb.render("rt_widget_qr_cam.rt_widget_field_char_qr_cam.dialog", {
                    //  heading: heading,
                }),
            });
            dialog.open().opened(function () {
                // To Vertically centered dialog add class
                dialog.$modal.find(".modal-dialog").addClass("modal-dialog-centered");
                // dialog opened method start here
                // ----------------------------------
                self.video_rt_widget_qr_cam = document.querySelector("#rt_widget_field_char_qr_video");
                self.canvas_element_rt_widget_qr_cam = document.querySelector("#rt_widget_field_char_qr_canvas");
                self.canvas_rt_widget_qr_cam = self.canvas_element_rt_widget_qr_cam.getContext("2d");
                var $camera_select = dialog.$el.find("#rt_widget_field_char_qr_cam_select");
                $camera_select.html(self.camera_options_rt_widget_qr_cam);
                self.dialog_element_rt_widget_qr_cam = dialog.$el;
                self.dialog_object_rt_widget_qr_cam = dialog;
                self.scan_again_btn_rt_widget_qr_cam = dialog.$el.find(".js_cls_scan_again_button");
                self.scan_again_btn_rt_widget_qr_cam.hide();

                function tick() {
                    self._run_scan_rt_widget_qr_cam();
                    if (!self.is_searchbar_things_already_done_once) {
                        requestAnimationFrame(tick);
                    }
                }
                self._start_stream_rt_widget_qr_cam().then((value) => {
                    if (value) {
                        tick();
                    }
                });

                dialog.$el.on("change", "#rt_widget_field_char_qr_cam_select", function (ev) {
                    var selected_device_id = $(ev.currentTarget).val();

                    self.constraints_rt_widget_qr_cam = {
                        audio: false,
                        video: {  facingMode: "environment" , deviceId: selected_device_id },
                    };
                    localStorage.setItem("rt_widget_field_char_qr_cam_selected_device_id", selected_device_id);
                    const tracks = self.video_rt_widget_qr_cam.srcObject ? self.video_rt_widget_qr_cam.srcObject.getTracks() : [];
                    for (const track of tracks) {
                        track.stop(); //  note that this will also automatically turn the flashlight off
                    }
                    location.reload();
                });

                /* On Click js_cls_rt_close_dialog_stop_scanning_btn
				------------------------- */
                dialog.$el.on("click", ".js_cls_rt_close_dialog_stop_scanning_btn", function (ev) {
                    //ev.stopPropagation();
                    ev.preventDefault();
                    try {
                        const tracks = self.video_rt_widget_qr_cam.srcObject ? self.video_rt_widget_qr_cam.srcObject.getTracks() : [];
                        for (const track of tracks) {
                            track.stop(); //  note that this will also automatically turn the flashlight off
                        }
                        self.video_rt_widget_qr_cam.srcObject = null;
                        //setTimeout(function(){ }, 1000);
                        dialog.close();
                    } catch (error) {
                        console.error(error);
                    }
                });

                /* On Click js_cls_scan_again_button
				------------------------- */
                dialog.$el.on("click", ".js_cls_scan_again_button", function (ev) {
                    //ev.stopPropagation();
                    ev.preventDefault();
                    self.is_searchbar_things_already_done_once = false;
                    self._start_stream_rt_widget_qr_cam().then((value) => {
                        if (value) {
                            tick();
                        }
                    });
                });

                /* On Click js_cls_rt_close_dialog_stop_scanning_btn
				------------------------- */
                dialog.$el.on("change", ".js_cls_setting_type_code", function (ev) {
                    localStorage.setItem("rt_widget_field_char_qr_cam_setting_type_code", $(ev.currentTarget).val());
                });

                dialog.$el.on("change", ".js_cls_setting_dont_close_dialog", function (ev) {
                    localStorage.setItem("rt_widget_field_char_qr_cam_setting_dont_close_dialog", this.checked);
                });

                dialog.$el.on("change", ".js_cls_setting_dont_stop_stream", function (ev) {
                    localStorage.setItem("rt_widget_field_char_qr_cam_setting_dont_stop_stream", this.checked);
                });

                dialog.$el.on("change", ".js_cls_setting_dont_play_audio", function (ev) {
                    localStorage.setItem("rt_widget_field_char_qr_cam_setting_dont_play_audio", this.checked);
                });

                dialog.$el.on("change", ".js_cls_setting_dont_select_autocomplete_result", function (ev) {
                    localStorage.setItem("rt_widget_field_char_qr_cam_setting_dont_select_autocomplete_result", this.checked);
                });

                dialog.$el.on("change", ".js_cls_setting_m2o_auto_selection_delay", function (ev) {
		 			var n =  $(ev.currentTarget).val();
					if (n < 500) {
		                alert('Delay must be greater than 500');
		                $(ev.currentTarget).val(500);
		            } else {
						localStorage.setItem("rt_widget_field_char_qr_cam_setting_m2o_auto_selection_delay", n );
		            }
                    
                });

                dialog.$el.on("change", ".js_cls_setting_searchview_auto_selection_delay", function (ev) {
		 			var n =  $(ev.currentTarget).val();
					if (n < 300) {
		                alert('Delay must be greater than 300');
		                $(ev.currentTarget).val(300);
		            } else {
						localStorage.setItem("rt_widget_field_char_qr_cam_setting_searchview_auto_selection_delay", n );
		            }
                    
                });

                // Apply Default Settings From Local Storage
                // ------------------------------------------

                var setting_type_code = localStorage.getItem("rt_widget_field_char_qr_cam_setting_type_code") || "both";

                if (setting_type_code == "barcode") {
                    dialog.$el.find('input[name="setting_type_code"][value="barcode"]').attr("checked", true);
                } else if (setting_type_code == "qrcode") {
                    dialog.$el.find('input[name="setting_type_code"][value="qrcode"]').attr("checked", true);
                } else {
                    dialog.$el.find('input[name="setting_type_code"][value="both"]').attr("checked", true);
                }

                dialog.$el.on("show.bs.collapse", "#rt_widget_field_char_qr_settings", function (ev) {
                    //ev.stopPropagation();
                    // Settings Implementation
                    var dont_close_dialog = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_close_dialog") || "false";
                    var dont_stop_stream = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_stop_stream") || "false";
                    var dont_play_audio = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_play_audio") || "false";
                    var dont_select_autocomplete_result = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_select_autocomplete_result") || "false";

                    if (dont_close_dialog == "true") {
                        dialog.$el.find('input[name="setting_dont_close_dialog"]').attr("checked", true);
                    } else {
                        dialog.$el.find('input[name="setting_dont_close_dialog"]').attr("checked", false);
                    }
                    if (dont_stop_stream == "true") {
                        dialog.$el.find('input[name="setting_dont_stop_stream"]').attr("checked", true);
                    } else {
                        dialog.$el.find('input[name="setting_dont_stop_stream"]').attr("checked", false);
                    }
                    if (dont_play_audio == "true") {
                        dialog.$el.find('input[name="setting_dont_play_audio"]').attr("checked", true);
                    } else {
                        dialog.$el.find('input[name="setting_dont_play_audio"]').attr("checked", false);
                    }
                    if (dont_select_autocomplete_result == "true") {
                        dialog.$el.find('input[name="setting_dont_select_autocomplete_result"]').attr("checked", true);
                    } else {
                        dialog.$el.find('input[name="setting_dont_select_autocomplete_result"]').attr("checked", false);
                    }

                    var m2o_delay = localStorage.getItem("rt_widget_field_char_qr_cam_setting_m2o_auto_selection_delay") || 500;
                    var search_bar_delay = localStorage.getItem("rt_widget_field_char_qr_cam_setting_searchview_auto_selection_delay") || 300;

                   dialog.$el.find('input[name="setting_m2o_auto_selection_delay"]').val(m2o_delay);
                   dialog.$el.find('input[name="setting_searchview_auto_selection_delay"]').val(search_bar_delay);



                });

                // ------------------------------------------
                // Apply Default Settings From Local Storage

                /* On Dialog Close
------------------------- */
                dialog.on("closed", self, function () {	
                    self.is_searchbar_things_already_done_once = true;
                });

                // dialog opened method ends here
                // ----------------------------------
            });
        },
    });

