package com.docviewer.mobile.bookmark

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import android.widget.Button
import android.widget.TextView
import com.docviewer.mobile.R

class BookmarkListAdapter(
    private val context: Context,
    private var items: List<Bookmark>,
    private val positionLabel: (Bookmark) -> String,
    private val onClick: (Bookmark) -> Unit,
    private val onEdit: (Bookmark) -> Unit,
    private val onDelete: (Bookmark) -> Unit
) : BaseAdapter() {

    fun submitList(newItems: List<Bookmark>) {
        items = newItems
        notifyDataSetChanged()
    }

    override fun getCount() = items.size
    override fun getItem(position: Int): Bookmark = items[position]
    override fun getItemId(position: Int): Long = items[position].id

    override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
        val view = convertView ?: LayoutInflater.from(context).inflate(R.layout.item_bookmark, parent, false)
        val bookmark = items[position]

        view.findViewById<TextView>(R.id.bookmarkPosition).text = positionLabel(bookmark)

        val memoView = view.findViewById<TextView>(R.id.bookmarkMemo)
        if (bookmark.memo.isBlank()) {
            memoView.visibility = View.GONE
        } else {
            memoView.visibility = View.VISIBLE
            memoView.text = bookmark.memo
        }

        view.setOnClickListener { onClick(bookmark) }
        view.findViewById<Button>(R.id.bookmarkEditButton).setOnClickListener { onEdit(bookmark) }
        view.findViewById<Button>(R.id.bookmarkDeleteButton).setOnClickListener { onDelete(bookmark) }
        return view
    }
}
