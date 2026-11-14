import org.jetbrains.kotlin.gradle.dsl.JvmTarget
plugins {
    id("org.jetbrains.kotlin.multiplatform")
    id("com.android.kotlin.multiplatform.library")
    id("org.jetbrains.kotlin.plugin.compose")
}
kotlin {
    android {
        namespace = "com.lingion.liquidglass"
        compileSdk = 37
        minSdk = 26
        androidResources { enable = true }
        compilerOptions { jvmTarget = JvmTarget.JVM_17 }
        withHostTestBuilder {}.configure {}
    }
    sourceSets {
        androidMain.dependencies {
            api("androidx.compose.runtime:runtime:1.12.1")
            api("androidx.compose.ui:ui:1.12.1")
            implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.11.0")
            implementation("io.github.kyant0:shapes:1.2.1")
            api(project(":backdrop"))
            api("androidx.compose.material3:material3:1.5.0-rc01")
            implementation("androidx.compose.foundation:foundation:1.12.1")
            implementation("studio.lunabee.compose:material-color-utilities:1.10.0")
        }
        val androidHostTest by getting { dependencies { implementation("junit:junit:4.13.2") } }
    }
}
