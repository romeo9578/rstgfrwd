import os
import subprocess
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# ================= CONFIG =================

BASE_DIR = os.getcwd()
IST = ZoneInfo("Asia/Kolkata")

START_RUNTIME = time.time()
MAX_RUNTIME = (5 * 60 * 60) + (30 * 60)

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

scripts = [
    "!! From laptop/moonknight series/moonseries.py"
    "!! From laptop/BoB Movies/Brat.py"
]

# ================= TELEGRAM =================

def send_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

def send_file(filepath):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(filepath, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"document": f})

def format_duration(seconds):
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    return f"{h:02}:{m:02}:{s:02}"

# ================= START MESSAGE =================

global_start = datetime.now(IST)

send_message(
    f"🚀 <b>Run Started</b>\n"
    f"🕒 {global_start.strftime('%d-%m-%Y %I:%M:%S %p IST')}"
)

# ================= MAIN LOOP =================

for script in scripts:

    if time.time() - START_RUNTIME >= MAX_RUNTIME:
        send_message("⏹️ <b>Time Limit Reached</b>")
        break

    script_path = os.path.join(BASE_DIR, script)
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    if not os.path.isfile(script_path):
        send_message(f"⚠️ File Not Found: {script_name}")
        continue

    start_time = datetime.now(IST)
    start_timer = time.time()

    log_file = f"{script_name.replace('.py','')}_log.txt"

    with open(log_file, "w", encoding="utf-8") as log:

        log.write("=========================================\n")
        log.write(f"SCRIPT NAME : {script_name}\n")
        log.write(f"START TIME  : {start_time.strftime('%d-%m-%Y %I:%M:%S %p IST')}\n")
        log.write("=========================================\n\n")

        process = subprocess.Popen(
            ["python3", script_name],
            cwd=script_dir,
            stdout=log,
            stderr=log
        )
        process.wait()

    end_time = datetime.now(IST)
    duration = format_duration(time.time() - start_timer)

    with open(log_file, "a", encoding="utf-8") as log:
        log.write("\n=========================================\n")
        log.write(f"END TIME    : {end_time.strftime('%d-%m-%Y %I:%M:%S %p IST')}\n")
        log.write(f"DURATION    : {duration}\n")
        log.write(f"STATUS      : {'SUCCESS' if process.returncode == 0 else 'FAILED'}\n")
        log.write("=========================================\n")

    # Telegram message (separate from log file)
    if process.returncode == 0:
        send_message(
            f"✅ <b>Script Completed</b>\n\n"
            f"📂 {script_name}\n"
            f"🕒 Start: {start_time.strftime('%d-%m-%Y %I:%M:%S %p IST')}\n"
            f"🕒 End: {end_time.strftime('%d-%m-%Y %I:%M:%S %p IST')}\n"
            f"⏱ Duration: {duration}"
        )
    else:
        send_message(
            f"❌ <b>Script Failed</b>\n\n"
            f"📂 {script_name}\n"
            f"🕒 Start: {start_time.strftime('%d-%m-%Y %I:%M:%S %p IST')}\n"
            f"🕒 End: {end_time.strftime('%d-%m-%Y %I:%M:%S %p IST')}\n"
            f"⏱ Duration: {duration}"
        )

    send_file(log_file)

    time.sleep(60)

# ================= FINAL =================

global_end = datetime.now(IST)
total_runtime = format_duration(time.time() - START_RUNTIME)

send_message(
    f"🏁 <b>All Scripts Finished</b>\n\n"
    f"🕒 Started: {global_start.strftime('%d-%m-%Y %I:%M:%S %p IST')}\n"
    f"🕒 Ended: {global_end.strftime('%d-%m-%Y %I:%M:%S %p IST')}\n"
    f"⏱ Total Runtime: {total_runtime}"
)
