/**
 * 数据导出工具函数
 * 统一封装 CSV / Excel / PDF 三种格式的导出
 */

import * as XLSX from 'xlsx'
import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'

function escapePdfText(value) {
  return String(value ?? '').replace(/[^\x20-\x7E]/g, char => {
    const code = char.codePointAt(0)
    return code ? `\\u${code.toString(16).padStart(4, '0')}` : ''
  })
}

/**
 * 导出 CSV 文件（带 BOM 支持中文 Excel 打开）
 */
export function exportCSV(headers, rows, filename) {
  const csvContent = '\uFEFF' + [headers, ...rows].map(row =>
    row.map(cell => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(',')
  ).join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  downloadBlob(blob, `${filename}.csv`)
}

/**
 * 导出 Excel 文件
 */
export function exportExcel(headers, rows, filename, sheetName = 'Sheet1') {
  const data = [headers, ...rows]
  const ws = XLSX.utils.aoa_to_sheet(data)

  ws['!cols'] = headers.map((h, i) => {
    const maxLen = Math.max(
      h.length,
      ...rows.map(r => String(r[i] ?? '').length)
    )
    return { wch: Math.min(40, Math.max(10, maxLen + 2)) }
  })

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, sheetName)
  XLSX.writeFile(wb, `${filename}.xlsx`)
}

/**
 * 导出 PDF 文件（支持中文）
 */
export async function exportPDF(headers, rows, filename, title = '') {
  const doc = new jsPDF({ orientation: 'landscape' })
  const normalizeCell = (value) => escapePdfText(value)
  const pdfHeaders = headers.map(normalizeCell)
  const pdfRows = rows.map(row => row.map(normalizeCell))
  const pdfTitle = normalizeCell(title)

  if (pdfTitle) {
    doc.setFontSize(14)
    doc.text(pdfTitle, 14, 15)
  }

  autoTable(doc, {
    head: [pdfHeaders],
    body: pdfRows,
    startY: pdfTitle ? 22 : 10,
    styles: {
      fontSize: 8,
      cellPadding: 2,
      font: 'helvetica',
    },
    headStyles: {
      fillColor: [64, 158, 255],
      fontStyle: 'normal',
    },
    margin: { left: 10, right: 10 },
  })

  doc.save(`${filename}.pdf`)
}

/**
 * 通用 Blob 下载
 */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
