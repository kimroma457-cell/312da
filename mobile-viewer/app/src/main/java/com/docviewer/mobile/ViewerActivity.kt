package com.docviewer.mobile

import android.content.ContentResolver
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.ext.SdkExtensions
import android.provider.OpenableColumns
import android.view.View
import android.webkit.WebView
import android.widget.Button
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.ListView
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.widget.addTextChangedListener
import androidx.lifecycle.lifecycleScope
import com.docviewer.mobile.bookmark.AppDatabase
import com.docviewer.mobile.bookmark.Bookmark
import com.docviewer.mobile.bookmark.BookmarkListAdapter
import com.docviewer.mobile.hwp.HwpToHtmlConverter
import com.docviewer.mobile.pdf.TrackingPdfViewerFragment
import com.github.barteksc.pdfviewer.PDFView
import kotlinx.coroutines.launch
import kr.dogfoot.hwplib.reader.HWPReader
import kr.dogfoot.hwplib.tool.textextractor.TextExtractMethod
import kr.dogfoot.hwplib.tool.textextractor.TextExtractor
import java.util.concurrent.Executors

class ViewerActivity : AppCompatActivity() {

    private enum class Mode { NONE, PDF_FRAGMENT, PDF_LEGACY, HWP }

    private lateinit var pdfView: PDFView
    private lateinit var pdfFragmentContainer: FrameLayout
    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var errorText: TextView

    private lateinit var searchToggleButton: Button
    private lateinit var bookmarkAddButton: Button
    private lateinit var bookmarkListButton: Button

    private lateinit var searchRow: View
    private lateinit var searchInput: EditText
    private lateinit var searchCount: TextView
    private lateinit var searchPrevButton: Button
    private lateinit var searchNextButton: Button
    private lateinit var searchCloseButton: Button

    private var mode: Mode = Mode.NONE
    private var currentUri: Uri? = null
    private var currentDisplayName: String = ""
    private var pdfViewerFragment: TrackingPdfViewerFragment? = null

    private val backgroundExecutor = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private val db by lazy { AppDatabase.get(applicationContext) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_viewer)

        pdfView = findViewById(R.id.pdfView)
        pdfFragmentContainer = findViewById(R.id.pdfFragmentContainer)
        webView = findViewById(R.id.webView)
        progressBar = findViewById(R.id.progressBar)
        errorText = findViewById(R.id.errorText)

        searchToggleButton = findViewById(R.id.searchToggleButton)
        bookmarkAddButton = findViewById(R.id.bookmarkAddButton)
        bookmarkListButton = findViewById(R.id.bookmarkListButton)

        searchRow = findViewById(R.id.searchRow)
        searchInput = findViewById(R.id.searchInput)
        searchCount = findViewById(R.id.searchCount)
        searchPrevButton = findViewById(R.id.searchPrevButton)
        searchNextButton = findViewById(R.id.searchNextButton)
        searchCloseButton = findViewById(R.id.searchCloseButton)

        webView.settings.javaScriptEnabled = false

        bookmarkAddButton.setOnClickListener { onBookmarkAddClicked() }
        bookmarkListButton.setOnClickListener { onBookmarkListClicked() }

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
        currentUri = uri
        currentDisplayName = queryDisplayName(uri) ?: uri.lastPathSegment.orEmpty()

        val mimeType = contentResolver.getType(uri)
        val isPdf = mimeType == "application/pdf" || currentDisplayName.endsWith(".pdf", ignoreCase = true)
        val isHwp = HWP_MIME_TYPES.contains(mimeType) || currentDisplayName.endsWith(".hwp", ignoreCase = true)

