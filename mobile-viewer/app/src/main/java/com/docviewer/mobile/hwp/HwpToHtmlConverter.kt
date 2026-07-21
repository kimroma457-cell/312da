package com.docviewer.mobile.hwp

import kr.dogfoot.hwplib.`object`.HWPFile
import kr.dogfoot.hwplib.`object`.bodytext.Section
import kr.dogfoot.hwplib.`object`.bodytext.control.ControlTable
import kr.dogfoot.hwplib.`object`.bodytext.control.table.Cell
import kr.dogfoot.hwplib.`object`.bodytext.control.table.Row
import kr.dogfoot.hwplib.`object`.bodytext.paragraph.Paragraph
import kr.dogfoot.hwplib.`object`.bodytext.paragraph.ParagraphList

/**
 * Renders an HWPFile's paragraph and table structure as HTML for display in a WebView.
 * Inline character formatting (bold/italic/color) and embedded images are not reproduced;
 * only paragraph breaks and table layout are preserved.
 */
object HwpToHtmlConverter {

    fun convert(hwpFile: HWPFile): String {
        val body = StringBuilder()
        for (section: Section in hwpFile.bodyText.sectionList) {
            appendSection(body, section)
        }
        return """
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body { font-family: sans-serif; font-size: 16px; line-height: 1.6; padding: 16px; word-break: break-word; }
                    p { margin: 0 0 10px 0; white-space: pre-wrap; }
                    table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                    td { border: 1px solid #999; padding: 6px; vertical-align: top; }
                </style>
            </head>
            <body>
            $body
            </body>
            </html>
        """.trimIndent()
    }

    private fun appendSection(sb: StringBuilder, section: Section) {
        val count = section.paragraphCount
        for (i in 0 until count) {
            appendParagraph(sb, section.getParagraph(i))
        }
    }

    private fun appendParagraph(sb: StringBuilder, paragraph: Paragraph) {
        paragraph.controlList?.filterIsInstance<ControlTable>()?.forEach { table ->
            appendTable(sb, table)
        }

        val text = paragraph.normalString.orEmpty()
        if (text.isBlank()) {
            sb.append("<p>&nbsp;</p>\n")
        } else {
            sb.append("<p>").append(escapeHtml(text)).append("</p>\n")
        }
    }

    private fun appendTable(sb: StringBuilder, table: ControlTable) {
        sb.append("<table>\n")
        for (row: Row in table.rowList) {
            sb.append("<tr>")
            for (cell: Cell in row.cellList) {
                sb.append("<td>")
                appendParagraphList(sb, cell.paragraphList)
                sb.append("</td>")
            }
            sb.append("</tr>\n")
        }
        sb.append("</table>\n")
    }

    private fun appendParagraphList(sb: StringBuilder, list: ParagraphList) {
        val count = list.paragraphCount
        for (i in 0 until count) {
            appendParagraph(sb, list.getParagraph(i))
        }
    }

    private fun escapeHtml(text: String): String {
        return text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
    }
}
