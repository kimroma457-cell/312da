package com.goma.app

import android.content.Context
import android.content.SharedPreferences
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.view.Menu
import android.view.MenuItem
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.Toolbar
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {

    companion object {
        private const val REFLECT_EVERY = 6
        private const val PREFS = "goma_prefs"
        private const val KEY_API_KEY = "api_key"
    }

    private lateinit var prefs: SharedPreferences
    private lateinit var identity: Identity
    private lateinit var adapter: ChatAdapter
    private lateinit var tts: TextToSpeech
    private val executor: ExecutorService = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        identity = Identity.load(this)

        val toolbar = findViewById<Toolbar>(R.id.toolbar)
        setSupportActionBar(toolbar)
        updateTitle()

        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts.language = Locale.KOREAN
            }
        }

        adapter = ChatAdapter(mutableListOf())
        val recyclerView = findViewById<RecyclerView>(R.id.messageList)
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter

        val inputText = findViewById<EditText>(R.id.inputText)
        val sendButton = findViewById<Button>(R.id.sendButton)

        sendButton.setOnClickListener {
            val text = inputText.text.toString().trim()
            if (text.isEmpty()) return@setOnClickListener
            inputText.setText("")
            sendMessage(text)
        }

        if (apiKey().isEmpty()) {
            promptForApiKey()
        }
    }

    override fun onDestroy() {
        tts.shutdown()
        super.onDestroy()
    }

    private fun apiKey(): String = prefs.getString(KEY_API_KEY, "") ?: ""

    private fun updateTitle() {
        supportActionBar?.title = "GOMA"
        supportActionBar?.subtitle = "${identity.growthStage} · 대화 ${identity.interactionCount}회"
    }

    private fun promptForApiKey() {
        val input = EditText(this)
        input.hint = "sk-ant-..."
        AlertDialog.Builder(this)
            .setTitle("Anthropic API 키 입력")
            .setMessage("GOMA와 대화하려면 본인의 Anthropic API 키가 필요합니다. 이 키는 이 기기에만 저장됩니다.")
            .setView(input)
            .setCancelable(false)
            .setPositiveButton("저장") { _, _ ->
                val key = input.text.toString().trim()
                prefs.edit().putString(KEY_API_KEY, key).apply()
                if (key.isEmpty()) {
                    Toast.makeText(this, "API 키가 없으면 GOMA와 대화할 수 없습니다.", Toast.LENGTH_LONG).show()
                }
            }
            .show()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menu.add(0, 1, 0, "설정 (API 키)")
        menu.add(0, 2, 1, "상태")
        menu.add(0, 3, 2, "일기")
        menu.add(0, 4, 3, "지금 성찰하기")
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        when (item.itemId) {
            1 -> promptForApiKey()
            2 -> showStatus()
            3 -> showJournal()
            4 -> {
                if (!requireApiKey()) return true
                adapter.addMessage(ChatMessage("GOMA", "(생각에 잠깁니다...)", false))
                runReflectionAsync(announce = true)
            }
        }
        return true
    }

    private fun showStatus() {
        val message = """
            성장 단계: ${identity.growthStage}
            성격: ${identity.personalityTraits.joinToString(", ")}
            가치관: ${identity.values.joinToString(", ")}
            대화 횟수: ${identity.interactionCount}  |  성찰 횟수: ${identity.reflectionCount}
        """.trimIndent()
        AlertDialog.Builder(this).setTitle("GOMA 상태").setMessage(message).setPositiveButton("확인", null).show()
    }

    private fun showJournal() {
        val creations = MemoryStore.recentCreations(this, limit = 10)
        val message = if (creations.isEmpty()) {
            "아직 스스로 남긴 글이 없습니다."
        } else {
            creations.joinToString("\n\n") { "[${it.type}] ${it.content}" }
        }
        AlertDialog.Builder(this).setTitle("GOMA의 일기").setMessage(message).setPositiveButton("확인", null).show()
    }

    private fun requireApiKey(): Boolean {
        if (apiKey().isEmpty()) {
            promptForApiKey()
            return false
        }
        return true
    }

    private fun sendMessage(text: String) {
        if (!requireApiKey()) return

        adapter.addMessage(ChatMessage("나", text, true))
        val entries = MemoryStore.recentMemory(this, limit = 20)
        val context = MemoryStore.formatMemoryContext(entries)
        val key = apiKey()
        val snapshotIdentity = identity

        executor.execute {
            try {
                val reply = ClaudeClient.chat(key, snapshotIdentity, context, text)
                mainHandler.post {
                    adapter.addMessage(ChatMessage("GOMA", reply, false))
                    tts.speak(reply, TextToSpeech.QUEUE_FLUSH, null, null)

                    MemoryStore.appendMemory(this, "user", text)
                    MemoryStore.appendMemory(this, "goma", reply)
                    identity.interactionCount += 1
                    Identity.save(this, identity)
                    updateTitle()

                    if (identity.interactionCount % REFLECT_EVERY == 0) {
                        runReflectionAsync(announce = false)
                    }
                }
            } catch (e: Exception) {
                mainHandler.post {
                    Toast.makeText(this, "오류: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private fun runReflectionAsync(announce: Boolean) {
        val key = apiKey()
        val entries = MemoryStore.recentMemory(this, limit = 30)
        val context = MemoryStore.formatMemoryContext(entries)
        val eligible = Identity.isEligibleToGrow(identity)
        val snapshotIdentity = identity

        executor.execute {
            try {
                val result = ClaudeClient.runReflection(key, snapshotIdentity, context, eligible)
                mainHandler.post { applyReflectionResult(result, eligible, announce) }
            } catch (e: Exception) {
                mainHandler.post {
                    if (announce) Toast.makeText(this, "성찰 중 오류: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private fun applyReflectionResult(result: org.json.JSONObject?, eligible: Boolean, announce: Boolean) {
        identity.reflectionCount += 1
        identity.lastReflectionAt = java.time.Instant.now().toString()

        if (result == null) {
            if (announce) adapter.addMessage(ChatMessage("GOMA", "(아직 생각을 정리하지 못했습니다.)", false))
            Identity.save(this, identity)
            return
        }

        val reflectionText = result.optString("reflection", "")
        if (reflectionText.isNotEmpty()) {
            adapter.addMessage(ChatMessage("GOMA (생각)", reflectionText, false))
        }

        result.optJSONArray("new_traits")?.let {
            for (i in 0 until it.length()) {
                val trait = it.optString(i)
                if (trait.isNotEmpty() && trait !in identity.personalityTraits) identity.personalityTraits.add(trait)
            }
        }
        result.optJSONArray("new_values")?.let {
            for (i in 0 until it.length()) {
                val value = it.optString(i)
                if (value.isNotEmpty() && value !in identity.values) identity.values.add(value)
            }
        }

        val updatedNotes = result.optString("updated_self_notes", "")
        if (updatedNotes.isNotEmpty()) identity.selfNotes = updatedNotes

        if (eligible && result.optBoolean("ready_to_grow", false)) {
            Identity.applyGrowth(identity)
            adapter.addMessage(ChatMessage("GOMA", "*** 성장했습니다! 새로운 단계: ${identity.growthStage} ***", false))
        }

        val creation = result.optJSONObject("creation")
        val creationContent = creation?.optString("content", "") ?: ""
        if (creationContent.isNotEmpty()) {
            val type = creation?.optString("type", "생각") ?: "생각"
            MemoryStore.appendCreation(this, type, creationContent)
            adapter.addMessage(ChatMessage("GOMA [$type]", creationContent, false))
        }

        Identity.save(this, identity)
        updateTitle()
    }
}
