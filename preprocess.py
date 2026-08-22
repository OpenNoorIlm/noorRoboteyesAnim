import subprocess, os, json, sqlite3, math

BASE = "/home/bismillah/Downloads/noorRoboteyesAnim/animationStuff/animations/animation"
OUT_BASE = BASE

# Key lists exactly as keyframed
eye_keys_original = ["Blink","Squint","Sad","Angry","Worried","Glare","Tired","Shocked","Smirk","Confused","WinkL","WinkR","Sleepy"]
eye_keys_new      = ["LTEL","LTER","LBEL","LBER","RTEL","RTER","RBEL","RBER","LT","LL","LR","LB","RT","RL","RR","RB"]
eye_keys_all      = ["Basis"] + eye_keys_original + eye_keys_new  # includes Basis for static hold
mouth_keys        = ["Smile","Frown","Angry","Smirk","Upset","SideAnger","SideSad","Shocked","MBP","AH","OH","OOH","EE"]
mouth_keys_all    = ["Basis"] + mouth_keys  # includes Basis

# Build pair sequences for each video
# output_mjpeg: frames 0-3771
# Section 1 (0-1690): eye_keys_original x mouth_keys, both animate
# Section 2 (1691-3771): eye_keys_new x mouth_keys, eye animates mouth holds
output_pairs = []
for ek in eye_keys_original:
    for mk in mouth_keys:
        output_pairs.append((ek, mk, "both"))
for ek in eye_keys_new:
    for mk in mouth_keys:
        output_pairs.append((ek, mk, "eye_anim_mouth_holds"))

# onlyEyes_mjpeg: frames 3772-7832
# mouth holds at 1.0, eye animates, mouth_keys_all x eye_keys_all (including Basis)
onlyEyes_pairs = []
for mk in mouth_keys_all:
    for ek in eye_keys_original + eye_keys_new:
        onlyEyes_pairs.append((ek, mk, "eye_anim_mouth_static"))

# onlyMouth_mjpeg: frames 7833-11733
# eye holds, mouth animates, eye_keys_all x mouth_keys
onlyMouth_pairs = []
for ek in eye_keys_all:
    for mk in mouth_keys:
        onlyMouth_pairs.append((ek, mk, "mouth_anim_eye_static"))

videos = [
    ("output_mjpeg.avi",    "output_mjpeg",    output_pairs),
    ("onlyEyes_mjpeg.avi",  "onlyEyes_mjpeg",  onlyEyes_pairs),
    ("onlyMouth_mjpeg.avi", "onlyMouth_mjpeg", onlyMouth_pairs),
]

print("Pair counts:")
for v, _, p in videos:
    print(f"  {v}: {len(p)} pairs")

config = {}
animations = {}
static_dir = os.path.join(OUT_BASE, "Static")
os.makedirs(static_dir, exist_ok=True)

for video_file, folder_name, pairs in videos:
    video_path = os.path.join(BASE, video_file)
    out_dir = os.path.join(OUT_BASE, folder_name)
    os.makedirs(out_dir, exist_ok=True)

    print(f"\nProcessing {video_file} ({len(pairs)} pairs)...")

    for i, (ek, mk, anim_type) in enumerate(pairs):
        clip_name = f"E{ek}||M{mk}"
        start_frame = i * 10
        start_sec = start_frame / 12.0
        duration_sec = 10 / 12.0

        clip_path = os.path.join(out_dir, f"{clip_name}.avi")
        static_path = os.path.join(static_dir, f"{clip_name}.jpg")

        # Split 10-frame clip
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start_sec),
            "-i", video_path,
            "-t", str(duration_sec),
            "-vcodec", "copy",
            clip_path
        ], capture_output=True)

        # Extract first frame as static image
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start_sec),
            "-i", video_path,
            "-vframes", "1",
            static_path
        ], capture_output=True)

        # Config entry
        config[clip_name] = f"{folder_name}/{clip_name}.avi"

        # Animation entry
        if anim_type == "both":
            eye_desc = f"Eyes transition to {ek} expression"
            mouth_desc = f"Mouth transitions to {mk} expression"
        elif anim_type == "eye_anim_mouth_holds":
            eye_desc = f"Eyes transition to {ek} expression"
            mouth_desc = f"Mouth stays still at {mk}"
        elif anim_type == "eye_anim_mouth_static":
            eye_desc = f"Eyes transition to {ek} expression"
            mouth_desc = f"Mouth is held static at {mk} shape"
        else:
            eye_desc = f"Eyes held static at {ek} shape"
            mouth_desc = f"Mouth transitions to {mk} expression"

        animations[clip_name] = {
            "description": f"Eyes: {ek}, Mouth: {mk}. {eye_desc}. {mouth_desc}.",
            "anim_type": anim_type,
            "eye_key": ek,
            "mouth_key": mk,
            "video": f"{folder_name}/{clip_name}.avi",
            "static": f"Static/{clip_name}.jpg",
            "timeline": {
                "0-5": f"{eye_desc} starts. {mouth_desc}.",
                "5-10": f"{eye_desc} returns to neutral. {mouth_desc}."
            }
        }
        if (i+1) % 50 == 0:
            print(f"  {i+1}/{len(pairs)} done")

    print(f"  {len(pairs)}/{len(pairs)} done")

# Build full JSON
full_json = {"config": config, **animations}
json_path = os.path.join(OUT_BASE, "animations.json")
with open(json_path, "w") as f:
    json.dump(full_json, f, indent=2)
print(f"\nJSON saved: {json_path}")

# Convert to SQLite
db_path = os.path.join(OUT_BASE, "animations.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS animations (
    name TEXT PRIMARY KEY,
    description TEXT,
    anim_type TEXT,
    eye_key TEXT,
    mouth_key TEXT,
    video TEXT,
    static TEXT,
    timeline_0_5 TEXT,
    timeline_5_10 TEXT
)''')

for k, v in config.items():
    c.execute("INSERT OR REPLACE INTO config VALUES (?,?)", (k, v))

for name, data in animations.items():
    c.execute("INSERT OR REPLACE INTO animations VALUES (?,?,?,?,?,?,?,?,?)", (
        name,
        data["description"],
        data["anim_type"],
        data["eye_key"],
        data["mouth_key"],
        data["video"],
        data["static"],
        data["timeline"]["0-5"],
        data["timeline"]["5-10"]
    ))

conn.commit()
conn.close()
print(f"DB saved: {db_path}")
print("\nDone!")
