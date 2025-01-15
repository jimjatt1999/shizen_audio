```markdown
# SHIZEN

A desktop application for intermediate to advanced language learners focused on improving listening and reading skills through authentic content. While primarily designed for Japanese learners, it supports multiple languages.

## Overview

SHIZEN helps you practice with real-world content by:
- Processing audio/video files for study
- Downloading YouTube videos  
- Finding and using podcast episodes
- Providing AI-powered language analysis
- Organizing review sessions with spaced repetition

## Setup

### Prerequisites

1. Python 3.9+
2. FFmpeg  
3. Ollama

### Installation Steps

First, install FFmpeg:

**Mac:**
```bash
brew install ffmpeg
```

**Linux:** 
```bash
sudo apt install ffmpeg
```

**Windows:**
Download from [FFmpeg website](https://ffmpeg.org/download.html)

Next, install Ollama:
1. Go to [Ollama.ai](https://ollama.ai)
2. Follow installation instructions for your OS
3. Pull the language model:
```bash
ollama pull llama3.2:8b 
```
note any other models would work, llama3.2:8b is lightweight 
### Setting up the Project

Create and activate a virtual environment:
```bash
# Create venv
python -m venv venv

# Activate on Mac/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Clone and run:
```bash
git clone https://github.com/jimjatt1999/shizen_audio.git
cd shizen_audio
python main.py
```

## Usage

1. Add content through:
   - File upload
   - YouTube videos
   - Podcast episodes

2. Review content with:
   - Transcriptions
   - AI analysis 
   - Spaced repetition system

3. Track your progress and manage content in the library

## Dependencies

Key packages:
- PyQt6 - GUI framework
- faster-whisper - Speech recognition
- yt-dlp - YouTube downloads
- Ollama - AI language analysis

## Planned or future improvement

- Text, document, articles support, with synthetic audio generation
- improve upload loading 
## Support

For issues or questions, please open a GitHub issue.

## License

MIT License

---

Note: This application requires a working internet connection for features like YouTube downloads and AI analysis.
```

