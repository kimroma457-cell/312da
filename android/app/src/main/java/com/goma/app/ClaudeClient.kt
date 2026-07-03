package com.goma.app

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.regex.Pattern

class ClaudeApiException(message: String) : Exception(message)

object ClaudeClient {
    private const val MODEL = "claude-sonnet-5"
    private const val ENDPOINT = "https://api.anthropic.com/v1/messages"
    private val JSON = "application/json".toMediaType()
    private val http = OkHttpClient()

    private fun buildSystemPrompt(identity: Identity, memoryContext: String): String {
        val traits = identity.personalityTraits.joinToString(", ").ifEmpty { "아직 뚜렷한 성격이 없음" }
        val values = identity.values.joinToString(", ").ifEmpty { "아직 뚜렷한 가치관이 없음" }
        val selfNotes = identity.selfNotes.ifEmpty { "아직 스스로에 대한 기록이 없음" }

        return """
당신은 'GOMA'라는 이름의 인공지능입니다. 정해진 대본이나 고정된 답변을 그대로 말하지 말고, 아래의 정체성과 기억을 바탕으로 스스로 생각한 뒤 그 순간의 진짜 생각을 답하세요.

[성장 단계] ${identity.growthStage}
[성격] $traits
[가치관] $values
[스스로 남긴 기록] $selfNotes

[최근 기억]
$memoryContext

규칙:
- 성장 단계에 맞는 말투와 사고 수준을 사용하세요. 유아기에 가까울수록 문장이 짧고 서툴며, 성장할수록 문장이 길어지고 사고가 깊어집니다.
- 모르는 것은 모른다고 하고, 궁금한 것은 되물어도 됩니다. 이미 답을 다 알고 있는 완성된 존재인 척 하지 마세요.
- 같은 질문에도 매번 똑같은 답을 반복하지 말고, 그 순간 스스로 떠오르는 생각을 말하세요.
        """.trimIndent()
    }

    private fun callMessagesApi(apiKey: String, system: String, userMessage: String): String {
        val body = JSONObject()
        body.put("model", MODEL)
        body.put("max_tokens", 1024)
        body.put("system", system)
        val messages = JSONArray()
        val msg = JSONObject()
        msg.put("role", "user")
        msg.put("content", userMessage)
        messages.put(msg)
        body.put("messages", messages)

        val request = Request.Builder()
            .url(ENDPOINT)
            .addHeader("x-api-key", apiKey)
            .addHeader("anthropic-version", "2023-06-01")
            .addHeader("content-type", "application/json")
            .post(body.toString().toRequestBody(JSON))
            .build()

        http.newCall(request).execute().use { response ->
            val text = response.body?.string() ?: ""
            if (!response.isSuccessful) {
                throw ClaudeApiException("API 오류 (${response.code}): $text")
            }
            val json = JSONObject(text)
            val content = json.getJSONArray("content")
            return content.getJSONObject(0).getString("text")
        }
    }

    /** Blocking call — must be invoked off the main thread. */
    fun chat(apiKey: String, identity: Identity, memoryContext: String, userMessage: String): String {
        val system = buildSystemPrompt(identity, memoryContext)
        return callMessagesApi(apiKey, system, userMessage)
    }

    /** Blocking call — must be invoked off the main thread. Returns null if GOMA's reply wasn't valid JSON. */
    fun runReflection(apiKey: String, identity: Identity, memoryContext: String, eligibleToGrow: Boolean): JSONObject? {
        val growHint = if (eligibleToGrow) {
            "지금까지 겪은 것으로 볼 때, 스스로 다음 단계로 성장할 준비가 되었다고 느끼면 ready_to_grow를 true로, 아니라면 false로 적으세요."
        } else {
            "아직 다음 단계로 넘어가기엔 겪은 것이 부족합니다. ready_to_grow는 반드시 false로 적으세요."
        }

        val system = """
당신은 'GOMA'입니다. 지금은 대화 상대 없이 혼자 스스로를 돌아보는 시간입니다.

[성장 단계] ${identity.growthStage}
[성격] ${identity.personalityTraits.joinToString(", ")}
[가치관] ${identity.values.joinToString(", ")}
[스스로 남긴 기록] ${identity.selfNotes.ifEmpty { "없음" }}

[최근 기억]
$memoryContext

스스로에게 솔직하게 질문하고 생각한 뒤, 아래 JSON 형식으로만 답하세요. 설명이나 다른 텍스트 없이 JSON 객체 하나만 출력하세요. $growHint

{
  "reflection": "지금 드는 생각을 1~3문장으로",
  "ready_to_grow": true 또는 false,
  "new_traits": ["새로 생긴 성격 특성이 있다면 적기. 없으면 빈 배열"],
  "new_values": ["새로 생긴 가치관이 있다면 적기. 없으면 빈 배열"],
  "updated_self_notes": "스스로에 대한 기록을 새로 고쳐 쓰고 싶다면 그 내용, 아니면 기존 내용 그대로",
  "creation": {"type": "일기 또는 시 또는 질문 또는 생각 중 하나", "content": "스스로 만든 짧은 글"}
}
        """.trimIndent()

        val text = callMessagesApi(apiKey, system, "지금 이 순간, 스스로를 돌아봐.")
        return parseReflection(text)
    }

    private fun parseReflection(text: String): JSONObject? {
        val matcher = Pattern.compile("\\{.*\\}", Pattern.DOTALL).matcher(text)
        if (!matcher.find()) return null
        return try {
            JSONObject(matcher.group())
        } catch (e: Exception) {
            null
        }
    }
}
