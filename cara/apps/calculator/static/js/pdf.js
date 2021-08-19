function execute_me() {
    const pdf_version = this.document.getElementById("body");

    console.log(pdf_version);
    console.log(window);
    var opt = {
        filename: 'myfile.pdf',
        image: { type: 'jpeg', quality: 0.9 },
        html2canvas: { scale: 2, logging: true, dpi: 192, letterRendering: true, width: 1200, windowWidth: 1200 },
        jsPDF: {
            unit: 'mm',
            format: 'a4',
            orientation: 'portrait'
        },
        pagebreak: { mode: 'avoid-all', after: ['#rules', '#results'] }
    };
    html2pdf().set(opt).from(pdf_version).toPdf().get('pdf').then(function(pdf) {
            var totalPages = pdf.internal.getNumberOfPages();
            for (i = 1; i <= totalPages; i++) {
                pdf.setPage(i);
                pdf.setFontSize(10);
                pdf.setTextColor(150);
                pdf.text('Page ' + i + ' of ' + totalPages, (pdf.internal.pageSize.getWidth() / 2.25, (pdf.internal.pageSize.getHeight() - 8)));
            }
        })
        .save();
};