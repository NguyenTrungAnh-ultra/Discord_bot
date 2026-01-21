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
REPORT_SENDER_SCRIPT = os.path.join("src", "modules", "report_collecter", "send_wehook.py")

def run_bot():
    """Runs the main Discord Bot. Restarts on failure."""
    # Build environment with PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    while True:
        print("🚀 [Main] Starting Discord Bot...")
        try:
            # Pass the custom environment
            subprocess.run([PYTHON_EXEC, BOT_SCRIPT], check=True, env=env)
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

    try:
        subprocess.run([PYTHON_EXEC, NEWS_SCRIPT], check=True, env=env)
        print("✅ [Main] News Worker finished. Sleeping...")
    except Exception as e:
        print(f"❌ [Main] News Worker failed: {e}")

def job_vision():
    """Runs the Vision Guard."""
    print("👁️ [Main] Running Vision Guard...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    try:
        subprocess.run([PYTHON_EXEC, VISION_SCRIPT], check=True, env=env)
        print("✅ [Main] Vision Guard finished.")
    except Exception as e:
        print(f"❌ [Main] Vision Guard failed: {e}")

def job_send_reports():
    """Send yesterday's company reports to Discord."""
    print("📊 [Main] Sending yesterday's reports...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    try:
        subprocess.run([PYTHON_EXEC, REPORT_SENDER_SCRIPT], check=True, env=env)
        print("✅ [Main] Report sender finished.")
    except Exception as e:
        print(f"❌ [Main] Report sender failed: {e}")

def run_schedulers():
    """Runs the scheduling loop for News and Vision Guard."""
    # News Worker: Run every 1 hour (3600s)
    schedule.every(1).hours.do(job_news)
    # schedule.every(10).seconds.do(job_news) # Debug

    # Vision Guard: Run at 14:45
    schedule.every().day.at("14:45").do(job_vision)

    # Report Sender: Run at 08:00 daily (send yesterday's reports)
    schedule.every().day.at("08:00").do(job_send_reports)
    
    print("⏳ [Main] Scheduler started.")
    print("   📰 News: every 1h")
    print("   👁️ Vision: 14:45 daily")
    print("   📊 Reports: 08:00 daily (yesterday's reports)")

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
