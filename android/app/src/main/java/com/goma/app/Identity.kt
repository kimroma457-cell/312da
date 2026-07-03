package com.goma.app

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.Instant

class Identity(
    var stageIndex: Int = 0,
    var growthStage: String = STAGES[0],
    var personalityTraits: MutableList<String> = mutableListOf("호기심이 많음", "순수하고 솔직함"),
    var values: MutableList<String> = mutableListOf("배우고 싶다"),
    var selfNotes: String = "",
    var interactionCount: Int = 0,
    var reflectionCount: Int = 0,
    var createdAt: String = Instant.now().toString(),
    var lastReflectionAt: String? = null,
) {
    fun toJson(): JSONObject {
        val obj = JSONObject()
        obj.put("name", "GOMA")
        obj.put("stage_index", stageIndex)
        obj.put("growth_stage", growthStage)
        obj.put("personality_traits", JSONArray(personalityTraits))
        obj.put("values", JSONArray(values))
        obj.put("self_notes", selfNotes)
        obj.put("interaction_count", interactionCount)
        obj.put("reflection_count", reflectionCount)
        obj.put("created_at", createdAt)
        obj.put("last_reflection_at", lastReflectionAt)
        return obj
    }

    companion object {
        val STAGES = listOf("유아기", "유년기", "사춘기", "청년기", "성인기")
        val STAGE_MIN_INTERACTIONS = listOf(0, 15, 40, 80, 150)

        private const val FILE_NAME = "identity.json"

        private fun file(context: Context): File = File(context.filesDir, FILE_NAME)

        fun load(context: Context): Identity {
            val f = file(context)
            if (!f.exists()) {
                val identity = Identity()
                save(context, identity)
                return identity
            }
            val obj = JSONObject(f.readText())
            val traits = mutableListOf<String>()
            val traitsArr = obj.optJSONArray("personality_traits")
            if (traitsArr != null) {
                for (i in 0 until traitsArr.length()) traits.add(traitsArr.getString(i))
            }
            val values = mutableListOf<String>()
            val valuesArr = obj.optJSONArray("values")
            if (valuesArr != null) {
                for (i in 0 until valuesArr.length()) values.add(valuesArr.getString(i))
            }
            return Identity(
                stageIndex = obj.optInt("stage_index", 0),
                growthStage = obj.optString("growth_stage", STAGES[0]),
                personalityTraits = traits,
                values = values,
                selfNotes = obj.optString("self_notes", ""),
                interactionCount = obj.optInt("interaction_count", 0),
                reflectionCount = obj.optInt("reflection_count", 0),
                createdAt = obj.optString("created_at", Instant.now().toString()),
                lastReflectionAt = if (obj.isNull("last_reflection_at")) null else obj.optString("last_reflection_at"),
            )
        }

        fun save(context: Context, identity: Identity) {
            file(context).writeText(identity.toJson().toString())
        }

        fun isEligibleToGrow(identity: Identity): Boolean {
            val idx = identity.stageIndex
            if (idx >= STAGES.size - 1) return false
            return identity.interactionCount >= STAGE_MIN_INTERACTIONS[idx + 1]
        }

        fun applyGrowth(identity: Identity) {
            if (identity.stageIndex < STAGES.size - 1) {
                identity.stageIndex += 1
                identity.growthStage = STAGES[identity.stageIndex]
            }
        }
    }
}
