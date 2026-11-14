plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}
android {
    namespace = "com.lingion.liquidglass.sample"
    compileSdk = 37
    defaultConfig {
        applicationId = "com.lingion.liquidglass.sample"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "0.1-dev"
    }
    buildFeatures { compose = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
dependencies {
    implementation(project(":runtime"))
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.compose.foundation:foundation:1.12.1")
}
