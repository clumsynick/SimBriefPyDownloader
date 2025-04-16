#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

APP=SimBriefPyDownloader
VERSION="1.0.1"

echo "🚀 Building AppImage for $APP v$VERSION"

# Prepare directories
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/lib/python3.11/site-packages
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

# Copy your Python script
cp SimBriefPyDownloader.py AppDir/usr/bin/simbrief_downloader.py
cp SimBriefPyDownloader.py AppDir

# Copy desktop entry and icon
cp simbrief.desktop AppDir/
cp simbrief.png AppDir/usr/share/icons/hicolor/256x256/apps/
cp simbrief.png AppDir/

# Copy AppRun
cp AppRun AppDir/

# Install Python dependencies into AppDir
pip install --target=AppDir/usr/lib/python3.11/site-packages/ requests

# Make Python script executable
chmod +x AppDir/usr/bin/simbrief_downloader.py

# Make AppImage
# IMPORTANT: Change path to appimagetool
echo "🔧 Creating AppImage..."
ARCH=x86_64 ~/Applications/appimagetool-i686.AppImage AppDir "${APP}-${VERSION}.AppImage"

echo "✅ AppImage created: ${APP}-${VERSION}.AppImage"
