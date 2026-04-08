import asyncio
import os
import random
import subprocess
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from hashlib import md5
from datetime import datetime

# ================= CONFIG =================

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
string_session = os.getenv("TG_STRING_SESSION")

source_group = '-1003678231874'
destination_groups = ['@jhfdsffgwegsfjhadsf63msxu23']

channel = "Bratty sis"

min_delay = 8
max_delay = 15

pause_every = 35
pause_time = 300  # seconds

hashes_file = 'forwarded_hashes.txt'
log_file = 'forward_log.txt'
duplicates_file = 'duplicates_log.txt'
resume_file = 'last_message_id.txt'

forwarded_hashes = set()

client = TelegramClient(StringSession(string_session), api_id, api_hash)

# ================= SAFE COMMIT =================

def safe_commit():
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions"])
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"])

        subprocess.run(["git", "add", resume_file, hashes_file, log_file, duplicates_file])

        result = subprocess.run(["git", "diff", "--cached", "--quiet"])

        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Auto update progress"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("💾 Progress committed")
        else:
            print("ℹ️ No changes to commit")

    except Exception as e:
        print(f"⚠️ Commit failed: {e}")

# ================= HELPERS =================

def load_hashes():
    if os.path.exists(hashes_file):
        with open(hashes_file, 'r', encoding='utf-8') as f:
            for line in f:
                forwarded_hashes.add(line.strip())

def save_hash(msg_hash):
    with open(hashes_file, 'a', encoding='utf-8') as f:
        f.write(msg_hash + '\n')

def log(file, msg):
    with open(file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def hash_message(message):
    if message.text:
        return md5(message.text.encode('utf-8')).hexdigest()
    elif message.media:
        return f"{message.media.__class__.__name__}_{message.id}"
    return None

def load_last_id():
    if os.path.exists(resume_file):
        with open(resume_file, 'r') as f:
            return int(f.read().strip())
    return 0

def save_last_id(message_id):
    with open(resume_file, 'w') as f:
        f.write(str(message_id))

# ================= MAIN =================

async def forward_history():
    load_hashes()
    await client.start()
    print("✅ Bot started")

    source_entity = await client.get_input_entity(int(source_group))

    resolved_destinations = []
    for dest in destination_groups:
        entity = await client.get_entity(dest)
        resolved_destinations.append(entity)

    for dest in resolved_destinations:
        await client.send_message(dest, f"======= Started {channel}")

    last_forwarded_id = load_last_id()
    forwarded_count = 0

    async for message in client.iter_messages(
            source_entity,
            min_id=last_forwarded_id,
            reverse=True
    ):

        msg_hash = hash_message(message)
        if not msg_hash:
            continue

        if msg_hash in forwarded_hashes:
            log(duplicates_file, "Skipped duplicate")
            continue

        should_forward_file = False
        send_text_only = False

        # ✅ Images
        if message.photo:
            should_forward_file = True

        # ✅ Videos
        elif message.video or (
            message.document and message.document.mime_type and
            message.document.mime_type.startswith("video")
        ):
            should_forward_file = True

        # ✅ PDF
        elif message.document and message.document.mime_type == "application/pdf":
            should_forward_file = True

        # ✅ ZIP / RAR / 7z (mime types)
        elif message.document and message.document.mime_type in [
            "application/zip",
            "application/x-zip-compressed",
            "application/x-rar-compressed",
            "application/octet-stream"
        ]:
            should_forward_file = True

        # ✅ ZIP fallback via filename
        elif message.document and message.file and message.file.name and \
                message.file.name.lower().endswith(('.zip', '.rar', '.7z')):
            should_forward_file = True

        # ✅ Any text
        elif message.text:
            send_text_only = True

        else:
            continue

        for dest in resolved_destinations:
            try:
                await asyncio.sleep(random.uniform(min_delay, max_delay))

                if should_forward_file:
                    await client.send_file(
                        dest,
                        message.media,
                        caption=message.text or ''
                    )
                    print(f"✅ Sent media: {message.id}")

                elif send_text_only:
                    await client.send_message(dest, message.text)
                    print(f"✅ Sent text: {message.id}")

                log(log_file, f"Forwarded {message.id}")
                save_last_id(message.id)
                forwarded_count += 1

                if forwarded_count % 15 == 0:
                    safe_commit()

            except errors.FloodWaitError as e:
                print(f"⏳ Flood wait: sleeping {e.seconds} seconds")
                await asyncio.sleep(e.seconds + 5)

            except Exception as e:
                print(f"❌ Error: {e}")
                log(log_file, f"Error: {e}")

        forwarded_hashes.add(msg_hash)
        save_hash(msg_hash)

        if forwarded_count % pause_every == 0:
            print(f"⏸ Pausing for {pause_time // 60} minutes...")
            await asyncio.sleep(pause_time)

    for dest in resolved_destinations:
        await client.send_message(dest, f"Till Now Done {channel}")

    safe_commit()
    print(f"🎉 Done forwarding {forwarded_count} message(s).")

# ================= RUN =================

try:
    client.loop.run_until_complete(forward_history())
except KeyboardInterrupt:
    print("\n🛑 Bot stopped by user.")
