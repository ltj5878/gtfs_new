/**
 * 数据导出工具函数
 * 统一封装 CSV / Excel / PDF 三种格式的导出
 */

import * as XLSX from 'xlsx'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

// 中文字体 Base64 缓存
let _fontBase64 = null
let _fontLoadPromise = null

/**
 * 预加载中文字体（返回 Promise，可多次调用）
 */
function loadChineseFont() {
  if (_fontBase64) return Promise.resolve(_fontBase64)
  if (_fontLoadPromise) return _fontLoadPromise
  _fontLoadPromise = fetch('/fonts/STHeiti-Subset.ttf')
    .then(res => {
      if (!res.ok) throw new Error('font fetch failed')
      return res.arrayBuffer()
    })
    .then(buf => {
      const bytes = new Uint8Array(buf)
      let binary = ''
      for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
      _fontBase64 = btoa(binary)
      return _fontBase64
    })
    .catch(err => {
      console.warn('中文字体加载失败:', err)
      _fontLoadPromise = null // 允许重试
      return null
    })
  return _fontLoadPromise
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
  // 先尝试加载中文字体
  const fontData = await loadChineseFont()

  const doc = new jsPDF({ orientation: 'landscape' })

  // 注册中文字体
  if (fontData) {
    doc.addFileToVFS('STHeiti-Subset.ttf', fontData)
    doc.addFont('STHeiti-Subset.ttf', 'STHeiti', 'normal')
    doc.setFont('STHeiti')
  }

  if (title) {
    doc.setFontSize(14)
    doc.text(title, 14, 15)
  }

  autoTable(doc, {
    head: [headers],
    body: rows,
    startY: title ? 22 : 10,
    styles: {
      fontSize: 8,
      cellPadding: 2,
      font: fontData ? 'STHeiti' : 'helvetica',
    },
    headStyles: { fillColor: [64, 158, 255] },
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
