# models/review.py

from datetime import datetime, timedelta
from typing import List, Dict
import json
from pathlib import Path
from collections import defaultdict
import time
import traceback

class ReviewSystem:
    def __init__(self, storage_path: str = "./data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize settings with language support
        self.settings = {
            'daily_new_cards': 20,
            'cards_per_session': 3,
            'learning_language': 'ja',    # Default to Japanese
            'native_language': 'en',      # Default to English
        }
        
        self.items = []
        self.skipped_cards = []
        self.analysis_cache = {}  # Add this to store AI analysis results

        
        # Initialize statistics
        self.stats = {
            'last_review_date': None,
            'streak': 0,
            'today_reviews': 0,
            'study_time': 0,
            'session_start': None,
            'review_history': {}
        }
        
        # Initialize AI helper with language settings
        from audio_processors.ai_service import AIHelper
        self.ai_helper = AIHelper()
        
        # Load existing state
        try:
            self.load_state()
        except Exception as e:
            print(f"Could not load state: {e}")
            
        print(f"Review system initialized with {len(self.items)} items")

    def get_cached_analysis(self, text: str, learning_lang: str, native_lang: str) -> Dict:
        """Get cached analysis or generate new one"""
        cache_key = f"{text}:{learning_lang}:{native_lang}"
        
        if cache_key in self.analysis_cache:
            print("Using cached analysis")
            return self.analysis_cache[cache_key]
        
        # Generate new analysis
        print("Generating new analysis")
        analysis = self.ai_helper.generate_analysis(text, learning_lang, native_lang)
        self.analysis_cache[cache_key] = analysis
        return analysis


    def check_daily_limit(self) -> Dict:
        """Check if daily limit has been reached"""
        today = datetime.now().date().isoformat()
        
        # Reset extra cards if it's a new day
        if self.settings.get('last_study_date') != today:
            self.settings['extra_cards_today'] = 0
            self.settings['last_study_date'] = today
            self.save_state()

        total_today = self.stats.get('today_reviews', 0)
        daily_limit = self.settings.get('daily_limit', 20)
        
        return {
            'limit_reached': total_today >= daily_limit,
            'total_today': total_today,
            'daily_limit': daily_limit,
            'extra_cards': self.settings.get('extra_cards_today', 0)
        }
    
    def continue_beyond_limit(self):
        """Track that user is continuing beyond limit"""
        self.settings['extra_cards_today'] += 1
        self.save_state()

    def process_review(self, item_id: str, response: str):
        """Process a review response with enhanced error handling"""
        try:
            # Find the item
            item = next((i for i in self.items if i['id'] == item_id), None)
            if not item:
                print(f"Card {item_id} not found")
                return

            print(f"Processing review for item {item_id}: {response}")

            # Update statistics
            today = datetime.now().date().isoformat()
            
            # Initialize ratings if needed
            if today not in self.stats['review_history']:
                self.stats['review_history'][today] = {
                    'total': 0,
                    'ratings': {
                        'again': 0,
                        'hard': 0,
                        'good': 0,
                        'easy': 0
                    }
                }

            self.stats['today_reviews'] += 1
            self.stats['review_history'][today]['total'] += 1
            self.stats['review_history'][today]['ratings'][response] += 1
            self.update_streak()

            # Update interval based on response
            current_interval = item.get('interval', 0)
            current_ease = item.get('ease', 2.5)

            if response == 'again':
                new_interval = 1
                new_ease = max(1.3, current_ease - 0.2)
            elif response == 'hard':
                new_interval = max(1, current_interval * current_ease * 0.8)
                new_ease = max(1.3, current_ease - 0.15)
            elif response == 'good':
                new_interval = max(1, current_interval * current_ease)
                new_ease = current_ease
            else:  # easy
                new_interval = max(2, current_interval * current_ease * 1.3)
                new_ease = min(2.5, current_ease + 0.1)

            # Update card
            item['interval'] = new_interval
            item['ease'] = new_ease
            item['next_review'] = datetime.now() + timedelta(days=new_interval)
            item['reviews'] = item.get('reviews', 0) + 1

            print(f"Updated card: interval={new_interval}, ease={new_ease}")
            
            # Save changes
            self.save_state()

        except Exception as e:
            print(f"Error in process_review: {str(e)}")
            traceback.print_exc()
            raise Exception(f"Failed to process review: {str(e)}")


    def load_state(self):
        """Load state and settings from disk"""
        try:
            state_file = self.storage_path / 'state.json'
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    
                    # Load items with language info
                    self.items = [{
                        **item,
                        'next_review': datetime.fromisoformat(item['next_review']),
                        'language': item.get('language', self.settings['learning_language'])
                    } for item in state.get('items', [])]
                    
                    # Load skipped cards
                    self.skipped_cards = [{
                        **card,
                        'next_review': datetime.fromisoformat(card['next_review']),
                        'language': card.get('language', self.settings['learning_language'])
                    } for card in state.get('skipped_cards', [])]
                    
                    # Update settings
                    saved_settings = state.get('settings', {})
                    self.settings.update(saved_settings)
                    
                    # Load statistics
                    saved_stats = state.get('stats', {})
                    self.stats.update(saved_stats)

                    # Load analysis cache
                    self.analysis_cache = state.get('analysis_cache', {})
                    
                print(f"Loaded {len(self.items)} items from {state_file}")
        except Exception as e:
            print(f"Error loading state: {str(e)}")
            self.items = []
            self.skipped_cards = []
            self.analysis_cache = {}  # Initialize empty cache on error
            

    def start_session(self):
        """Start a study session"""
        self.stats['session_start'] = time.time()

    def end_session(self):
        """End a study session and update study time"""
        if self.stats['session_start']:
            self.stats['study_time'] += time.time() - self.stats['session_start']
            self.stats['session_start'] = None
            self.save_state()

    def update_streak(self):
        """Update study streak"""
        try:
            today = datetime.now().date()
            if self.stats.get('last_review_date'):
                last_date = datetime.fromisoformat(self.stats['last_review_date']).date()
                if today - last_date == timedelta(days=1):
                    self.stats['streak'] += 1
                elif today - last_date > timedelta(days=1):
                    self.stats['streak'] = 1
            else:
                self.stats['streak'] = 1
                
            self.stats['last_review_date'] = datetime.now().isoformat()
            self.save_state()
        except Exception as e:
            print(f"Error updating streak: {e}")

    def validate_card(self, card: Dict) -> bool:
        """Validate card data"""
        required_fields = ['id', 'text', 'audio_path', 'start_time', 'end_time']
        try:
            return all(
                card.get(field) is not None 
                for field in required_fields
            )
        except Exception as e:
            print(f"Error validating card: {e}")
            return False
        
    def get_source_segments(self, audio_path: str) -> List[Dict]:
        """Get all segments for a specific source"""
        segments = [
            {
                'start': float(item.get('start_time', 0)),  # Ensure float
                'end': float(item.get('end_time', 0)),      # Ensure float
                'text': item.get('text', ''),
                'id': item.get('id', '')
            }
            for item in self.items 
            if item['audio_path'] == audio_path
        ]
        
        # Sort by start time
        segments.sort(key=lambda x: x['start'])
        return segments
    
    def add_source(self, source_info: dict, segments: List[dict]):
        """Add new audio source and its segments with language info"""
        try:
            print(f"Adding source: {source_info['title']}")
            if not segments:
                raise ValueError("No segments provided")
            
            for segment in segments:
                if not segment['text'].strip():
                    continue
                    
                card = {
                    'id': segment['id'],
                    'text': segment['text'],
                    'audio_path': source_info['audio_path'],
                    'url': source_info.get('url', ''),
                    'start_time': segment['start'],
                    'end_time': segment['end'],
                    'next_review': datetime.now(),
                    'interval': 0,
                    'ease': 2.5,
                    'reviews': 0,
                    'language': self.settings['learning_language']  # Add language info
                }
                
                if self.validate_card(card):
                    self.items.append(card)
                else:
                    print(f"Invalid card data: {card}")
            
            print(f"Added {len(segments)} segments to review system")
            self.save_state()
            
        except Exception as e:
            print(f"Error adding source: {str(e)}")
            raise Exception(f"Failed to add source: {str(e)}")


    def skip_card(self, card_id: str):
        """Temporarily skip a card and show it again later"""
        try:
            # Find and remove the card from main items
            card = next((c for c in self.items if c['id'] == card_id), None)
            if card:
                # Remove from main items
                self.items = [item for item in self.items if item['id'] != card_id]
                
                # Add to skipped cards if not already there
                if not any(s['id'] == card_id for s in self.skipped_cards):
                    self.skipped_cards.append(card)
                    print(f"Card {card_id} skipped, will show again later")
                else:
                    print(f"Card {card_id} already in skipped cards")
                    
                self.save_state()  # Save the state after modification
            else:
                print(f"Card {card_id} not found")
        except Exception as e:
            print(f"Error skipping card: {e}")
            raise Exception(f"Failed to skip card: {str(e)}")

    def edit_card_text(self, card_id: str, new_text: str):
        """Edit card text"""
        try:
            card = next((c for c in self.items if c['id'] == card_id), None)
            if card:
                card['text'] = new_text.strip()
                self.save_state()
                print(f"Card {card_id} text updated")
            else:
                print(f"Card {card_id} not found")
        except Exception as e:
            print(f"Error editing card: {e}")
            raise Exception(f"Failed to edit card: {str(e)}")

    def delete_card(self, card_id: str):
        """Delete individual card"""
        try:
            print(f"Deleting card: {card_id}")
            original_count = len(self.items)
            self.items = [item for item in self.items if item['id'] != card_id]
            deleted_count = original_count - len(self.items)
            if deleted_count > 0:
                self.save_state()
                print(f"Card deleted, remaining cards: {len(self.items)}")
            else:
                print(f"Card {card_id} not found")
        except Exception as e:
            print(f"Error deleting card: {str(e)}")
            raise Exception(f"Failed to delete card: {str(e)}")
        
    def get_settings(self):
        """Safe way to get settings with defaults"""
        return {
            'daily_new_cards': self.settings.get('daily_new_cards', 20),
            'cards_per_session': self.settings.get('cards_per_session', 3),
            'learning_language': self.settings.get('learning_language', 'ja'),
            'native_language': self.settings.get('native_language', 'en')
        }

    def update_settings(self, daily_new_cards: int, cards_per_session: int,
                       learning_language: str = None, native_language: str = None):
        """Update settings including language preferences"""
        try:
            self.settings['daily_new_cards'] = daily_new_cards
            self.settings['cards_per_session'] = cards_per_session
            
            # Update language settings if provided
            if learning_language is not None:
                self.settings['learning_language'] = learning_language
            if native_language is not None:
                self.settings['native_language'] = native_language
            
            self.save_state()
            print(f"Settings updated: {self.settings}")
        except Exception as e:
            print(f"Error updating settings: {e}")
            raise Exception(f"Failed to update settings: {str(e)}")

    def get_due_items(self, limit: int = None) -> List[dict]:
        """Get items due for review"""
        try:
            now = datetime.now()
            cards_per_session = self.settings.get('cards_per_session', 3)
            
            # Get all due and new cards
            due_cards = [item for item in self.items 
                        if item['reviews'] > 0 and item['next_review'] <= now]
            new_cards = [item for item in self.items if item['reviews'] == 0]
            
            # Count new cards studied today
            new_cards_today = len([i for i in self.items 
                                 if i.get('reviews', 0) == 1 and 
                                 i.get('last_review_date') == now.date().isoformat()])
            
            new_cards_limit = self.settings.get('daily_new_cards', 20)
            remaining_new = max(0, new_cards_limit - new_cards_today)
            
            # Combine cards
            items_to_show = due_cards.copy()
            if remaining_new > 0:
                items_to_show.extend(new_cards[:remaining_new])
            
            # Shuffle and limit by cards_per_session
            import random
            random.shuffle(items_to_show)
            return items_to_show[:cards_per_session]
            
        except Exception as e:
            print(f"Error getting due items: {e}")
            return []
        
    def reset_stats(self):
        """Reset all statistics and learning progress"""
        try:
            # Reset statistics
            self.stats = {
                'last_review_date': None,
                'streak': 0,
                'today_reviews': 0,
                'study_time': 0,
                'session_start': None,
                'review_history': {}
            }

            # Reset learning progress for all cards
            for card in self.items:
                card['next_review'] = datetime.now()
                card['interval'] = 0
                card['ease'] = 2.5
                card['reviews'] = 0

            # Clear skipped cards
            self.skipped_cards = []

            self.save_state()
            print("Statistics and learning progress reset successfully")
        except Exception as e:
            print(f"Error resetting stats: {e}")
            raise Exception(f"Failed to reset stats: {str(e)}")

    def get_stats(self) -> Dict:
        """Get current statistics"""
        try:
            now = datetime.now()
            new_cards_limit = self.settings.get('daily_new_cards', 20)
            
            # Get all due and new cards
            due_cards = [i for i in self.items 
                        if i.get('reviews', 0) > 0 and i.get('next_review', now) <= now]
            new_cards = [i for i in self.items if i.get('reviews', 0) == 0]
            
            # Count new cards studied today
            new_cards_today = len([i for i in self.items 
                                 if i.get('reviews', 0) == 1 and 
                                 i.get('last_review_date') == now.date().isoformat()])
            
            remaining_new = max(0, new_cards_limit - new_cards_today)

            stats = {
                'due': len(due_cards),
                'new': min(len(new_cards), remaining_new),
                'total': len(self.items)
            }
            print(f"Current stats: {stats}")
            return stats
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'due': 0, 'new': 0, 'total': 0}

    def get_detailed_stats(self) -> Dict:
        """Get detailed statistics"""
        try:
            today = datetime.now().date()
            return {
                'streak': self.stats.get('streak', 0),
                'today_reviews': self.stats.get('today_reviews', 0),
                'study_time': round(self.stats.get('study_time', 0) / 3600, 1),  # hours
                'ratings_distribution': dict(self.stats['review_history'].get(
                    today.isoformat(), {}).get('ratings', defaultdict(int))),
                'sources_distribution': self.get_sources_distribution(),
                'progress': {
                    'done': self.stats.get('today_reviews', 0),
                    'total': self.settings.get('daily_limit', 20)
                }
            }
        except Exception as e:
            print(f"Error getting detailed stats: {e}")
            return {
                'streak': 0,
                'today_reviews': 0,
                'study_time': 0,
                'ratings_distribution': {},
                'sources_distribution': {},
                'progress': {'done': 0, 'total': 20}
            }

    def get_sources_distribution(self) -> Dict:
        """Get card distribution by source"""
        try:
            distribution = defaultdict(lambda: {'total': 0, 'reviewed': 0})
            for item in self.items:
                source = Path(item['audio_path']).stem
                distribution[source]['total'] += 1
                if item.get('reviews', 0) > 0:
                    distribution[source]['reviewed'] += 1
            return dict(distribution)
        except Exception as e:
            print(f"Error getting source distribution: {e}")
            return {}

    def get_sources(self) -> List[Dict]:
        """Get list of unique sources and their card counts"""
        try:
            sources = {}
            for item in self.items:
                if item['audio_path'] not in sources:
                    source_type = 'youtube' if 'youtube.com' in item.get('url', '') else 'podcast'
                    sources[item['audio_path']] = {
                        'audio_path': item['audio_path'],
                        'title': Path(item['audio_path']).stem,
                        'type': source_type,
                        'card_count': 1,
                        'reviewed_count': 1 if item.get('reviews', 0) > 0 else 0
                    }
                else:
                    sources[item['audio_path']]['card_count'] += 1
                    if item.get('reviews', 0) > 0:
                        sources[item['audio_path']]['reviewed_count'] += 1
            
            return list(sources.values())
        except Exception as e:
            print(f"Error getting sources: {e}")
            return []
        
    def delete_source(self, audio_path: str):
        """Delete source and update stats"""
        try:
            print(f"Deleting source: {audio_path}")
            cards_before = len(self.items)
            self.items = [item for item in self.items if item['audio_path'] != audio_path]
            cards_deleted = cards_before - len(self.items)
            
            # Reset stats if no items remain
            if len(self.items) == 0:
                self.reset_stats()
            
            try:
                audio_file = Path(audio_path)
                if audio_file.exists():
                    audio_file.unlink()
                    print(f"Deleted audio file: {audio_path}")
            except Exception as e:
                print(f"Warning: Could not delete audio file: {audio_path} - {e}")
            
            self.save_state()
            print(f"Saved updated state with {len(self.items)} remaining cards")
            
        except Exception as e:
            print(f"Error in delete_source: {e}")
            raise Exception(f"Failed to delete source: {str(e)}")
            
        except Exception as e:
            print(f"Error in delete_source: {e}")
            raise Exception(f"Failed to delete source: {str(e)}")

    def save_state(self):
        """Save current state and settings to disk"""
        try:
            state_file = self.storage_path / 'state.json'
            state = {
                'items': [{
                    **item,
                    'next_review': item['next_review'].isoformat()
                } for item in self.items],
                'skipped_cards': [{
                    **card,
                    'next_review': card['next_review'].isoformat()
                } for card in self.skipped_cards],
                'settings': self.settings,
                'stats': {
                    **self.stats,
                    'review_history': dict(self.stats['review_history'])
                },
                'analysis_cache': self.analysis_cache  # Save analysis cache
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error saving state: {str(e)}")
            raise Exception(f"Failed to save state: {str(e)}")