        when {
            isPdf -> {
                if (isPdfViewerFragmentSupported()) showPdfWithFragment(uri) else showPdfLegacy(uri)
            }
            isHwp -> showHwp(uri)
            else -> showError(getString(R.string.error_unsupported_type))
        }
    }

    private fun isPdfViewerFragmentSupported(): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return false
        return try {
            SdkExtensions.getExtensionVersion(Build.VERSION_CODES.S) >= 13
        } catch (e: Exception) {
            false
        }
    }

    // --- PDF: official Jetpack viewer (search built in), only on qualifying devices ---
    private fun showPdfWithFragment(uri: Uri) {
        mode = Mode.PDF_FRAGMENT
        pdfFragmentContainer.visibility = View.VISIBLE
        progressBar.visibility = View.VISIBLE
        WindowCompat.setDecorFitsSystemWindows(window, false)

        val fragment = TrackingPdfViewerFragment()
        fragment.onResult = { success ->
            mainHandler.post {
                progressBar.visibility = View.GONE
                if (!success) showError(getString(R.string.error_open_failed))
            }
        }
        pdfViewerFragment = fragment

        val transaction = supportFragmentManager.beginTransaction()
        transaction.replace(R.id.pdfFragmentContainer, fragment, PDF_VIEWER_FRAGMENT_TAG)
        transaction.commitAllowingStateLoss()
        supportFragmentManager.executePendingTransactions()

        fragment.documentUri = uri

        searchToggleButton.visibility = View.VISIBLE
        searchToggleButton.setOnClickListener {
            val active = pdfViewerFragment?.isTextSearchActive == true
            pdfViewerFragment?.isTextSearchActive = !active
        }
        // The official viewer doesn't expose a current-page accessor we could verify
        // from this environment, so bookmarking isn't wired up for this path yet.
        // See the TODO in TrackingPdfViewerFragment (onPdfViewCreated/PdfView public
        // API) before adding it — no reflection or internal APIs.
        bookmarkAddButton.visibility = View.GONE
        bookmarkListButton.visibility = View.GONE
    }

    // --- PDF: bundled fallback renderer (no search), used everywhere else ---
    private fun showPdfLegacy(uri: Uri) {
        mode = Mode.PDF_LEGACY
        pdfView.visibility = View.VISIBLE
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

        searchToggleButton.visibility = View.GONE
    }

    private fun showHwp(uri: Uri) {
        mode = Mode.HWP
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
                    setupHwpSearch()
                }
            }
        }
    }

    private fun setupHwpSearch() {
        searchToggleButton.visibility = View.VISIBLE
        searchToggleButton.setOnClickListener {
            searchRow.visibility = if (searchRow.visibility == View.VISIBLE) View.GONE else View.VISIBLE
            if (searchRow.visibility == View.GONE) {
                webView.clearMatches()
                searchInput.setText("")
            }
        }

        webView.setFindListener { activeMatchOrdinal, numberOfMatches, isDoneCounting ->
            if (isDoneCounting) {
                searchCount.text = if (numberOfMatches == 0) {
                    getString(R.string.search_no_match)
                } else {
                    getString(R.string.search_count_format, activeMatchOrdinal + 1, numberOfMatches)
                }
            }
        }
        searchInput.addTextChangedListener { text ->
            val query = text?.toString().orEmpty()
            if (query.isEmpty()) {
                webView.clearMatches()
                searchCount.text = getString(R.string.search_no_match)
            } else {
                webView.findAllAsync(query)
            }
        }
        searchPrevButton.setOnClickListener { webView.findNext(false) }
        searchNextButton.setOnClickListener { webView.findNext(true) }
        searchCloseButton.setOnClickListener {
            webView.clearMatches()
            searchInput.setText("")
            searchRow.visibility = View.GONE
        }
    }

    // --- Bookmarks ---

    private fun getCurrentPosition(): Int? = when (mode) {
        Mode.PDF_LEGACY -> pdfView.currentPage
        Mode.HWP -> webView.scrollY
        else -> null
    }

    private fun jumpToPosition(position: Int) {
        when (mode) {
            Mode.PDF_LEGACY -> pdfView.jumpTo(position)
            Mode.HWP -> webView.scrollTo(0, position)
            else -> {}
        }
    }

    private fun positionLabel(bookmark: Bookmark): String = when (mode) {
        Mode.PDF_LEGACY -> getString(R.string.bookmark_position_pdf, bookmark.position + 1)
        else -> getString(R.string.bookmark_position_hwp, bookmark.position)
    }

    private fun onBookmarkAddClicked() {
        val uri = currentUri ?: return
        val position = getCurrentPosition()
        if (position == null) {
            Toast.makeText(this, R.string.bookmark_unavailable, Toast.LENGTH_SHORT).show()
            return
        }

        val input = layoutInflater.inflate(R.layout.dialog_bookmark_memo, null) as EditText
        AlertDialog.Builder(this)
            .setTitle(R.string.bookmark_dialog_title)
            .setView(input)
            .setPositiveButton(R.string.save) { _, _ ->
                val bookmark = Bookmark(
                    docUri = uri.toString(),
                    docDisplayName = currentDisplayName,
                    position = position,
                    memo = input.text?.toString().orEmpty(),
                    createdAt = System.currentTimeMillis()
                )
                lifecycleScope.launch {
                    db.bookmarkDao().insert(bookmark)
                    Toast.makeText(this@ViewerActivity, R.string.bookmark_saved, Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private fun onBookmarkListClicked() {
        val uri = currentUri ?: return
        val view = layoutInflater.inflate(R.layout.dialog_bookmark_list, null)
        val listView = view.findViewById<ListView>(R.id.bookmarkListView)
        val emptyText = view.findViewById<TextView>(R.id.bookmarkEmptyText)

        val dialog = AlertDialog.Builder(this)
            .setTitle(R.string.bookmark_list)
            .setView(view)
            .setNegativeButton(R.string.cancel, null)
            .create()

        lateinit var adapter: BookmarkListAdapter
        fun refresh() {
            lifecycleScope.launch {
                val bookmarks = db.bookmarkDao().forDocument(uri.toString())
                emptyText.visibility = if (bookmarks.isEmpty()) View.VISIBLE else View.GONE
                adapter.submitList(bookmarks)
            }
        }

        adapter = BookmarkListAdapter(
            context = this,
            items = emptyList(),
            positionLabel = ::positionLabel,
            onClick = { bookmark ->
                jumpToPosition(bookmark.position)
                dialog.dismiss()
            },
            onDelete = { bookmark ->
                lifecycleScope.launch {
                    db.bookmarkDao().delete(bookmark)
                    refresh()
                }
            }
        )
        listView.adapter = adapter
        refresh()
        dialog.show()
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
        private const val PDF_VIEWER_FRAGMENT_TAG = "pdf_viewer_fragment"
        private val HWP_MIME_TYPES = setOf(
            "application/x-hwp",
            "application/haansofthwp",
            "application/vnd.hancom.hwp"
        )
    }
}
