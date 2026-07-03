package com.goma.app

import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

data class ChatMessage(val sender: String, val text: String, val isUser: Boolean)

class ChatAdapter(private val messages: MutableList<ChatMessage>) :
    RecyclerView.Adapter<ChatAdapter.ViewHolder>() {

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val senderLabel: TextView = view.findViewById(R.id.senderLabel)
        val messageText: TextView = view.findViewById(R.id.messageText)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_message, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val message = messages[position]
        holder.senderLabel.text = message.sender
        holder.messageText.text = message.text

        val gravity = if (message.isUser) Gravity.END else Gravity.START
        (holder.senderLabel.parent as View).let { row ->
            (row as android.widget.LinearLayout).gravity = gravity
        }
        holder.senderLabel.gravity = gravity
        holder.messageText.setBackgroundColor(
            if (message.isUser) 0xFFDCF0FF.toInt() else 0xFFEDEDED.toInt()
        )
    }

    override fun getItemCount(): Int = messages.size

    fun addMessage(message: ChatMessage) {
        messages.add(message)
        notifyItemInserted(messages.size - 1)
    }
}
