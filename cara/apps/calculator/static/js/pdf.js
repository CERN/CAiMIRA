function execute_me() {
    const pdf_version = this.document.getElementById("body");

    console.log(pdf_version);
    console.log(window);
    var opt = {
        filename: 'myfile.pdf',
        image: { type: 'jpeg', quality: 0.9 },
        html2canvas: { scale: 2, width: 1200, windowWidth: 1200 },
        jsPDF: {
            format: 'a4',
            orientation: 'portrait'
        },
        pagebreak: { after: '.page-break' }
    };
    const pdf = html2pdf().set(opt).from(pdf_version).outputImg().save();
};