"""
Video Renderer Script
Renders the scenes, generates the soundtrack, and combines them into the final .mp4 video.

Usage:
    python3 render.py           # Renders how_targeted_chat_scanning_works.mp4 (from system.py)
    python3 render.py system    # Renders how_targeted_chat_scanning_works.mp4
    python3 render.py make      # Renders presentation.mp4 (from make.py)
"""
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def render_target(target="system"):
    if target == "system":
        import system
        scenes = system.SCENES
        script_name = "system.py"
        output_file = os.path.join(BASE_DIR, "how_targeted_chat_scanning_works.mp4")
        temp_dir = os.path.join(BASE_DIR, "_temp_system_scenes")
    elif target == "make":
        import make
        scenes = make.SCENES
        script_name = "make.py"
        output_file = os.path.join(BASE_DIR, "presentation.mp4")
        temp_dir = os.path.join(BASE_DIR, "_temp_make_scenes")
    else:
        print(f"Unknown target: {target}. Choose 'system' or 'make'.")
        sys.exit(1)

    os.makedirs(temp_dir, exist_ok=True)
    total_duration = sum(dur for _, _, dur in scenes)
    print(f"=== Rendering {target} ({len(scenes)} scenes, {total_duration:.1f}s) ===")

    # 1. Render scene video clips
    print("\n[1/3] Rendering video scene clips...")
    cmd_scenes = [sys.executable, os.path.join(BASE_DIR, script_name), temp_dir, "video"]
    subprocess.run(cmd_scenes, check=True)

    # 2. Render background music
    print("\n[2/3] Generating background music...")
    audio_path = os.path.join(temp_dir, "music.wav")
    cmd_music = [sys.executable, os.path.join(BASE_DIR, "music.py"), audio_path, str(total_duration)]
    subprocess.run(cmd_music, check=True)

    # 3. Concatenate scenes and merge audio
    print("\n[3/3] Combining video and audio with FFmpeg...")
    concat_list_path = os.path.join(temp_dir, "concat.txt")
    with open(concat_list_path, "w") as f:
        for name, _, _ in scenes:
            scene_path = os.path.join(temp_dir, f"{name}.mp4")
            f.write(f"file '{scene_path}'\n")

    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_file
    ]
    subprocess.run(cmd_concat, check=True)
    print(f"\nSUCCESS: Video saved to {output_file}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "system"
    render_target(target)
