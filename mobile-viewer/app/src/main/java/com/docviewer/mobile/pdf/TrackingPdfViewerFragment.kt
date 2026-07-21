package com.docviewer.mobile.pdf

import android.os.Build
import androidx.annotation.RequiresExtension
import androidx.pdf.viewer.fragment.PdfViewerFragment

/**
 * Thin subclass so we can observe document load success/failure; PdfViewerFragment
 * only exposes these as overridable protected methods, not a settable listener.
 * Must keep a no-arg constructor since the system can recreate fragments via reflection.
 */
@RequiresExtension(extension = Build.VERSION_CODES.S, version = 13)
class TrackingPdfViewerFragment : PdfViewerFragment() {

    var onResult: ((success: Boolean) -> Unit)? = null

    override fun onLoadDocumentSuccess() {
        onResult?.invoke(true)
    }

    override fun onLoadDocumentError(error: Throwable) {
        onResult?.invoke(false)
    }

    // TODO(bookmarks-for-official-viewer): PdfViewerFragment reportedly exposes
    // `onPdfViewCreated(pdfView: PdfView)`. Once Gradle can actually sync this
    // artifact, check PdfView's public API for a way to read the current /
    // visible page (e.g. something like getCurrentPage() or a visible-page-range
    // getter). If — and only if — a genuine public API gives us that, wire up
    // ViewerActivity.getCurrentPosition()/jumpToPosition() for Mode.PDF_FRAGMENT
    // and un-hide bookmarkAddButton/bookmarkListButton there. Do not use
    // reflection or any internal/non-public API to fake this.
}
