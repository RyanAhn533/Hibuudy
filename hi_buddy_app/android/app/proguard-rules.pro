# Hi-Buddy ProGuard Rules

# Flutter
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Keep annotations
-keepattributes *Annotation*

# Dart/Flutter specific
-dontwarn io.flutter.embedding.**

# HTTP package
-dontwarn okhttp3.**
-dontwarn okio.**

# SharedPreferences
-keep class androidx.datastore.** { *; }

# TTS
-keep class com.tundralabs.fluttertts.** { *; }

# YouTube player
-keep class com.pierfrancescosoffritti.** { *; }
