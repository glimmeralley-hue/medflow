[app]

# (str) Title of your application
title = MedFlow

# (str) Package name
package.name = medflow

# (str) Package domain (needed for android/ios packaging)
package.domain = com.medflow

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,svg,wav,txt

# (list) List of inclusions using pattern matching
source.include_patterns = medflow/*,sounds/*,medflow-icon.svg

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec,sh,md

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = bin, dist, build, obj, venv, .venv, __pycache__

# (list) List of exclusions using pattern matching
source.exclude_patterns = license,images/*,sounds/env*

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# PySide6 support for Android is experimental - may need to use Kivy instead
requirements = python3, pyside6, sqlite3

# (str) Custom source folders for requirements
# Sets the source folder for requirements to the 'libs' directory
requirements.source = libs/

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/medflow-icon.svg

# (str) Supported orientation (landscape or portrait or all)
orientation = portrait

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (str) Android API version (integer) - needed for PySide6
android.api = 33

# (str) Android NDK version
android.ndk = 25b

# (str) Android SDK path
#android.sdk_path =

# (str) Android NDK path
#android.ndk_path =

# (str) Python version for Android
android.python = 3.10

# (list) Python modules to include
#android.mod_packages =

# (list) Android AAR archives to add
#android.add_aar =

# (bool) Use --private data storage (True) or --application-id (False)
#android.private_storage = True

# (str) Android additional libraries
#android.add_libs_armeabi_v7a = libgameengine.so
#android.add_libs_arm64_v8a = libgameengine.so
#android.add_libs_x86 = libgameengine.so
#android.add_libs_x86_64 = libgameengine.so

# (list) Android AAR archives to add (currently works only with sdl2 bootstrap)
#android.add_aar_dir =

# (list) Gradle dependencies
#android.gradle_dependencies =

# (bool) Enable AndroidX support
#android.enable_androidx = True

# (list) add java compile options
# this can be necessary for PySide6
#android.java_compile_options = -source 1.8 -target 1.8

# (list) Java classes to add as imports
#android.add_java_imports =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning about using SDK version before N
warn_sdk_version = 21

[app:android]

# (list) Permissions
android.permissions = INTERNET