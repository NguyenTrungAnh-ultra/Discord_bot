import subprocess
import time
import schedule
import threading
import os
import sys
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

# Define paths
PYTHON_EXEC = sys.executable
BOT_SCRIPT = os.path.join("src", "modules", "bot_main", "Bot.py")
NEWS_SCRIPT = os.path.join("src", "modules", "news_summarizer", "Firms_news.py")
VISION_SCRIPT = os.path.join("src", "modules", "vision_guard", "VisionGuard.py")
DAILY_JOB_SCRIPT = os.path.join("src", "modules", "report_collecter", "daily_job.py")

def run_bot():
    """Runs the main Discord Bot. Restarts on failure."""
    # Build environment with PYTHONPATH
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    while True:
        print("🚀 [Main] Starting Discord Bot...")
        try:
            # Pass the custom environment
            subprocess.run([PYTHON_EXEC, "-u", BOT_SCRIPT], check=True, env=env)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ [Main] Bot crashed with error: {e}. Restarting in 10s...")
            time.sleep(10)
        except KeyboardInterrupt:
            print("🛑 [Main] Bot stopped by user.")
            break

def job_news():
    """Runs the news summarizer."""
    print("📰 [Main] Running News Worker...")
    # Build environment with PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        subprocess.run([PYTHON_EXEC, "-u", NEWS_SCRIPT], check=True, env=env)
        print("✅ [Main] News Worker finished. Sleeping...")
    except Exception as e:
        print(f"❌ [Main] News Worker failed: {e}")

def job_vision():
    """Runs the Vision Guard."""
    print("👁️ [Main] Running Vision Guard...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        subprocess.run([PYTHON_EXEC, "-u", VISION_SCRIPT], check=True, env=env)
        print("✅ [Main] Vision Guard finished.")
    except Exception as e:
        print(f"❌ [Main] Vision Guard failed: {e}")

def job_daily_report():
    """Runs the Daily Report Job (Scan + Send)."""
    print("📊 [Main] Running Daily Report Job...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        subprocess.run([PYTHON_EXEC, "-u", DAILY_JOB_SCRIPT], check=True, env=env)
        print("✅ [Main] Daily Report Job finished.")
    except Exception as e:
        print(f"❌ [Main] Daily Report Job failed: {e}")

def run_schedulers():
    """Runs the scheduling loop for News and Vision Guard."""
    # News Worker: Run every 1 hour (3600s)
    schedule.every(1).hours.do(job_news)
    # schedule.every(10).seconds.do(job_news) # Debug

    # Vision Guard: Run at 14:45
    schedule.every().day.at("14:45").do(job_vision)

    # Report Sender: Run at 07:00 daily
    schedule.every().day.at("07:00").do(job_daily_report)
    
    print("⏳ [Main] Scheduler started.")
    print("   📰 News: every 1h")
    print("   👁️ Vision: 14:45 daily")
    print("   📊 Reports: 07:00 daily (Scan + Send)")

    while True:
        schedule.run_pending()
        time.sleep(30) # Check every 30s
    

def main():
    print("🔥 Discord Manager Started")
    
    # Start Bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    job_news()
    job_vision()
    # Start Scheduler in the main thread (or separate, but main needs to stay alive)
    # We can run scheduler in main thread
    try:
        run_schedulers()
    except KeyboardInterrupt:
        print("\n👋 Exiting Manager.")

if __name__ == "__main__":
    main()
