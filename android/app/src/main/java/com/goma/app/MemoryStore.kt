package com.goma.app

import android.content.Context
import org.json.JSONObject
import java.io.File
import java.time.Instant

data class MemoryEntry(val role: String, val content: String, val timestamp: String)
data class CreationEntry(val type: String, val content: String, val timestamp: String)

object MemoryStore {
    private const val MEMORY_FILE = "memory.jsonl"
    private const val CREATIONS_FILE = "creations.jsonl"

    private fun memoryFile(context: Context) = File(context.filesDir, MEMORY_FILE)
    private fun creationsFile(context: Context) = File(context.filesDir, CREATIONS_FILE)

    fun appendMemory(context: Context, role: String, content: String) {
        val entry = JSONObject()
        entry.put("role", role)
        entry.put("content", content)
        entry.put("timestamp", Instant.now().toString())
        memoryFile(context).appendText(entry.toString() + "\n")
    }

    fun recentMemory(context: Context, limit: Int = 20): List<MemoryEntry> {
        val f = memoryFile(context)
        if (!f.exists()) return emptyList()
        val lines = f.readLines().filter { it.isNotBlank() }
        return lines.takeLast(limit).map {
            val obj = JSONObject(it)
            MemoryEntry(obj.getString("role"), obj.getString("content"), obj.getString("timestamp"))
        }
    }

    fun formatMemoryContext(entries: List<MemoryEntry>): String {
        if (entries.isEmpty()) return "(아직 기억이 없음)"
        return entries.joinToString("\n") { e ->
            val speaker = if (e.role == "user") "사용자" else "GOMA"
            "$speaker: ${e.content}"
        }
    }

    fun appendCreation(context: Context, type: String, content: String) {
        val entry = JSONObject()
        entry.put("type", type)
        entry.put("content", content)
        entry.put("timestamp", Instant.now().toString())
        creationsFile(context).appendText(entry.toString() + "\n")
    }

    fun recentCreations(context: Context, limit: Int = 5): List<CreationEntry> {
        val f = creationsFile(context)
        if (!f.exists()) return emptyList()
        val lines = f.readLines().filter { it.isNotBlank() }
        return lines.takeLast(limit).map {
            val obj = JSONObject(it)
            CreationEntry(obj.getString("type"), obj.getString("content"), obj.getString("timestamp"))
        }
    }
}
