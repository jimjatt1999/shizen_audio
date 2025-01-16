# setup.py
from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('ui/assets', ['ui/assets/icon.icns']),
    ('data', ['data/state.json']),
    ('downloads', [])
]
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'ui/assets/icon.icns',
    'packages': ['PyQt6', 'faster_whisper', 'requests', 'yt_dlp', 'feedparser'],
    'plist': {
        'CFBundleName': "SHIZEN",
        'CFBundleDisplayName': "SHIZEN",
        'CFBundleGetInfoString': "Language Learning App",
        'CFBundleIdentifier': "com.shizen.app",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': "© 2024"
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)