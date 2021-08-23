function execute_me(qr_link) {
    const pdf_version = this.document.getElementById("body");

    // Set height of first page break according to the results div
    const header_height = this.document.getElementById("report-header-div").offsetHeight;
    const results_height = this.document.getElementById("results-div").offsetHeight;
    this.document.getElementById("break-first-page").style.height = (1420 - header_height - results_height) + 'pt';

    // PDF styling
    var opt = {
        filename: 'myfile.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, width: 1200, windowWidth: 1200 },
        enableLinks: false,
        jsPDF: {
            unit: 'pt',
            format: 'letter',
            orientation: 'portrait',
        },
        pagebreak: { mode: '', avoid: '.break-avoid' },
    };
    html2pdf().set(opt).from(pdf_version).toPdf().get('pdf').then(function(pdf) {
        var totalPages = pdf.internal.getNumberOfPages();
        pdf.setPage(1);
        pdf.link(530, 25, 60, 60, { url: qr_link }); //Hyperlink to reproduce results

        for (i = 1; i <= totalPages; i++) {
            pdf.setPage(i);
            pdf.setFontSize(10);
            pdf.setTextColor(150);
            pdf.text('Page ' + i + ' of ' + totalPages, (pdf.internal.pageSize.getWidth() / 2.25), (pdf.internal.pageSize.getHeight() - 10));
        }
    }).save();
};