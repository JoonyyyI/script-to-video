import streamlit as st
import re
import pandas as pd
import io

# --------- Parsing ----------
def parse_script(text):
    scenes = []
    title = ""
    blocks = text.strip().split("#scene")
    for i, block in enumerate(blocks[1:]):
        header, *body = block.strip().split("\n")
        if i == 0:
            title = body[0] if len(body) > 0 else ""
        scene_number = re.findall(r'\d+', header)[0]
        timing = re.findall(r'\((.*?)\)', header)
        content = "\n".join(body).strip()
        scenes.append({
            "scene": int(scene_number),
            "timing": timing[0] if timing else None,
            "text": content
        })
    return title, scenes

# --------- Timing ----------
def estimate_timings(scenes, avg_wpm=200):
    timings = []
    for s in scenes:
        words = len(s['text'].replace("\n", " ").split())
        seconds = round((words / avg_wpm) * 60, 1)
        timings.append(seconds)
    return timings

# --------- Subtitle Generation (.srt) ----------
def generate_srt(title, scenes, durations):
    srt = ""
    current_time = 0.0
    idx = 1

    # Title as fixed top subtitle
    srt += f"{idx}\n00:00:00,000 --> 00:00:40,000\n{title}\n\n"
    idx += 1

    for scene, duration in zip(scenes, durations):
        start = format_time(current_time)
        end = format_time(current_time + duration)
        srt += f"{idx}\n{start} --> {end}\n{scene['text']}\n\n"
        current_time += duration
        idx += 1
    return srt.encode("utf-8")

def format_time(t):
    mins, secs = divmod(int(t), 60)
    millis = int((t - int(t)) * 1000)
    return f"00:{mins:02}:{secs:02},{millis:03}"

# --------- Excel for Cut Timing ----------
def generate_xlsx(scenes, durations):
    rows = []
    current_time = 0.0
    for s, dur in zip(scenes, durations):
        rows.append({
            "Scene": s['scene'],
            "Start": round(current_time, 2),
            "End": round(current_time + dur, 2),
            "Text": s['text']
        })
        current_time += dur
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()

# --------- UI ----------
st.title("🎬 제목 + 대본만 입력하면 영상 자막 자동 생성")

title = st.text_input("📌 영상 제목 (상단 고정 자막)")
script = st.text_area("✍️ 대본 입력창 (scene 단위)", height=300, placeholder="#scene1 (0~3초)\n대본...")

if st.button("🚀 자막 생성"):
    parsed_title, scenes = parse_script(script)
    title = title if title else parsed_title
    timings = estimate_timings(scenes)
    srt_data = generate_srt(title, scenes, timings)
    xlsx_data = generate_xlsx(scenes, timings)

    st.success("✅ 자막 생성 완료!")
    st.download_button("📥 자막 파일 (.srt)", srt_data, file_name="subtitles.srt")
    st.download_button("📥 컷 구성표 (.xlsx)", xlsx_data, file_name="capcut_cuts.xlsx")
