#!/bin/sh

barcode -t 2x7+40+40 -m 40x20 -p "210x297mm" -e code128b -n > barcodes_TMP_FILE.ps  << BARCODES
O-BTN.pause
O-BTN.next
O-BTN.prev
O-BTN.skip
O-BTN.cloWO
O-BTN.cloMO
O-BTN.pass
O-BTN.fail
O-BTN.finish
O-BTN.record
BARCODES

cat > barcodesHeaders_TMP_FILE.ps << HEADER
/showTitle { /Helvetica findfont 12 scalefont setfont moveto show } def
(CONTINUE/PAUSE) 79 780 showTitle
(VALIDATE/NEXT) 336 780 showTitle
(PREVIOUS) 79 672 showTitle
(SKIP) 336 672 showTitle
(MARK AS DONE) 79 565 showTitle
(MARK AS DONE AND CLOSE MO) 336 565 showTitle
(PASS) 79 456 showTitle
(FAIL) 336 456 showTitle
(FINISH STEPS) 79 347 showTitle
(RECORD PRODUCTION) 336 347 showTitle
HEADER

cat barcodesHeaders_TMP_FILE.ps barcodes_TMP_FILE.ps | ps2pdf - - > barcodes_actions_Manufacturing.pdf
rm barcodesHeaders_TMP_FILE.ps barcodes_TMP_FILE.ps
