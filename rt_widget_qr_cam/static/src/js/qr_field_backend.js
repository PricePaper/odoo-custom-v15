odoo.define("rt_widget_qr_cam.widget_qr_cam", function (require) {
    "use strict";

    var basicFields = require("web.basic_fields");
    var fieldRegistry = require("web.field_registry");
    var core = require("web.core");
    var qweb = core.qweb;
    var _t = core._t;
    var Dialog = require("web.Dialog");

    /* 
=============================
 Many2one Field
=============================
*/

    var relational_fields = require("web.relational_fields");
    var FieldMany2One = relational_fields.FieldMany2One;

    var FieldMany2OneQRCam = FieldMany2One.extend({
        //--------------------------------------------------------------------------
        // Widget Many2one Scan Things Start
        //--------------------------------------------------------------------------

        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            var self = this;
            self.audio_beep = new Audio("/rt_widget_qr_cam/static/src/audio/beep.mp3");
            self.selected_device_id = localStorage.getItem("rt_widget_field_char_qr_cam_selected_device_id") || false;
            self._get_camera_selection()
                .then((value) => {
                    self.camera_options = value;
                })
                .catch((error) => {
                    console.error("onRejected function called: " + error.message);
                });
            self.constraints = { audio: false, video: { facingMode: "environment"} };
            self.selected_device_id = localStorage.getItem("rt_widget_field_char_qr_cam_selected_device_id") || false;
            if (self.selected_device_id) {
                self.constraints = {
                    audio: false,
                    video: {  facingMode: "environment", deviceId: self.selected_device_id },
                };
            }
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Get Camera Selection.
         * @private
         */
        _get_camera_selection: async function () {
            var self = this;
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter((device) => device.kind === "videoinput");
            const options = videoDevices.map((videoDevice) => {
                var selected = "";
                var deviceId = videoDevice.deviceId || "";
                var label = videoDevice.label || "";
                if (self.selected_device_id == videoDevice.deviceId) {
                    selected = 'selected=""';
                }
                return "<option " + selected + ' value="' + deviceId + '">' + label + "</option>";
            });
            return options.join("");
        },

        /**
         * Start Stream
         * @private
         */
        _start_stream: async function () {
            var self = this;
            let stream = null;
            try {
                stream = await navigator.mediaDevices.getUserMedia(self.constraints);
                self.video.srcObject = stream;
                self.video.setAttribute("playsinline", true); // required to tell iOS safari we don't want fullscreen
                self.video.play();
                /* use the stream */
            } catch (err) {
                /* handle the error */
                console.log(err.name + ": " + err.message);
                var wrap = self.dialog_element.find(".rt_widget_field_char_qr_cam_wrapper");
                if (wrap.length) {
                    var alert_div = '<div class="alert alert-danger" role="alert">' + err.name + ": " + err.message + "</div>";
                    wrap.html(alert_div);
                }
                //return stream;
            }
            return stream;
        },

        _handle_detected_code_rt_widget_qr_cam: async function (detected_barcode_or_qr_code) {
            var self = this;
            self.is_searchbar_things_already_done_once = true;
            var m2o_delay = localStorage.getItem("rt_widget_field_char_qr_cam_setting_m2o_auto_selection_delay") || 500;
			m2o_delay = parseInt(m2o_delay);

            // final value
            // -----------------------------------------------
            // update value for many2one field
            //self.$input.val(detected_barcode_or_qr_code);
            //await self.$input.autocomplete("search");

// async function FetchDropdownAutocomplete() {
 // await self.$input.val(detected_barcode_or_qr_code);
 // await self.$input.autocomplete("search");
// var values = await self._search(detected_barcode_or_qr_code);
// }

/*FetchDropdownAutocomplete()
.catch(e => {
  console.log('There has been a problem with your fetch operation: ' + e.message);
});
*/

var is_found_record_in_dropdown_list = false;
var values = await self._search(detected_barcode_or_qr_code);
for (var i = 0; i < values.length; i++) {
   if (values[i].hasOwnProperty('id')){
		is_found_record_in_dropdown_list = true;
		self.reinitialize({ id: values[i]['id'], display_name: values[i]['name'] });		
		break;
	}
}



                if (is_found_record_in_dropdown_list) {
                    self.$input.addClass("rt_widget_field_many2one_qr_cam_bg_success");
                    self.$input.removeClass("rt_widget_field_many2one_qr_cam_bg_danger");
                } else {
					self.reinitialize(false);
                    self.$input.addClass("rt_widget_field_many2one_qr_cam_bg_danger");
                    self.$input.removeClass("rt_widget_field_many2one_qr_cam_bg_success");
                    alert("Record not found for this scanned barcode/QR code: " + detected_barcode_or_qr_code);
                }

/*            setTimeout(function () {
                var $found_record_in_dropdown_list = self.$input.autocomplete('widget').find("li:not(.o_m2o_dropdown_option):first a");

                if ($found_record_in_dropdown_list.length) {
                    $found_record_in_dropdown_list.click();
                    self.$input.addClass("rt_widget_field_many2one_qr_cam_bg_success");
                    self.$input.removeClass("rt_widget_field_many2one_qr_cam_bg_danger");
                } else {
                    self.$input.val('');
                    self.$input.autocomplete("close");
                    self.$input.addClass("rt_widget_field_many2one_qr_cam_bg_danger");
                    self.$input.removeClass("rt_widget_field_many2one_qr_cam_bg_success");
                    alert("Record not found for this scanned barcode/QR code: " + detected_barcode_or_qr_code);
                }
            }, m2o_delay);*/

            // update value for many2one field
            // ------------------------------------------------
            // Change Color
            // ----------------
            var random_color = "#" + ("000000" + Math.floor(Math.random() * 16777215).toString(16)).slice(-6);
            var last_scan_result = self.dialog_element.find(".js_cls_rt_widget_field_char_qr_last_scan_result");
            last_scan_result.css({
                "background-color": random_color,
            });
            last_scan_result.html("Last scanned: " + detected_barcode_or_qr_code);
            // Settings Implementation
            var dont_close_dialog = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_close_dialog") || "false";
            var dont_stop_stream = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_stop_stream") || "false";
            var dont_play_audio = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_play_audio") || "false";

            if (dont_play_audio == "false") {
                self.audio_beep.play();
            }

            if (dont_stop_stream == "false") {
                const tracks = self.video.srcObject ? self.video.srcObject.getTracks() : [];
                for (const track of tracks) {
                    track.stop(); //  note that this will also automatically turn the flashlight off
                }
                self.video.srcObject = null;
                self.scan_again_btn.show();
            } else {
                self.scan_again_btn.hide();
            }
            if (dont_close_dialog == "false") {
                self.dialog_object.close();
            }
        },

        /**
         * Run Scan
         * @private
         */
        _run_scan: async function () {

            var self = this;
            var detected_barcode_or_qr_code = false;
            var setting_type_code = localStorage.getItem("rt_widget_field_char_qr_cam_setting_type_code") || "both";

            if (self.video.readyState === self.video.HAVE_ENOUGH_DATA) {
                self.canvas_element.height = self.video.videoHeight;
                self.canvas_element.width = self.video.videoWidth;
                self.canvas.drawImage(self.video, 0, 0, self.canvas_element.width, self.canvas_element.height);
                var imageData = self.canvas.getImageData(0, 0, self.canvas_element.width, self.canvas_element.height);
                /*                var code = await jsQR(imageData.data, imageData.width, imageData.height, {
                    inversionAttempts: "dontInvert",
                });*/

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
                        var fullQuality = self.canvas_element.toDataURL("image/jpeg", 1.0);
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
                                        //var msg = "Incorrect barcode detected! Barcode format is: " + result.codeResult.format + " and Barcode number is: " + result.codeResult.code;
                                        detected_barcode_or_qr_code = result.codeResult.code;

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
            //requestAnimationFrame(self._run_scan());
        },

        /**
         * Open QR scan dialog.
         *
         * @private
         */
        _on_click_rt_widget_field_char_qr_cam_scan_btn: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
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
                self.video = document.querySelector("#rt_widget_field_char_qr_video");
                self.canvas_element = document.querySelector("#rt_widget_field_char_qr_canvas");
                self.canvas = self.canvas_element.getContext("2d");
                var $camera_select = dialog.$el.find("#rt_widget_field_char_qr_cam_select");
                $camera_select.html(self.camera_options);
                self.dialog_element = dialog.$el;
                self.dialog_object = dialog;
                self.scan_again_btn = dialog.$el.find(".js_cls_scan_again_button");
                self.scan_again_btn.hide();
                function tick() {
                    self._run_scan();
                    if (!self.is_searchbar_things_already_done_once) {
                        requestAnimationFrame(tick);
                    }
                }
                self._start_stream().then((value) => {
                    if (value) {
                        tick();
                    }
                });

                dialog.$el.on("change", "#rt_widget_field_char_qr_cam_select", function (ev) {
                    var selected_device_id = $(ev.currentTarget).val();
                    self.constraints = {
                        audio: false,
                        video: {  facingMode: "environment", deviceId: selected_device_id },
                    };
                    localStorage.setItem("rt_widget_field_char_qr_cam_selected_device_id", selected_device_id);
                    const tracks = self.video.srcObject ? self.video.srcObject.getTracks() : [];
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
                        const tracks = self.video.srcObject ? self.video.srcObject.getTracks() : [];
                        for (const track of tracks) {
                            track.stop(); //  note that this will also automatically turn the flashlight off
                        }
                        self.video.srcObject = null;
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
                    self._start_stream().then((value) => {
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

        /**
         * @override
         */
        //init: function () {
        //  this._super.apply(this, arguments);
        //this.additionalContext.hr_timesheet_display_remaining_hours = true;
        // },
        /**
         * @override
         */
        _getDisplayNameWithoutHours: function (value) {
            return value.split(" ‒ ")[0];
        },
        /**
         * @override
         * @private
         */
        _renderEdit: function () {
            var def = this._super.apply(this, arguments);
            //this.$el.addClass("col-10");
            var $ScanButton = $("<a>", {
                title: _t(""),
                href: "",
                class: "d-block mt-1 mb-1 rt_widget_field_char_qr_cam_scan_btn",
                html: $("<small>", { class: "font-weight-bold ml-1", html: "Scan" }),
            });
            $ScanButton.prepend($("<i>", { class: "fa fa-qrcode" }));
            $ScanButton.on("click", this._on_click_rt_widget_field_char_qr_cam_scan_btn.bind(this));
            this.$el = this.$el.add($ScanButton);
            return def;
        },

        //--------------------------------------------------------------------------
        // Widget Many2one Scan Things End
        //--------------------------------------------------------------------------
    });

    /* 
=============================
 Many2one Field
=============================
*/


    /* 
=============================
 Character Field
=============================
*/

    var FieldCharQRCam = basicFields.FieldChar.extend({
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            var self = this;
            self.audio_beep = new Audio("/rt_widget_qr_cam/static/src/audio/beep.mp3");
            self.selected_device_id = localStorage.getItem("rt_widget_field_char_qr_cam_selected_device_id") || false;
            self._get_camera_selection()
                .then((value) => {
                    self.camera_options = value;
                })
                .catch((error) => {
                    console.error("onRejected function called: " + error.message);
                });
            self.constraints = { audio: false, video: { facingMode: "environment"  } };
            self.selected_device_id = localStorage.getItem("rt_widget_field_char_qr_cam_selected_device_id") || false;
            if (self.selected_device_id) {
                self.constraints = {
                    audio: false,
                    video: { facingMode: "environment", deviceId: self.selected_device_id },
                };
            }
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Get Camera Selection.
         * @private
         */
        _get_camera_selection: async function () {
            var self = this;
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter((device) => device.kind === "videoinput");
            const options = videoDevices.map((videoDevice) => {
                var selected = "";
                var deviceId = videoDevice.deviceId || "";
                var label = videoDevice.label || "";
                if (self.selected_device_id == videoDevice.deviceId) {
                    selected = 'selected=""';
                }
                return "<option " + selected + ' value="' + deviceId + '">' + label + "</option>";
            });
            return options.join("");
        },

        /**
         * Start Stream
         * @private
         */
        _start_stream: async function () {
            var self = this;
            let stream = null;
            try {
                stream = await navigator.mediaDevices.getUserMedia(self.constraints);
                self.video.srcObject = stream;
                self.video.setAttribute("playsinline", true); // required to tell iOS safari we don't want fullscreen
                self.video.play();
                /* use the stream */
            } catch (err) {
                /* handle the error */
                console.log(err.name + ": " + err.message);
                var wrap = self.dialog_element.find(".rt_widget_field_char_qr_cam_wrapper");
                if (wrap.length) {
                    var alert_div = '<div class="alert alert-danger" role="alert">' + err.name + ": " + err.message + "</div>";
                    wrap.html(alert_div);
                }
                //return stream;
            }
            return stream;
        },

        _handle_detected_code_rt_widget_qr_cam: async function (detected_barcode_or_qr_code) {
            var self = this;

            self.is_searchbar_things_already_done_once = true;
            // final value
            self.$input.val(detected_barcode_or_qr_code);
            self._onChange();
            // Change Color
            // ----------------
            var random_color = "#" + ("000000" + Math.floor(Math.random() * 16777215).toString(16)).slice(-6);
            var last_scan_result = self.dialog_element.find(".js_cls_rt_widget_field_char_qr_last_scan_result");
            last_scan_result.css({
                "background-color": random_color,
            });
            last_scan_result.html("Last scanned: " + detected_barcode_or_qr_code);
            // Settings Implementation
            var dont_close_dialog = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_close_dialog") || "false";
            var dont_stop_stream = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_stop_stream") || "false";
            var dont_play_audio = localStorage.getItem("rt_widget_field_char_qr_cam_setting_dont_play_audio") || "false";

            if (dont_play_audio == "false") {
                self.audio_beep.play();
            }

            if (dont_stop_stream == "false") {
                const tracks = self.video.srcObject ? self.video.srcObject.getTracks() : [];
                for (const track of tracks) {
                    track.stop(); //  note that this will also automatically turn the flashlight off
                }
                self.video.srcObject = null;
                self.scan_again_btn.show();
            } else {
                self.scan_again_btn.hide();
            }
            if (dont_close_dialog == "false") {
                self.dialog_object.close();
            }
        },

        /**
         * Run Scan
         * @private
         */
        _run_scan: async function () {
            var self = this;
            var detected_barcode_or_qr_code = false;
            var setting_type_code = localStorage.getItem("rt_widget_field_char_qr_cam_setting_type_code") || "both";

            if (self.video.readyState === self.video.HAVE_ENOUGH_DATA) {
                self.canvas_element.height = self.video.videoHeight;
                self.canvas_element.width = self.video.videoWidth;
                self.canvas.drawImage(self.video, 0, 0, self.canvas_element.width, self.canvas_element.height);
                var imageData = self.canvas.getImageData(0, 0, self.canvas_element.width, self.canvas_element.height);
                /*                var code = await jsQR(imageData.data, imageData.width, imageData.height, {
                    inversionAttempts: "dontInvert",
                });*/

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
                        var fullQuality = self.canvas_element.toDataURL("image/jpeg", 1.0);
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
                                        // var msg = "Incorrect barcode detected! Barcode format is: " + result.codeResult.format + " and Barcode number is: " + result.codeResult.code;
                                        detected_barcode_or_qr_code = result.codeResult.code;
 
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
            //requestAnimationFrame(self._run_scan());
        },

        /**
         * Open QR scan dialog.
         *
         * @private
         */
        _on_click_rt_widget_field_char_qr_cam_scan_btn: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
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
                self.video = document.querySelector("#rt_widget_field_char_qr_video");
                self.canvas_element = document.querySelector("#rt_widget_field_char_qr_canvas");
                self.canvas = self.canvas_element.getContext("2d");
                var $camera_select = dialog.$el.find("#rt_widget_field_char_qr_cam_select");
                $camera_select.html(self.camera_options);
                self.dialog_element = dialog.$el;
                self.dialog_object = dialog;
                self.scan_again_btn = dialog.$el.find(".js_cls_scan_again_button");
                self.scan_again_btn.hide();
                function tick() {
                    self._run_scan();
                    if (!self.is_searchbar_things_already_done_once) {
                        requestAnimationFrame(tick);
                    }
                }
                self._start_stream().then((value) => {
                    if (value) {
                        tick();
                    }
                });

                dialog.$el.on("change", "#rt_widget_field_char_qr_cam_select", function (ev) {
                    var selected_device_id = $(ev.currentTarget).val();
                    self.constraints = {
                        audio: false,
                        video: { facingMode: "environment", deviceId: selected_device_id },
                    };
                    localStorage.setItem("rt_widget_field_char_qr_cam_selected_device_id", selected_device_id);
                    const tracks = self.video.srcObject ? self.video.srcObject.getTracks() : [];
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
                        const tracks = self.video.srcObject ? self.video.srcObject.getTracks() : [];
                        for (const track of tracks) {
                            track.stop(); //  note that this will also automatically turn the flashlight off
                        }
                        self.video.srcObject = null;
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
                    self._start_stream().then((value) => {
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

        /**
         * Add a button to open the scan dialog.
         *
         * @override
         * @private
         */
        _renderEdit: function () {
            var def = this._super.apply(this, arguments);
            //this.$el.addClass("col-10");
            var $ScanButton = $("<a>", {
                title: _t(""),
                href: "",
                class: "d-block mt-1 mb-1 rt_widget_field_char_qr_cam_scan_btn",
                html: $("<small>", { class: "font-weight-bold ml-1", html: "Scan" }),
            });
            $ScanButton.prepend($("<i>", { class: "fa fa-qrcode" }));
            $ScanButton.on("click", this._on_click_rt_widget_field_char_qr_cam_scan_btn.bind(this));
            this.$el = this.$el.add($ScanButton);
            return def;
        },
    });

    /* 
=============================
 Character Field
=============================
*/

    fieldRegistry.add("rt_widget_field_char_qr_cam", FieldCharQRCam);
    fieldRegistry.add("rt_widget_field_many2one_qr_cam", FieldMany2OneQRCam);

    return {
        FieldCharQRCam: FieldCharQRCam,
        FieldMany2OneQRCam: FieldMany2OneQRCam,
    };
});
