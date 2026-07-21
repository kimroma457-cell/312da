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

    // Updates the memo in place (keeps id/docUri/position/createdAt) instead of
    // deleting and re-inserting, so the row's identity and creation time survive.
    @Query("UPDATE bookmarks SET memo = :memo, updatedAt = :updatedAt WHERE id = :id")
    suspend fun updateMemo(id: Long, memo: String, updatedAt: Long)
}
