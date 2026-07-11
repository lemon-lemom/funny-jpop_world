// 書き出し: SVG → Canvas → PNG / 印刷

export function downloadPNG(container, filename = "score.png") {
  const svg = container.querySelector("svg");
  if (!svg) return;
  const xml = new XMLSerializer().serializeToString(svg);
  const svg64 = btoa(unescape(encodeURIComponent(xml)));
  const w = (svg.width && svg.width.baseVal && svg.width.baseVal.value) || 1000;
  const h = (svg.height && svg.height.baseVal && svg.height.baseVal.value) || 600;
  const img = new Image();
  img.onload = () => {
    const scale = 2;
    const canvas = document.createElement("canvas");
    canvas.width = w * scale;
    canvas.height = h * scale;
    const cctx = canvas.getContext("2d");
    cctx.fillStyle = "#ffffff";
    cctx.fillRect(0, 0, canvas.width, canvas.height);
    cctx.scale(scale, scale);
    cctx.drawImage(img, 0, 0);
    canvas.toBlob((blob) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    });
  };
  img.src = "data:image/svg+xml;base64," + svg64;
}

export function printScore() {
  window.print();
}
