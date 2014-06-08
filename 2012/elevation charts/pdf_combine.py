from pyPdf import PdfFileWriter, PdfFileReader

output_file_name = "RAAM2012-Grade.pdf"
h_output = PdfFileWriter()

for TS in range(1,56):
    input_file_name = "TS%s.pdf"%(TS)
    print(input_file_name)
    h_input = PdfFileReader(file(input_file_name, "rb"))

    # add page 1 from input1 to output document, unchanged
    h_output.addPage(h_input.getPage(0))

# finally, write "output" to document-output.pdf
outputStream = file(output_file_name, "wb")
h_output.write(outputStream)
outputStream.close()
