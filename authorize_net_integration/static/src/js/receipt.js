odoo.define('authorize_net_integration.receipt', function (require) {
"use strict";
    $(document).ready(function() {
        $('.receipt').each(function(){
            $("#print").click(function(){
                var mywindow = window.open('', 'PRINT', 'height=400,width=600');
                mywindow.document.write('<html><head><title>' + document.title  + '</title>');
                mywindow.document.write('</head><body >');
//                mywindow.document.write("<img src='/authorize_net_integration/static/src/img/ed_logo.png'/>");
                mywindow.document.write("<h1 style='text-align:center;'>Payment Receipt</h1>");
                var data=$('<div/>').append($('#receipt').clone()).html()
                mywindow.document.write(data);
                mywindow.document.write('</body></html>');

                mywindow.document.close();
                mywindow.focus();

                mywindow.print();
                mywindow.close();


             });
        });
    });

});