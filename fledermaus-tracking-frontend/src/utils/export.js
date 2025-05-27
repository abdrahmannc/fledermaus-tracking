export function exportAsCSV(data) {
  const csv = data.map(row => Object.values(row).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  downloadBlob(blob, "results.csv");
}

export function exportAsJSON(data) {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  downloadBlob(blob, "results.json");
}

export function exportAsPDF(data) {
  // Einfacher PDF-Export – z. B. nur Text
  const text = JSON.stringify(data, null, 2);
  const blob = new Blob([text], { type: "application/pdf" });
  downloadBlob(blob, "results.pdf");
}

export function exportAsPNG(canvasRef) {
  if (!canvasRef?.current) return;
  const link = document.createElement("a");
  link.download = "chart.png";
  link.href = canvasRef.current.toDataURL("image/png");
  link.click();
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}


export function exportAsPDFs() {
    alert("worked")
}