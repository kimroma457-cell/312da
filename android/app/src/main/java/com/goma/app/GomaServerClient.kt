package com.goma.app

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class GomaApiException(message: String) : Exception(message)

object GomaServerClient {
    private val JSON = "application/json".toMediaType()
    private val http = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private fun normalize(serverUrl: String): String = serverUrl.trimEnd('/')

    private fun getRaw(url: String): String {
        val request = Request.Builder().url(url).get().build()
        http.newCall(request).execute().use { response ->
            val text = response.body?.string() ?: ""
            if (!response.isSuccessful) throw GomaApiException("서버 오류 (${response.code}): $text")
            return text
        }
    }

    private fun postRaw(url: String, body: JSONObject): String {
        val request = Request.Builder().url(url).post(body.toString().toRequestBody(JSON)).build()
        http.newCall(request).execute().use { response ->
            val text = response.body?.string() ?: ""
            if (!response.isSuccessful) throw GomaApiException("서버 오류 (${response.code}): $text")
            return text
        }
    }

    /** Blocking call — must be invoked off the main thread. */
    fun chat(serverUrl: String, message: String): JSONObject {
        val body = JSONObject()
        body.put("message", message)
        return JSONObject(postRaw("${normalize(serverUrl)}/chat", body))
    }

    /** Blocking call — must be invoked off the main thread. */
    fun reflect(serverUrl: String): JSONObject {
        return JSONObject(postRaw("${normalize(serverUrl)}/reflect", JSONObject()))
    }

    /** Blocking call — must be invoked off the main thread. */
    fun status(serverUrl: String): JSONObject {
        return JSONObject(getRaw("${normalize(serverUrl)}/status"))
    }

    /** Blocking call — must be invoked off the main thread. */
    fun journal(serverUrl: String): JSONArray {
        return JSONArray(getRaw("${normalize(serverUrl)}/journal"))
    }
}
