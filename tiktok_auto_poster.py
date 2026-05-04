#!/usr/bin/env python3
"""
TikTok Auto Poster - Automated TikTok Content Posting Script
This script runs 24/7 and automatically finds trending TikTok videos, downloads them, and reposts them
with custom hashtags at scheduled times (8AM, 2PM, 8PM EST).
"""

import os
import sys
import time
import logging
import smtplib
import requests
import subprocess
from datetime import datetime, timezone
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import re

# Third-party imports
import yt_dlp
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tiktok_poster.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TikTokAutoPoster:
    """Main class for automated TikTok video posting"""
    
    def __init__(self):
        """Initialize the TikTok Auto Poster with configuration and credentials"""
        # Load credentials from environment variables
        self.tiktok_api_key = os.getenv('TIKTOK_API_KEY')
        self.tiktok_api_secret = os.getenv('TIKTOK_API_SECRET')
        self.tiktok_access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
        self.tiktok_username = os.getenv('TIKTOK_USERNAME')
        self.gmail_address = os.getenv('GMAIL_ADDRESS')
        self.gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')
        
        # File paths for logging and storage
        self.posted_videos_file = 'posted_videos.txt'
        self.errors_file = 'errors.txt'
        self.downloads_folder = Path('downloads')
        
        # Search keywords for finding trending videos
        self.search_keywords = ['reddit story', 'reddit stories', 'redditor', 'AITA', 'storytime reddit']
        
        # Hashtags to use when posting
        self.post_hashtags = '#reddit #redditstories #redditstorytime #redditreadings #storytime'
        
        # Minimum requirements for videos
        self.min_views = 100000
        self.min_duration_seconds = 60
        
        # Retry configuration
        self.max_retries = 3
        
        # Create downloads folder if it doesn't exist
        self.downloads_folder.mkdir(exist_ok=True)
        
        # Initialize posted videos set
        self.posted_videos = self.load_posted_videos()
        
        logger.info("TikTok Auto Poster initialized successfully")
    
    def load_posted_videos(self) -> set:
        """Load the set of already posted video URLs from the log file"""
        posted_videos = set()
        try:
            if os.path.exists(self.posted_videos_file):
                with open(self.posted_videos_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            # Extract URL from log line (format: timestamp URL)
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                posted_videos.add(parts[1])
                logger.info(f"Loaded {len(posted_videos)} previously posted videos")
        except Exception as e:
            logger.error(f"Error loading posted videos: {e}")
        return posted_videos
    
    def save_posted_video(self, video_url: str) -> None:
        """Save a video URL to the posted videos log file"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.posted_videos_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} {video_url}\n")
            
            # Also update the in-memory set
            self.posted_videos.add(video_url)
            logger.info(f"Saved posted video: {video_url}")
        except Exception as e:
            logger.error(f"Error saving posted video: {e}")
    
    def log_error(self, error_message: str) -> None:
        """Log an error to the errors file with timestamp"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.errors_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} - {error_message}\n")
        except Exception as e:
            logger.error(f"Error logging to errors file: {e}")
    
    def send_error_email(self, subject: str, message: str) -> None:
        """Send an error notification email using Gmail SMTP"""
        try:
            if not self.gmail_address or not self.gmail_app_password:
                logger.warning("Gmail credentials not configured, skipping email notification")
                return
            
            # Create the email message
            msg = MimeMultipart()
            msg['From'] = self.gmail_address
            msg['To'] = self.gmail_address
            msg['Subject'] = f"TikTok Auto Poster Error: {subject}"
            
            # Add the message body
            body = f"An error occurred in the TikTok Auto Poster:\n\n{message}\n\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            msg.attach(MimeText(body, 'plain'))
            
            # Send the email using Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_address, self.gmail_app_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Error email sent successfully: {subject}")
        except Exception as e:
            logger.error(f"Failed to send error email: {e}")
            self.log_error(f"Failed to send error email: {e}")
    
    def search_tiktok_videos(self, keyword: str) -> List[Dict[str, Any]]:
        """Search TikTok for videos using yt-dlp and return video information"""
        try:
            # Configure yt-dlp options for searching TikTok
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Only extract metadata, don't download
                'ignoreerrors': True,
            }
            
            # Search query
            search_query = f"tiktoksearch {keyword}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Perform the search
                search_results = ydl.extract_info(search_query, download=False)
                
                videos = []
                if 'entries' in search_results:
                    for entry in search_results['entries']:
                        if entry and 'url' in entry:
                            video_info = {
                                'url': entry['url'],
                                'title': entry.get('title', ''),
                                'view_count': entry.get('view_count', 0),
                                'duration': entry.get('duration', 0),
                                'uploader': entry.get('uploader', ''),
                                'description': entry.get('description', '')
                            }
                            videos.append(video_info)
                
                logger.info(f"Found {len(videos)} videos for keyword: {keyword}")
                return videos
                
        except Exception as e:
            logger.error(f"Error searching TikTok videos for '{keyword}': {e}")
            self.log_error(f"Error searching TikTok videos for '{keyword}': {e}")
            return []
    
    def filter_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter videos based on criteria (views, duration, not already posted, not from own account)"""
        filtered_videos = []
        
        for video in videos:
            try:
                # Skip if already posted
                if video['url'] in self.posted_videos:
                    continue
                
                # Skip if from own account
                if self.tiktok_username and video['uploader'] == self.tiktok_username:
                    continue
                
                # Skip if insufficient views
                if video['view_count'] < self.min_views:
                    continue
                
                # Skip if insufficient duration
                if video['duration'] < self.min_duration_seconds:
                    continue
                
                filtered_videos.append(video)
                
            except Exception as e:
                logger.error(f"Error filtering video {video.get('url', 'unknown')}: {e}")
                continue
        
        # Sort by view count (highest first)
        filtered_videos.sort(key=lambda x: x['view_count'], reverse=True)
        
        logger.info(f"Filtered to {len(filtered_videos)} eligible videos")
        return filtered_videos
    
    def download_video(self, video_url: str, max_retries: int = 3) -> Optional[str]:
        """Download a TikTok video using yt-dlp with retry logic"""
        for attempt in range(max_retries):
            try:
                # Generate a unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"tiktok_video_{timestamp}.mp4"
                filepath = self.downloads_folder / filename
                
                # Configure yt-dlp options for downloading
                ydl_opts = {
                    'outtmpl': str(filepath),
                    'format': 'best[ext=mp4]',
                    'quiet': True,
                    'no_warnings': True,
                    'ignoreerrors': True,
                    'writethumbnail': False,
                    # Try to remove watermark if possible
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Download the video
                    info = ydl.extract_info(video_url, download=True)
                    
                    # Verify the downloaded file exists and has sufficient duration
                    if filepath.exists():
                        # Get actual duration of downloaded video
                        actual_duration = info.get('duration', 0)
                        
                        if actual_duration >= self.min_duration_seconds:
                            logger.info(f"Successfully downloaded video: {filename}")
                            return str(filepath)
                        else:
                            logger.warning(f"Downloaded video too short ({actual_duration}s), deleting: {filename}")
                            filepath.unlink()
                            return None
                    else:
                        logger.error(f"Download failed - file not found: {filename}")
                        return None
                        
            except Exception as e:
                logger.error(f"Download attempt {attempt + 1} failed for {video_url}: {e}")
                if attempt == max_retries - 1:
                    self.log_error(f"Failed to download video after {max_retries} attempts: {video_url} - {e}")
                    self.send_error_email("Video Download Failed", f"Failed to download video: {video_url}\nError: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def upload_to_tiktok(self, video_path: str, max_retries: int = 3) -> bool:
        """Upload a video to TikTok using the TikTok Content Posting API"""
        for attempt in range(max_retries):
            try:
                if not all([self.tiktok_api_key, self.tiktok_api_secret, self.tiktok_access_token]):
                    logger.error("TikTok API credentials not configured")
                    self.send_error_email("TikTok API Missing", "TikTok API credentials are not configured in environment variables")
                    return False
                
                # TikTok Content Posting API endpoint
                upload_url = "https://open.tiktokapis.com/v2/video/upload/"
                
                # Prepare the video file for upload
                with open(video_path, 'rb') as video_file:
                    files = {
                        'video': (os.path.basename(video_path), video_file, 'video/mp4')
                    }
                    
                    # Prepare the data payload
                    data = {
                        'access_token': self.tiktok_access_token,
                        'caption': self.post_hashtags,
                    }
                    
                    # Make the upload request
                    response = requests.post(upload_url, files=files, data=data)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if 'data' in response_data and 'video_id' in response_data['data']:
                            video_id = response_data['data']['video_id']
                            logger.info(f"Successfully uploaded video to TikTok: {video_id}")
                            return True
                        else:
                            logger.error(f"TikTok upload response missing video_id: {response_data}")
                    else:
                        logger.error(f"TikTok upload failed with status {response.status_code}: {response.text}")
                
            except Exception as e:
                logger.error(f"TikTok upload attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    self.log_error(f"Failed to upload to TikTok after {max_retries} attempts: {video_path} - {e}")
                    self.send_error_email("TikTok Upload Failed", f"Failed to upload video: {video_path}\nError: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    def cleanup_video_file(self, video_path: str) -> None:
        """Delete the downloaded video file to save storage space"""
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Cleaned up video file: {video_path}")
        except Exception as e:
            logger.error(f"Error cleaning up video file {video_path}: {e}")
    
    def find_and_post_video(self) -> bool:
        """Main method to find, download, and post a TikTok video"""
        try:
            logger.info("Starting video search and post process")
            
            # Search through all keywords
            all_videos = []
            for keyword in self.search_keywords:
                logger.info(f"Searching for videos with keyword: {keyword}")
                videos = self.search_tiktok_videos(keyword)
                all_videos.extend(videos)
            
            if not all_videos:
                logger.warning("No videos found for any keywords")
                return False
            
            # Filter videos based on criteria
            eligible_videos = self.filter_videos(all_videos)
            
            if not eligible_videos:
                logger.warning("No eligible videos found after filtering")
                return False
            
            # Try the best video (highest views)
            best_video = eligible_videos[0]
            logger.info(f"Selected best video: {best_video['title']} ({best_video['view_count']} views)")
            
            # Download the video
            video_path = self.download_video(best_video['url'])
            
            if not video_path:
                logger.error("Failed to download video")
                return False
            
            # Upload to TikTok
            upload_success = self.upload_to_tiktok(video_path)
            
            if upload_success:
                # Mark as posted
                self.save_posted_video(best_video['url'])
                
                # Clean up
                self.cleanup_video_file(video_path)
                
                logger.info("Successfully completed video posting process")
                return True
            else:
                # Clean up even if upload failed
                self.cleanup_video_file(video_path)
                return False
                
        except Exception as e:
            logger.error(f"Error in find_and_post_video: {e}")
            self.log_error(f"Error in find_and_post_video: {e}")
            self.send_error_email("Video Posting Process Failed", f"Error in video posting process: {e}")
            return False
    
    def run_scheduled_post(self) -> None:
        """Execute the scheduled posting process"""
        try:
            logger.info("Running scheduled TikTok post")
            
            success = self.find_and_post_video()
            
            if success:
                logger.info("Scheduled post completed successfully")
            else:
                logger.warning("Scheduled post failed or no suitable video found")
                
        except Exception as e:
            logger.error(f"Error in scheduled post: {e}")
            self.log_error(f"Error in scheduled post: {e}")
            self.send_error_email("Scheduled Post Failed", f"Error during scheduled post: {e}")
    
    def start_scheduler(self) -> None:
        """Start the APScheduler for automated posting"""
        try:
            # Create a background scheduler
            scheduler = BackgroundScheduler(timezone='EST')
            
            # Schedule jobs for 8AM, 2PM, and 8PM EST every day
            scheduler.add_job(
                func=self.run_scheduled_post,
                trigger=CronTrigger(hour=8, minute=0, timezone='EST'),
                id='morning_post',
                name='Morning TikTok Post (8AM EST)',
                replace_existing=True
            )
            
            scheduler.add_job(
                func=self.run_scheduled_post,
                trigger=CronTrigger(hour=14, minute=0, timezone='EST'),
                id='afternoon_post',
                name='Afternoon TikTok Post (2PM EST)',
                replace_existing=True
            )
            
            scheduler.add_job(
                func=self.run_scheduled_post,
                trigger=CronTrigger(hour=20, minute=0, timezone='EST'),
                id='evening_post',
                name='Evening TikTok Post (8PM EST)',
                replace_existing=True
            )
            
            # Start the scheduler
            scheduler.start()
            
            logger.info("Scheduler started successfully")
            logger.info("Scheduled posts: 8:00 AM EST, 2:00 PM EST, 8:00 PM EST")
            
            # Keep the script running
            try:
                while True:
                    time.sleep(60)  # Check every minute
            except (KeyboardInterrupt, SystemExit):
                logger.info("Shutting down scheduler...")
                scheduler.shutdown()
                
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            self.log_error(f"Error starting scheduler: {e}")
            self.send_error_email("Scheduler Failed", f"Failed to start scheduler: {e}")

def main():
    """Main function to run the TikTok Auto Poster"""
    try:
        logger.info("Starting TikTok Auto Poster")
        
        # Create and start the auto poster
        poster = TikTokAutoPoster()
        poster.start_scheduler()
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        # Try to send email notification about fatal error
        try:
            poster = TikTokAutoPoster()
            poster.send_error_email("Fatal Error", f"Fatal error in TikTok Auto Poster: {e}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
