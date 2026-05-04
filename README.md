# TikTok Auto Poster - Automated Content Posting Script

A fully automated Python script that runs 24/7 on Railway.app and automatically finds trending TikTok videos, downloads them, and reposts them to your TikTok account with custom hashtags.

## 🚀 Features

- **Automated Video Discovery**: Searches TikTok for trending Reddit story videos
- **Smart Filtering**: Only posts videos with 100k+ views and 60+ seconds duration
- **Duplicate Prevention**: Never reposts the same video twice
- **Scheduled Posting**: Posts automatically at 8:00 AM, 2:00 PM, and 8:00 PM EST
- **Error Handling**: Comprehensive retry logic and error logging
- **Email Notifications**: Get instant email alerts when something goes wrong
- **Railway Ready**: Fully configured for Railway.app deployment

## 📋 Requirements

- Python 3.11+
- TikTok Developer Account
- Gmail Account (for error notifications)
- Railway.app Account

## 🔧 Setup Instructions

### 1. Get TikTok API Credentials

1. **Apply for TikTok Developer Access**
   - Go to [TikTok Developer Portal](https://developers.tiktok.com/)
   - Click "Apply Now" and create a developer account
   - Select "Create an App" and choose "Content Posting" API

2. **Get Your API Credentials**
   - Once approved, go to your app dashboard
   - Find your **API Key** and **API Secret**
   - Generate an **Access Token** with content posting permissions

3. **Note Your TikTok Username**
   - Make sure you have the exact username of the account that will post videos

### 2. Set Up Gmail for Error Notifications

1. **Enable 2-Factor Authentication**
   - Go to your Google Account settings
   - Enable 2FA if not already enabled

2. **Generate App Password**
   - Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" for the app and "Other (Custom name)" for the device
   - Name it "TikTok Auto Poster"
   - Copy the generated 16-character password

### 3. Configure Environment Variables

1. **Create .env file**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your credentials**
   ```env
   # TikTok API Credentials
   TIKTOK_API_KEY=your_actual_api_key
   TIKTOK_API_SECRET=your_actual_api_secret
   TIKTOK_ACCESS_TOKEN=your_actual_access_token
   
   # Your TikTok Account
   TIKTOK_USERNAME=your_tiktok_username
   
   # Gmail for Notifications
   GMAIL_ADDRESS=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_char_app_password
   ```

### 4. Deploy to Railway.app

1. **Create Railway Account**
   - Sign up at [Railway.app](https://railway.app/)
   - Connect your GitHub account

2. **Deploy the Project**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository with these files
   - Railway will automatically detect it's a Python project

3. **Add Environment Variables in Railway**
   - Go to your project settings → "Variables"
   - Add all the same variables from your .env file:
     - `TIKTOK_API_KEY`
     - `TIKTOK_API_SECRET` 
     - `TIKTOK_ACCESS_TOKEN`
     - `TIKTOK_USERNAME`
     - `GMAIL_ADDRESS`
     - `GMAIL_APP_PASSWORD`

4. **Configure Deployment Settings**
   - Make sure the build command is: `pip install -r requirements.txt`
   - The start command should be: `python tiktok_auto_poster.py`
   - Set the health check path to `/` (optional)

5. **Deploy and Monitor**
   - Click "Deploy" and wait for the build to complete
   - Check the logs to ensure the script started successfully

## 📁 Project Structure

```
your-project/
├── tiktok_auto_poster.py    # Main script with all automation logic
├── requirements.txt          # Python dependencies
├── Procfile                 # Railway deployment configuration
├── .env.example             # Environment variables template
├── README.md               # This file
└── downloads/              # Temporary folder (created automatically)
```

## ⚙️ How It Works

### Video Finding Process
1. Searches TikTok using keywords: "reddit story", "reddit stories", "redditor", "AITA", "storytime reddit"
2. Filters videos based on:
   - 100,000+ views
   - 60+ seconds duration
   - Not from your own account
   - Not previously posted
3. Selects the highest-viewed video that meets criteria

### Posting Process
1. Downloads video in highest quality using yt-dlp
2. Attempts to remove TikTok watermark
3. Uploads to your TikTok account with hashtags: `#reddit #redditstories #redditstorytime #redditreadings #storytime`
4. Logs the video URL to prevent reposting
5. Deletes the local video file to save space

### Scheduling
- Uses APScheduler to run at exactly 8:00 AM, 2:00 PM, and 8:00 PM EST
- Script runs continuously 24/7
- If no suitable video is found, it skips and tries again next time

## 🔍 Monitoring and Logs

### Check Railway Logs
1. Go to your Railway project
2. Click on your deployed service
3. View real-time logs in the "Logs" tab

### Local Log Files
The script creates these log files in your Railway deployment:
- `tiktok_poster.log` - Main activity log
- `posted_videos.txt` - History of posted videos
- `errors.txt` - Detailed error log

### Email Notifications
You'll receive emails for:
- Failed video downloads
- TikTok upload failures  
- API credential issues
- Scheduler startup problems
- Fatal script errors

## 🛠️ Local Development

To test the script locally:

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run the script**
   ```bash
   python tiktok_auto_poster.py
   ```

## 🔧 Troubleshooting

### Common Issues

**"TikTok API credentials not configured"**
- Check that all TikTok environment variables are set in Railway
- Verify your API keys are correct and have content posting permissions

**"No videos found"**
- The script will automatically retry at the next scheduled time
- Check the logs to see if search queries are working
- TikTok may be blocking automated searches temporarily

**"Download failed"**
- The script retries up to 3 times automatically
- Check if yt-dlp needs updates (handled by requirements.txt)

**"Upload failed"**
- Verify your TikTok access token is valid and not expired
- Check that your TikTok account is in good standing

### Getting Help

1. **Check Railway Logs** - Most errors appear here with full details
2. **Review Error Emails** - You'll get detailed error messages via email
3. **Verify API Credentials** - Most issues are related to expired or incorrect API keys

## 📝 Customization

### Change Search Keywords
Edit the `search_keywords` list in `tiktok_auto_poster.py`:
```python
self.search_keywords = ['reddit story', 'reddit stories', 'redditor', 'AITA', 'storytime reddit']
```

### Change Posting Schedule
Modify the cron triggers in the `start_scheduler()` method:
```python
# Example: Change to 9AM, 3PM, 9PM
scheduler.add_job(func=self.run_scheduled_post, trigger=CronTrigger(hour=9, minute=0, timezone='EST'))
```

### Change Hashtags
Update the `post_hashtags` variable:
```python
self.post_hashtags = '#reddit #redditstories #redditstorytime #redditreadings #storytime'
```

### Change Video Requirements
Modify these variables in the `__init__` method:
```python
self.min_views = 100000      # Minimum view count
self.min_duration_seconds = 60  # Minimum video duration in seconds
```

## ⚠️ Important Notes

- **TikTok API Limits**: TikTok may rate-limit API calls. The script handles this with retry logic
- **Content Guidelines**: Ensure reposted content complies with TikTok's community guidelines
- **Storage Space**: Videos are automatically deleted after posting to save space
- **24/7 Operation**: Railway's free tier may pause inactive deployments. Consider upgrading for guaranteed 24/7 operation

## 📄 License

This project is for educational purposes. Use responsibly and in accordance with TikTok's terms of service and API usage policies.

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Railway logs for detailed error messages
3. Verify all API credentials are correct and current

---

**Happy automated posting! 🚀**
