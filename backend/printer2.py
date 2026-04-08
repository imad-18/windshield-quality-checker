import win32print

# Get your Zebra printer name (important)
printer_name = win32print.GetDefaultPrinter()
# OR manually set it:
# printer_name = "ZDesigner ZT411-203dpi ZPL"

zpl = "^XA^FO300,100^BQN,2,6^FDLA,Hello World^FS^XZ"

hPrinter = win32print.OpenPrinter(printer_name)

try:
    hJob = win32print.StartDocPrinter(hPrinter, 1, ("ZPL Label", None, "RAW"))
    win32print.StartPagePrinter(hPrinter)
    win32print.WritePrinter(hPrinter, zpl.encode())
    win32print.EndPagePrinter(hPrinter)
    win32print.EndDocPrinter(hPrinter)
finally:
    win32print.ClosePrinter(hPrinter)