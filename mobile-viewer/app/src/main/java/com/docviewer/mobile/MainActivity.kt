package com.docviewer.mobile

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private val openDocument = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri != null) {
            // Keeps the permission alive across app restarts so bookmarks saved
            // against this file can still be reopened later.
            try {
                contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            } catch (e: SecurityException) {
                // Not persistable; the file is still usable for this session.
            }
            startActivity(Intent(this, ViewerActivity::class.java).apply {
                action = Intent.ACTION_VIEW
                data = uri
            })
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        findViewById<android.widget.Button>(R.id.openFileButton).setOnClickListener {
            // Many file providers report .hwp as generic octet-stream, so we request
            // everything here and validate the actual file type in ViewerActivity.
            openDocument.launch(arrayOf("*/*"))
        }
    }
}
