import React, { useEffect, useRef } from "react";
import * as pdfjsLib from "pdfjs-dist";
import type { PDFDocumentProxy, PDFPageProxy } from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { motion } from "framer-motion";

(pdfjsLib as any).GlobalWorkerOptions.workerSrc = workerUrl;

type Props = {
  file: File;
  highlightPage: number | null;   // 0-based; null => first page
  boxes?: number[][];              // [[x0,y0,x1,y1]] in PyMuPDF coords (TOP-LEFT origin)
  pageW?: number;                  // PDF page width in points (backend page.rect.width)
  pageH?: number;                  // PDF page height in points (backend page.rect.height)
};

export default function PdfViewer({ file, highlightPage, boxes = [], pageW, pageH }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let cancelled = false;

    const render = async () => {
      try {
        const data = await file.arrayBuffer();
        const loadingTask = (pdfjsLib as any).getDocument({ data });
        const pdf: PDFDocumentProxy = await loadingTask.promise;
        if (cancelled) return;

        const pageIndex = Math.max(0, Math.min((highlightPage ?? 0), pdf.numPages - 1));
        const page: PDFPageProxy = await pdf.getPage(pageIndex + 1);

        // pdf.js handles rotation internally; viewport is in CSS pixels.
        const viewport = page.getViewport({ scale: 1.5 });
        const canvas = canvasRef.current!;
        const ctx = canvas.getContext("2d")!;
        canvas.width  = Math.ceil(viewport.width);
        canvas.height = Math.ceil(viewport.height);

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        await page.render({ canvasContext: ctx, viewport } as any).promise;

        // ✅ Correct mapping: PyMuPDF boxes are TOP-LEFT; we only scale.
        if (!cancelled && boxes.length > 0 && pageW && pageH) {
          const scaleX = canvas.width  / pageW;
          const scaleY = canvas.height / pageH;

          ctx.save();
          ctx.lineWidth   = Math.max(2, 2 / Math.max(scaleX, scaleY));
          ctx.strokeStyle = "rgba(34,197,94,1)";
          ctx.fillStyle   = "rgba(34,197,94,0.18)";

          for (const [x0, y0, x1, y1] of boxes) {
            const left = x0 * scaleX;
            const top  = y0 * scaleY;          // no flip (TOP-LEFT origin)
            const w    = (x1 - x0) * scaleX;
            const h    = (y1 - y0) * scaleY;
            if (w <= 0 || h <= 0) continue;

            ctx.beginPath();
            ctx.rect(left, top, w, h);
            ctx.fill();
            ctx.stroke();
          }
          ctx.restore();
        }
      } catch (err) {
        console.error("PDF render error:", err);
      }
    };

    render();
    return () => { cancelled = true; };
  }, [file, highlightPage, JSON.stringify(boxes), pageW, pageH]);

  return (
    <motion.canvas
      ref={canvasRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.25 }}
      className="pdf-canvas"
      style={{ display: "block" }}
    />
  );
}
