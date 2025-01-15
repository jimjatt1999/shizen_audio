# audio_processors/media_processor.py
from typing import List, Dict
from pathlib import Path
import yt_dlp
import requests
import feedparser
from .whisper import WhisperProcessor
import ffmpeg  # Add this import
import shutil

class MediaProcessor:
    def __init__(self, download_dir: str = "./downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.whisper = WhisperProcessor()


    def process_upload(self, file_path: Path) -> Dict:
        """Process uploaded media file"""
        try:
            # Create output path
            output_path = self.download_dir / file_path.name

            # Copy file if it's audio, convert if it's video
            if file_path.suffix.lower() in ['.mp3', '.wav', '.m4a']:
                import shutil
                shutil.copy2(file_path, output_path)
                audio_path = output_path
            else:
                # Convert video to audio
                audio_path = output_path.with_suffix('.mp3')
                self.convert_to_audio(str(file_path), str(audio_path))

            # Process with Whisper
            segments = self.whisper.transcribe(str(audio_path))

            return {
                'title': file_path.stem,
                'audio_path': str(audio_path),
                'original_path': str(output_path),
                'type': 'upload',
                'segments': segments
            }

        except Exception as e:
            raise Exception(f"Failed to process upload: {str(e)}")


    def convert_to_audio(self, input_path: str, output_path: str):
        """Convert video to audio using ffmpeg"""
        try:
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(stream, output_path, acodec='libmp3lame', ab='192k')
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
            print('stdout:', e.stdout.decode('utf8'))
            print('stderr:', e.stderr.decode('utf8'))
            raise Exception(f"FFmpeg error: {str(e)}")
        
    def process_youtube(self, url: str) -> Dict:
        """Download and process YouTube video"""
        print(f"Processing YouTube URL: {url}")  # Debug
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.download_dir / '%(title)s.%(ext)s'),
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = str(self.download_dir / f"{info['title']}.mp3")
            print(f"Downloaded audio to: {audio_path}")  # Debug
            
            return {
                'title': info['title'],
                'duration': info['duration'],
                'audio_path': audio_path,
                'url': url,
                'type': 'youtube'
            }

    def search_podcasts(self, query: str) -> List[Dict]:
        """Search iTunes podcast directory"""
        print(f"Searching podcasts for: {query}")  # Debug
        url = "https://itunes.apple.com/search"
        params = {
            'term': query,
            'entity': 'podcast',
            'limit': 50
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        results = [{
            'title': item['collectionName'],
            'author': item['artistName'],
            'feed_url': item['feedUrl'],
            'artwork': item.get('artworkUrl600', ''),
            'description': item.get('description', '')
        } for item in data.get('results', [])]
        
        print(f"Found {len(results)} podcasts")  # Debug
        return results

    def get_podcast_episodes(self, feed_url: str) -> List[Dict]:
        """Get episodes from podcast feed"""
        print(f"Fetching episodes from: {feed_url}")  # Debug
        feed = feedparser.parse(feed_url)
        episodes = []
        
        for entry in feed.entries:
            audio_url = next(
                (link.href for link in entry.links 
                if hasattr(link, 'type') and 
                link.type.startswith('audio/')),
                None
            )
            
            if audio_url:
                episodes.append({
                    'title': entry.title,
                    'url': audio_url,
                    'description': entry.get('description', ''),
                    'duration': entry.get('itunes_duration', ''),
                    'published': entry.get('published', '')
                })
        
        print(f"Found {len(episodes)} episodes")  # Debug
        return episodes

    def process_podcast_episode(self, episode_url: str, title: str) -> Dict:
        """Download and process podcast episode"""
        print(f"Processing podcast episode: {title}")  # Debug
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}.mp3"
        output_path = self.download_dir / filename
        
        if not output_path.exists():
            print(f"Downloading episode to: {output_path}")  # Debug
            response = requests.get(episode_url, stream=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        return {
            'title': title,
            'audio_path': str(output_path),
            'url': episode_url,
            'type': 'podcast'
        }