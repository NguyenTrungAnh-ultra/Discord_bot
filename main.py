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
    # Build environment with PYTHONPATH so bot can find internal modules
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONUNBUFFERED"] = "1"

    while True:
        print("🚀 [Main] Starting Discord Bot...")
        sys.stdout.flush() # Force print
        try:
            # Pass the custom environment
            subprocess.run([PYTHON_EXEC, "-u", BOT_SCRIPT], check=True, env=env)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ [Main] Bot crashed with error: {e}. Restarting in 10s...")
            sys.stdout.flush()
            time.sleep(10)
        except Exception as e:
            print(f"❌ [Main] Bot manager encountered an error: {e}")
            sys.stdout.flush()
            time.sleep(10)

def job_news():
    """Runs the news summarizer."""
    print("📰 [Main] Running News Worker...")
    sys.stdout.flush()
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        subprocess.run([PYTHON_EXEC, "-u", NEWS_SCRIPT], check=True, env=env)
        print("✅ [Main] News Worker finished.")
    except Exception as e:
        print(f"❌ [Main] News Worker failed: {e}")
    sys.stdout.flush()

def job_vision():
    """Runs the Vision Guard."""
    print("👁️ [Main] Running Vision Guard...")
    sys.stdout.flush()
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        subprocess.run([PYTHON_EXEC, "-u", VISION_SCRIPT], check=True, env=env)
        print("✅ [Main] Vision Guard finished.")
    except Exception as e:
        print(f"❌ [Main] Vision Guard failed: {e}")
    sys.stdout.flush()

def job_daily_report():
    """Runs the Daily Report Job (Scan + Send)."""
    print("📊 [Main] Running Daily Report Job...")
    sys.stdout.flush()
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        # We use a slight timeout or ensured exit to prevent hanging
        subprocess.run([PYTHON_EXEC, "-u", DAILY_JOB_SCRIPT], check=True, env=env)
        print("✅ [Main] Daily Report Job finished.")
    except Exception as e:
        print(f"❌ [Main] Daily Report Job failed: {e}")
    sys.stdout.flush()

def run_schedulers():
    """Runs the scheduling loop for News and Vision Guard."""
    schedule.every(1).hours.do(job_news)
    schedule.every().day.at("14:50").do(job_vision)
    schedule.every().day.at("07:00").do(job_daily_report)
    
    print("⏳ [Main] Scheduler started.")
    print("   📰 News: every 1h")
    print("   👁️ Vision: 14:50 daily")
    print("   📊 Reports: 07:00 daily")
    sys.stdout.flush()

    while True:
        schedule.run_pending()
        time.sleep(30)
    

def main():
    print("🔥 Discord Manager Started")
    sys.stdout.flush()
    
    # 2. Run Bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 3. Initial startup jobs
    time.sleep(10) # Give more time for bot to initialize
    job_daily_report() 
    
    # 4. Schedule recurring tasks
    try:
        run_schedulers()
    except KeyboardInterrupt:
        print("\n👋 Exiting Manager.")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
