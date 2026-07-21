plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.kapt")
}

android {
    namespace = "com.docviewer.mobile"
    // compileSdk 36 + extension 19 (and AGP 8.9.1+ below) are required by
    // androidx.pdf:pdf-viewer-fragment:1.0.0-alpha19 — confirmed by an actual
    // Android Studio build failure, not just docs.
    compileSdk = 36
    compileSdkExtension = 19

    defaultConfig {
        applicationId = "com.docviewer.mobile"
        // Raised from 24: the androidx.pdf library's manifest requires a higher
        // minSdk. Devices below the SdkExtensions check in ViewerActivity still
        // fall back to the legacy PDFView (without search).
        minSdk = 28
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.activity:activity-ktx:1.9.0")
    implementation("androidx.fragment:fragment-ktx:1.8.2")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.4")
    implementation("com.google.android.material:material:1.12.0")

    // PDF rendering: legacy fallback, works on every minSdk 28+ device but has
    // no text search API at all (confirmed against its source on GitHub).
    implementation("com.github.mhiew:android-pdf-viewer:3.2.0-beta.3")

    // PDF rendering: official Jetpack viewer with built-in text search/highlight.
    // Only usable at runtime where SdkExtensions.getExtensionVersion(S) >= 13
    // (see ViewerActivity.isPdfViewerFragmentSupported). Alpha artifact hosted
    // only on Google's Maven repo (unreachable from this dev sandbox), and it
    // requires the AGP/compileSdk/extension bump above at build time.
    implementation("androidx.pdf:pdf-viewer-fragment:1.0.0-alpha19")

    // HWP parsing (converted to HTML for display)
    implementation("kr.dogfoot:hwplib:1.1.10")

    // Bookmarks + memo storage.
    // 2.6.1's bundled kapt annotation processor only reads Kotlin metadata up
    // to version 2.0.0; Kotlin 2.1.20 (bumped above for androidx.pdf) stamps
    // class metadata as 2.1.0, so room-compiler needs a version that reads it.
    implementation("androidx.room:room-runtime:2.7.1")
    implementation("androidx.room:room-ktx:2.7.1")
    kapt("androidx.room:room-compiler:2.7.1")
}
