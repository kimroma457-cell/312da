package com.docviewer.mobile

import android.content.ContentResolver
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.OpenableColumns
import android.view.View
import android.webkit.WebView
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.docviewer.mobile.hwp.HwpToHtmlConverter
import com.github.barteksc.pdfviewer.PDFView
import kr.dogfoot.hwplib.reader.HWPReader
import kr.dogfoot.hwplib.tool.textextractor.TextExtractMethod
import kr.dogfoot.hwplib.tool.textextractor.TextExtractor
import java.util.concurrent.Executors

class ViewerActivity : AppCompatActivity() {

    private lateinit var pdfView: PDFView
    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var errorText: TextView

    private val backgroundExecutor = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_viewer)

        pdfView = findViewById(R.id.pdfView)
        webView = findViewById(R.id.webView)
        progressBar = findViewById(R.id.progressBar)
        errorText = findViewById(R.id.errorText)
        webView.settings.javaScriptEnabled = false

        val uri = resolveUri(intent)
        if (uri == null) {
            showError(getString(R.string.error_no_file))
            return
        }
        openFile(uri)
    }

    private fun resolveUri(intent: Intent?): Uri? {
        if (intent == null) return null
        return when (intent.action) {
            Intent.ACTION_SEND -> intent.getParcelableExtra(Intent.EXTRA_STREAM)
            else -> intent.data
        }
    }

    private fun openFile(uri: Uri) {
        val displayName = queryDisplayName(uri) ?: uri.lastPathSegment.orEmpty()
        val mimeType = contentResolver.getType(uri)
        val isPdf = mimeType == "application/pdf" || displayName.endsWith(".pdf", ignoreCase = true)
        val isHwp = HWP_MIME_TYPES.contains(mimeType) || displayName.endsWith(".hwp", ignoreCase = true)

        when {
            isPdf -> showPdf(uri)
            isHwp -> showHwp(uri)
            else -> showError(getString(R.string.error_unsupported_type))
        }
    }

    private fun showPdf(uri: Uri) {
        progressBar.visibility = View.VISIBLE
        pdfView.fromUri(uri)
            .onLoad {
                progressBar.visibility = View.GONE
                pdfView.visibility = View.VISIBLE
            }
            .onError {
                progressBar.visibility = View.GONE
                showError(getString(R.string.error_open_failed))
            }
            .load()
    }

    private fun showHwp(uri: Uri) {
        progressBar.visibility = View.VISIBLE
        backgroundExecutor.execute {
            val html = try {
                contentResolver.openInputStream(uri)?.use { input ->
                    val hwpFile = HWPReader.fromInputStream(input)
                    try {
                        HwpToHtmlConverter.convert(hwpFile)
                    } catch (e: Exception) {
                        plainTextHtml(
                            TextExtractor.extract(hwpFile, TextExtractMethod.InsertControlTextBetweenParagraphText)
                        )
                    }
                }
            } catch (e: Exception) {
                null
            }
            mainHandler.post {
                progressBar.visibility = View.GONE
                if (html == null) {
                    showError(getString(R.string.error_open_failed))
                } else {
                    webView.visibility = View.VISIBLE
                    webView.loadDataWithBaseURL(null, html, "text/html", "utf-8", null)
                }
            }
        }
    }

    private fun plainTextHtml(text: String): String {
        val escaped = text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        return "<html><body style=\"font-family:sans-serif;padding:16px;\">$escaped</body></html>"
    }

    private fun queryDisplayName(uri: Uri): String? {
        if (uri.scheme != ContentResolver.SCHEME_CONTENT) return uri.lastPathSegment
        return contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (idx >= 0) cursor.getString(idx) else null
            } else {
                null
            }
        }
    }

    private fun showError(message: String) {
        errorText.text = message
        errorText.visibility = View.VISIBLE
    }

    override fun onDestroy() {
        super.onDestroy()
        backgroundExecutor.shutdown()
    }

    companion object {
        private val HWP_MIME_TYPES = setOf(
            "application/x-hwp",
            "application/haansofthwp",
            "application/vnd.hancom.hwp"
        )
    }
}
