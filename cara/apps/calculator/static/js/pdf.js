window.onload = function() {
    document.getElementById("download-pdf")
        .addEventListener("click", () => {
            const pdf_version = this.document.getElementById("body");
            console.log(pdf_version);
            console.log(window);
            var opt = {
                filename: 'myfile.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, letterRendering: true },
                jsPDF: { format: 'a4', orientation: 'portrait' },
            };
            html2pdf().from(pdf_version).set(opt).save();
        })
}