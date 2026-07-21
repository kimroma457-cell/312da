package com.docviewer.mobile

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private val openDocument = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri != null) {
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
