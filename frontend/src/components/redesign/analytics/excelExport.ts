import ExcelJS from 'exceljs';
import html2canvas from 'html2canvas';

// ─── Style helpers ────────────────────────────────────────────────────────
const headerFill: ExcelJS.Fill = {
  type: 'pattern',
  pattern: 'solid',
  fgColor: { argb: 'FF1E293B' },
};
const headerFont: Partial<ExcelJS.Font> = {
  bold: true,
  color: { argb: 'FFE0F2FE' },
  size: 11,
};
const titleFont: Partial<ExcelJS.Font> = {
  bold: true,
  size: 16,
  color: { argb: 'FF0F172A' },
};

function applyHeader(row: ExcelJS.Row): void {
  row.eachCell((cell) => {
    cell.fill = headerFill;
    cell.font = headerFont;
    cell.alignment = { vertical: 'middle', horizontal: 'left' };
    cell.border = {
      bottom: { style: 'thin', color: { argb: 'FF94A3B8' } },
    };
  });
}

function autoFitColumns(ws: ExcelJS.Worksheet): void {
  ws.columns.forEach((col) => {
    let max = 10;
    col.eachCell?.({ includeEmpty: false }, (cell) => {
      const len = String(cell.value ?? '').length;
      if (len > max) max = len;
    });
    col.width = Math.min(max + 2, 60);
  });
}

// ─── Public types ─────────────────────────────────────────────────────────
export interface ExcelSummaryRow {
  label: string;
  value: string | number;
}

export interface ExcelTrendRow {
  time: string;
  pm25?: number;
  temperature?: number;
  humidity?: number;
  co2?: number;
  noise?: number;
}

export interface ExcelChartCapture {
  /** Sheet name to render the chart on. */
  sheetName: string;
  /** DOM element that contains the chart (usually the chart-card root). */
  element: HTMLElement;
  /** Title row text rendered above the image. */
  title: string;
}

export interface BuildAnalyticsExcelOptions {
  title: string;
  subtitle: string;
  scopeLabel: string;
  timeRangeLabel: string;
  summary: ExcelSummaryRow[];
  trend: ExcelTrendRow[];
  charts: ExcelChartCapture[];
}

// ─── Capture a DOM element to PNG using html2canvas ───────────────────────
async function captureToPng(el: HTMLElement): Promise<{ buffer: ArrayBuffer; w: number; h: number } | null> {
  try {
    const canvas = await html2canvas(el, {
      backgroundColor: '#1E293B',
      scale: 1.5,
      useCORS: true,
      logging: false,
    });
    const dataUrl = canvas.toDataURL('image/png');
    const base64 = dataUrl.split(',')[1];
    const binary = atob(base64);
    const buffer = new ArrayBuffer(binary.length);
    const view = new Uint8Array(buffer);
    for (let i = 0; i < binary.length; i++) view[i] = binary.charCodeAt(i);
    return { buffer, w: canvas.width, h: canvas.height };
  } catch (e) {
    console.error('Chart capture failed:', e);
    return null;
  }
}

// ─── Main builder ─────────────────────────────────────────────────────────
export async function buildAnalyticsExcel(opts: BuildAnalyticsExcelOptions): Promise<ExcelJS.Workbook> {
  const wb = new ExcelJS.Workbook();
  wb.creator = 'Smart City IoT Dashboard';
  wb.created = new Date();

  // ─── Sheet 1: Tóm Tắt ───
  const sumWs = wb.addWorksheet('Tóm Tắt');
  sumWs.mergeCells('A1:B1');
  sumWs.getCell('A1').value = opts.title;
  sumWs.getCell('A1').font = titleFont;
  sumWs.getCell('A1').fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE0F2FE' } };
  sumWs.getCell('A1').alignment = { vertical: 'middle', horizontal: 'center' };
  sumWs.getRow(1).height = 28;

  sumWs.mergeCells('A2:B2');
  sumWs.getCell('A2').value = opts.subtitle;
  sumWs.getCell('A2').font = { italic: true, color: { argb: 'FF475569' }, size: 11 };
  sumWs.getCell('A2').alignment = { horizontal: 'center' };

  const headerRow = sumWs.addRow(['Chỉ số', 'Giá trị']);
  applyHeader(headerRow);

  for (const r of opts.summary) {
    const row = sumWs.addRow([r.label, r.value]);
    row.getCell(1).font = { bold: true };
    row.eachCell((cell) => {
      cell.border = { bottom: { style: 'hair', color: { argb: 'FFCBD5E1' } } };
    });
  }
  autoFitColumns(sumWs);

  // ─── Sheet 2: Xu Hướng (data table) ───
  const trendWs = wb.addWorksheet(`Xu Hướng (${opts.timeRangeLabel})`);
  const trendHeader = trendWs.addRow([
    'Thời điểm',
    'PM2.5 (µg/m³)',
    'Nhiệt độ (°C)',
    'Độ ẩm (%)',
    'CO₂ (ppm)',
    'Tiếng ồn (dB)',
  ]);
  applyHeader(trendHeader);
  for (const r of opts.trend) {
    trendWs.addRow([
      r.time,
      r.pm25 !== undefined ? +r.pm25.toFixed(1) : '',
      r.temperature !== undefined ? +r.temperature.toFixed(1) : '',
      r.humidity !== undefined ? +r.humidity.toFixed(0) : '',
      r.co2 !== undefined ? Math.round(r.co2) : '',
      r.noise !== undefined ? +r.noise.toFixed(1) : '',
    ]);
  }
  autoFitColumns(trendWs);
  trendWs.views = [{ state: 'frozen', ySplit: 1 }];

  // ─── Sheet 3+: Charts (one chart per sheet) ───
  for (const chart of opts.charts) {
    const captured = await captureToPng(chart.element);
    if (!captured) continue;

    // Excel has a 31-char sheet name limit and disallows : / \ ? * [ ]
    const safeName = chart.sheetName.replace(/[:/\\?*[\]]/g, '-').slice(0, 31);
    const ws = wb.addWorksheet(safeName);
    ws.mergeCells('A1:H1');
    ws.getCell('A1').value = chart.title;
    ws.getCell('A1').font = titleFont;
    ws.getCell('A1').alignment = { horizontal: 'center', vertical: 'middle' };
    ws.getRow(1).height = 26;

    const imgId = wb.addImage({ buffer: captured.buffer, extension: 'png' });
    // Aim for ~700-pixel-wide rendering.
    const targetW = Math.min(900, captured.w);
    const ratio = targetW / captured.w;
    ws.addImage(imgId, {
      tl: { col: 0, row: 2 },
      ext: { width: targetW, height: captured.h * ratio },
    });
  }

  return wb;
}

export async function downloadWorkbook(wb: ExcelJS.Workbook, filename: string): Promise<void> {
  const buffer = await wb.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
