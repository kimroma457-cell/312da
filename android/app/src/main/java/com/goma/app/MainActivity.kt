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
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {

    companion object {
        private const val PREFS = "goma_prefs"
        private const val KEY_SERVER_URL = "server_url"
    }

    private lateinit var prefs: SharedPreferences
    private lateinit var adapter: ChatAdapter
    private lateinit var tts: TextToSpeech
    private val executor: ExecutorService = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())

    private var growthStage = "유아기"
    private var interactionCount = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)

        val toolbar = findViewById<Toolbar>(R.id.toolbar)
        setSupportActionBar(toolbar)
        updateTitle()

        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) tts.language = Locale.KOREAN
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

        if (serverUrl().isEmpty()) {
            promptForServerUrl()
        } else {
            refreshStatus()
        }
    }

    override fun onDestroy() {
        tts.shutdown()
        super.onDestroy()
    }

    private fun serverUrl(): String = prefs.getString(KEY_SERVER_URL, "") ?: ""

    private fun updateTitle() {
        supportActionBar?.title = "GOMA"
        supportActionBar?.subtitle = "$growthStage · 대화 ${interactionCount}회"
    }

    private fun promptForServerUrl() {
        val input = EditText(this)
        input.hint = "http://100.x.x.x:8765"
        input.setText(serverUrl())
        AlertDialog.Builder(this)
            .setTitle("GOMA 서버 주소")
            .setMessage("컴퓨터에서 실행 중인 GOMA 서버 주소를 입력하세요 (Tailscale IP 등).")
            .setView(input)
            .setCancelable(false)
            .setPositiveButton("저장") { _, _ ->
                val url = input.text.toString().trim()
                prefs.edit().putString(KEY_SERVER_URL, url).apply()
                if (url.isEmpty()) {
                    Toast.makeText(this, "서버 주소가 없으면 GOMA와 대화할 수 없습니다.", Toast.LENGTH_LONG).show()
                } else {
                    refreshStatus()
                }
            }
            .show()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menu.add(0, 1, 0, "설정 (서버 주소)")
        menu.add(0, 2, 1, "상태")
        menu.add(0, 3, 2, "일기")
        menu.add(0, 4, 3, "지금 성찰하기")
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        when (item.itemId) {
            1 -> promptForServerUrl()
            2 -> showStatus()
            3 -> showJournal()
            4 -> {
                if (!requireServerUrl()) return true
                adapter.addMessage(ChatMessage("GOMA", "(생각에 잠깁니다...)", false))
                runReflectionAsync()
            }
        }
        return true
    }

    private fun requireServerUrl(): Boolean {
        if (serverUrl().isEmpty()) {
            promptForServerUrl()
            return false
        }
        return true
    }

    private fun showStatus() {
        if (!requireServerUrl()) return
        val url = serverUrl()
        executor.execute {
            try {
                val json = GomaServerClient.status(url)
                mainHandler.post { showStatusDialog(json) }
            } catch (e: Exception) {
                mainHandler.post { Toast.makeText(this, "오류: ${e.message}", Toast.LENGTH_LONG).show() }
            }
        }
    }

    private fun showStatusDialog(json: JSONObject) {
        val traits = jsonArrayToList(json.optJSONArray("personality_traits")).joinToString(", ")
        val values = jsonArrayToList(json.optJSONArray("values")).joinToString(", ")
        val message = """
            성장 단계: ${json.optString("growth_stage")}
            성격: $traits
            가치관: $values
            대화 횟수: ${json.optInt("interaction_count")}  |  성찰 횟수: ${json.optInt("reflection_count")}
        """.trimIndent()
        AlertDialog.Builder(this).setTitle("GOMA 상태").setMessage(message).setPositiveButton("확인", null).show()
    }

    private fun jsonArrayToList(array: JSONArray?): List<String> {
        if (array == null) return emptyList()
        return (0 until array.length()).map { array.optString(it) }
    }

    private fun showJournal() {
        if (!requireServerUrl()) return
        val url = serverUrl()
        executor.execute {
            try {
                val array = GomaServerClient.journal(url)
                mainHandler.post { showJournalDialog(array) }
            } catch (e: Exception) {
                mainHandler.post { Toast.makeText(this, "오류: ${e.message}", Toast.LENGTH_LONG).show() }
            }
        }
    }

    private fun showJournalDialog(array: JSONArray) {
        val message = if (array.length() == 0) {
            "아직 스스로 남긴 글이 없습니다."
        } else {
            (0 until array.length()).joinToString("\n\n") {
                val entry = array.getJSONObject(it)
                "[${entry.optString("type")}] ${entry.optString("content")}"
            }
        }
        AlertDialog.Builder(this).setTitle("GOMA의 일기").setMessage(message).setPositiveButton("확인", null).show()
    }

    private fun refreshStatus() {
        val url = serverUrl()
        if (url.isEmpty()) return
        executor.execute {
            try {
                val json = GomaServerClient.status(url)
                mainHandler.post { applyIdentity(json) }
            } catch (e: Exception) {
                // 서버가 아직 안 켜져 있을 수 있으니 조용히 무시
            }
        }
    }

    private fun applyIdentity(json: JSONObject) {
        growthStage = json.optString("growth_stage", growthStage)
        interactionCount = json.optInt("interaction_count", interactionCount)
        updateTitle()
    }

    private fun sendMessage(text: String) {
        if (!requireServerUrl()) return
        val url = serverUrl()

        adapter.addMessage(ChatMessage("나", text, true))

        executor.execute {
            try {
                val json = GomaServerClient.chat(url, text)
                mainHandler.post {
                    val reply = json.optString("reply", "")
                    adapter.addMessage(ChatMessage("GOMA", reply, false))
                    tts.speak(reply, TextToSpeech.QUEUE_FLUSH, null, null)

                    json.optJSONObject("identity")?.let { applyIdentity(it) }
                    json.optJSONObject("reflection")?.let { applyReflectionSummary(it) }
                }
            } catch (e: Exception) {
                mainHandler.post { Toast.makeText(this, "오류: ${e.message}", Toast.LENGTH_LONG).show() }
            }
        }
    }

    private fun runReflectionAsync() {
        val url = serverUrl()
        executor.execute {
            try {
                val json = GomaServerClient.reflect(url)
                mainHandler.post {
                    json.optJSONObject("identity")?.let { applyIdentity(it) }
                    json.optJSONObject("summary")?.let { applyReflectionSummary(it) }
                }
            } catch (e: Exception) {
                mainHandler.post { Toast.makeText(this, "성찰 중 오류: ${e.message}", Toast.LENGTH_LONG).show() }
            }
        }
    }

    private fun applyReflectionSummary(summary: JSONObject) {
        val reflectionText = summary.optString("reflection", "")
        if (reflectionText.isNotEmpty()) {
            adapter.addMessage(ChatMessage("GOMA (생각)", reflectionText, false))
        }
        if (summary.optBoolean("grew", false)) {
            adapter.addMessage(
                ChatMessage("GOMA", "*** 성장했습니다! 새로운 단계: ${summary.optString("new_growth_stage")} ***", false)
            )
        }
        summary.optJSONObject("creation")?.let { creation ->
            val type = creation.optString("type", "생각")
            val content = creation.optString("content", "")
            if (content.isNotEmpty()) {
                adapter.addMessage(ChatMessage("GOMA [$type]", content, false))
            }
        }
    }
}
