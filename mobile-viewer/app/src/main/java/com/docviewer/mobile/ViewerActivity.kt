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
    private lateinit var errorContainer: View
    private lateinit var errorText: TextView
    private lateinit var reselectButton: Button

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

    // Position to jump back to once content finishes loading; populated either from
    // savedInstanceState (process death) or left null on a normal cold start.
    private var pendingRestorePosition: Int? = null

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
        errorContainer = findViewById(R.id.errorContainer)
        errorText = findViewById(R.id.errorText)
        reselectButton = findViewById(R.id.reselectButton)

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
        reselectButton.setOnClickListener {
            startActivity(Intent(this, MainActivity::class.java))
            finish()
        }

        // Prefer the URI we saved ourselves (survives process death); fall back to
        // resolving it fresh from the launching Intent on a normal cold start.
        val uri = savedInstanceState?.let { restoredUri(it) } ?: resolveUri(intent)
        if (uri == null) {
            showError(getString(R.string.error_no_file), allowReselect = true)
            return
        }
        pendingRestorePosition = savedInstanceState?.takeIf { it.containsKey(STATE_POSITION) }
            ?.getInt(STATE_POSITION)

        openFile(uri)
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        currentUri?.let { outState.putParcelable(STATE_URI, it) }
        getCurrentPosition()?.let { outState.putInt(STATE_POSITION, it) }
    }

    private fun resolveUri(intent: Intent?): Uri? {
        if (intent == null) return null
        return when (intent.action) {
            Intent.ACTION_SEND -> intent.getParcelableExtra(Intent.EXTRA_STREAM)
            else -> intent.data
        }
    }

    private fun restoredUri(bundle: Bundle): Uri? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            bundle.getParcelable(STATE_URI, Uri::class.java)
        } else {
            @Suppress("DEPRECATION")
            bundle.getParcelable(STATE_URI)
        }
    }

    private fun openFile(uri: Uri) {
        currentUri = uri

        val (displayName, mimeType) = try {
            (queryDisplayName(uri) ?: uri.lastPathSegment.orEmpty()) to contentResolver.getType(uri)
        } catch (e: SecurityException) {
            showError(getString(R.string.error_permission_expired), allowReselect = true)
            return
        } catch (e: Exception) {
            showError(getString(R.string.error_open_failed), allowReselect = true)
            return
        }
        currentDisplayName = displayName

        val isPdf = mimeType == "application/pdf" || displayName.endsWith(".pdf", ignoreCase = true)
        val isHwp = (mimeType != null && mimeType in HWP_MIME_TYPES) || displayName.endsWith(".hwp", ignoreCase = true)

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

    private fun isPermissionError(error: Throwable?): Boolean {
        return error is SecurityException || error?.cause is SecurityException
    }

    // --- PDF: official Jetpack viewer (search built in), only on qualifying devices ---
    private fun showPdfWithFragment(uri: Uri) {
        mode = Mode.PDF_FRAGMENT
        pdfFragmentContainer.visibility = View.VISIBLE
        progressBar.visibility = View.VISIBLE
        WindowCompat.setDecorFitsSystemWindows(window, false)

        val fragment = TrackingPdfViewerFragment()
        fragment.onResult = { error ->
            mainHandler.post {
                progressBar.visibility = View.GONE
                if (error != null) {
                    if (isPermissionError(error)) {
                        showError(getString(R.string.error_permission_expired), allowReselect = true)
                    } else {
                        showError(getString(R.string.error_open_failed))
                    }
                }
            }
        }
        pdfViewerFragment = fragment

        val transaction = supportFragmentManager.beginTransaction()
        transaction.replace(R.id.pdfFragmentContainer, fragment, PDF_VIEWER_FRAGMENT_TAG)
        transaction.commitAllowingStateLoss()
        supportFragmentManager.executePendingTransactions()

        try {
            fragment.documentUri = uri
        } catch (e: SecurityException) {
            progressBar.visibility = View.GONE
            showError(getString(R.string.error_permission_expired), allowReselect = true)
            return
        }

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
                pendingRestorePosition?.let { pdfView.jumpTo(it) }
                pendingRestorePosition = null
            }
            .onError { throwable ->
                progressBar.visibility = View.GONE
                if (isPermissionError(throwable)) {
                    showError(getString(R.string.error_permission_expired), allowReselect = true)
                } else {
                    showError(getString(R.string.error_open_failed))
                }
            }
            .load()

        searchToggleButton.visibility = View.GONE
    }

    private fun showHwp(uri: Uri) {
        mode = Mode.HWP
        progressBar.visibility = View.VISIBLE
        backgroundExecutor.execute {
            var permissionError = false
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
            } catch (e: SecurityException) {
                permissionError = true
                null
            } catch (e: Exception) {
                null
            }
            mainHandler.post {
                progressBar.visibility = View.GONE
                if (html == null) {
                    if (permissionError) {
                        showError(getString(R.string.error_permission_expired), allowReselect = true)
                    } else {
                        showError(getString(R.string.error_open_failed))
                    }
                } else {
                    webView.visibility = View.VISIBLE
                    webView.loadDataWithBaseURL(null, html, "text/html", "utf-8", null)
                    setupHwpSearch()
                    pendingRestorePosition?.let { y -> webView.post { webView.scrollTo(0, y) } }
                    pendingRestorePosition = null
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
    // Keyed by the full content Uri string (not filename), so two different files
    // that happen to share a display name never share bookmarks, and the same file
    // opened via two different apps/paths (different Uris) is tracked separately
    // rather than risking an incorrect merge.

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
                    memo = normalizeMemo(input.text?.toString().orEmpty()),
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
            onEdit = { bookmark -> showEditMemoDialog(bookmark, ::refresh) },
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

    // Pre-fills the existing memo; Cancel leaves the stored bookmark untouched.
    // Save only updates the memo/updatedAt columns (BookmarkDao.updateMemo) —
    // id, docUri, position and createdAt are never touched.
    private fun showEditMemoDialog(bookmark: Bookmark, onSaved: () -> Unit) {
        val input = layoutInflater.inflate(R.layout.dialog_bookmark_memo, null) as EditText
        input.setText(bookmark.memo)
        AlertDialog.Builder(this)
            .setTitle(R.string.bookmark_edit_dialog_title)
            .setView(input)
            .setPositiveButton(R.string.save) { _, _ ->
                val memo = normalizeMemo(input.text?.toString().orEmpty())
                lifecycleScope.launch {
                    db.bookmarkDao().updateMemo(bookmark.id, memo, System.currentTimeMillis())
                    Toast.makeText(this@ViewerActivity, R.string.bookmark_updated, Toast.LENGTH_SHORT).show()
                    onSaved()
                }
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    // Empty memos are allowed as-is; a whitespace-only memo is normalized to "".
    private fun normalizeMemo(raw: String): String = if (raw.isBlank()) "" else raw

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

    private fun showError(message: String, allowReselect: Boolean = false) {
        errorText.text = message
        errorContainer.visibility = View.VISIBLE
        reselectButton.visibility = if (allowReselect) View.VISIBLE else View.GONE
    }

    override fun onDestroy() {
        super.onDestroy()
        backgroundExecutor.shutdown()
    }

    companion object {
        private const val PDF_VIEWER_FRAGMENT_TAG = "pdf_viewer_fragment"
        private const val STATE_URI = "state_uri"
        private const val STATE_POSITION = "state_position"
        private val HWP_MIME_TYPES = setOf(
            "application/x-hwp",
            "application/haansofthwp",
            "application/vnd.hancom.hwp"
        )
    }
}
