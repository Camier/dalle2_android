# ProGuard Rules for DALL-E AI Art Generator
# This file contains rules to optimize and obfuscate the release APK

# Keep application class
-keep public class com.aiart.dalleaiart.** { *; }

# Keep Kivy framework classes
-keep class org.kivy.** { *; }
-keep class org.renpy.** { *; }

# Keep Python interpreter
-keep class org.python.** { *; }

# Keep security classes
-keep class com.aiart.security.** { *; }
-keep class javax.crypto.** { *; }
-keep class java.security.** { *; }

# Keep Android security classes
-keep class androidx.security.crypto.** { *; }

# Keep networking classes
-keep class okhttp3.** { *; }
-keep class retrofit2.** { *; }
-keep class com.squareup.okhttp3.** { *; }

# Keep certificate pinning
-keep class okhttp3.CertificatePinner { *; }
-keep class okhttp3.CertificatePinner$Builder { *; }

# Remove logging in release
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
    public static *** i(...);
    public static *** w(...);
    public static *** e(...);
}

# Obfuscate sensitive method names
-obfuscate

# Optimize code
-optimizationpasses 5
-dontusemixedcaseclassnames
-dontskipnonpubliclibraryclasses
-dontpreverify
-verbose

# Keep attributes for stack traces
-keepattributes SourceFile,LineNumberTable

# Keep exceptions
-keepattributes Exceptions

# Keep signatures for reflection
-keepattributes Signature

# Keep annotations
-keepattributes *Annotation*

# Prevent stripping of native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep enums
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# Keep Parcelables
-keepclassmembers class * implements android.os.Parcelable {
    public static final android.os.Parcelable$Creator CREATOR;
}

# Keep Serializable classes
-keepclassmembers class * implements java.io.Serializable {
    static final long serialVersionUID;
    private static final java.io.ObjectStreamField[] serialPersistentFields;
    private void writeObject(java.io.ObjectOutputStream);
    private void readObject(java.io.ObjectInputStream);
    java.lang.Object writeReplace();
    java.lang.Object readResolve();
}

# Keep R class
-keep class **.R$* { *; }

# Aggressive optimizations
-optimizations !code/simplification/arithmetic,!code/simplification/cast,!field/*,!class/merging/*