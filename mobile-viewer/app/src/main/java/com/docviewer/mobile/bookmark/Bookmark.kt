package com.docviewer.mobile.bookmark

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "bookmarks")
data class Bookmark(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val docUri: String,
    val docDisplayName: String,
    val position: Int,
    val memo: String,
    val createdAt: Long,
    val updatedAt: Long = createdAt
)
