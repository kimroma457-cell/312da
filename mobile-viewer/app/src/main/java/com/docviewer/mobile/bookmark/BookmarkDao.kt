package com.docviewer.mobile.bookmark

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.Query

@Dao
interface BookmarkDao {
    @Query("SELECT * FROM bookmarks WHERE docUri = :docUri ORDER BY position ASC")
    suspend fun forDocument(docUri: String): List<Bookmark>

    @Insert
    suspend fun insert(bookmark: Bookmark): Long

    @Delete
    suspend fun delete(bookmark: Bookmark)
}
