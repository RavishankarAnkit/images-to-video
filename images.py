import streamlit as st
import os
import glob
import tempfile

# Handling MoviePy version differences
try:
    from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
except ImportError:
    from moviepy import ImageClip, concatenate_videoclips, AudioFileClip

import yt_dlp

# =========================
# SESSION STATE
# =========================

if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = None

# =========================
# CLEANUP FUNCTION
# =========================

def cleanup_temp_files():

    files = glob.glob("temp_*") + ["output_video.mp4"]

    for f in files:

        try:
            os.remove(f)

        except:
            pass

    st.session_state['audio_path'] = None

# =========================
# DOWNLOAD YOUTUBE AUDIO
# =========================

def download_youtube_audio(url):

    audio_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',

        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/122.0.0.0 Safari/537.36'
            ),
        },

        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        ydl.download([url])

    return "temp_audio.mp3"

# =========================
# CREATE VIDEO
# =========================

def create_video(image_files, duplicate_count, fps, audio_path):

    clips = []

    duration_per_image = duplicate_count / fps

    target_resolution = (1280, 720)

    # Process Images
    for idx, img_file in enumerate(image_files):

        temp_img_path = f"temp_img_{idx}.png"

        with open(temp_img_path, "wb") as f:
            f.write(img_file.getbuffer())

        try:
            clip = (
                ImageClip(temp_img_path)
                .with_duration(duration_per_image)
                .resized(target_resolution)
            )

        except:
            # Fallback for older MoviePy
            clip = (
                ImageClip(temp_img_path)
                .set_duration(duration_per_image)
                .resize(target_resolution)
            )

        clips.append(clip)

    # Merge Clips
    final_video = concatenate_videoclips(clips, method="compose")

    try:
        final_video = final_video.with_fps(fps)

    except:
        final_video = final_video.set_fps(fps)

    # Add Audio
    audio_clip = AudioFileClip(audio_path)

    if audio_clip.duration > final_video.duration:

        try:
            audio_clip = audio_clip.with_duration(final_video.duration)

        except:
            audio_clip = audio_clip.subclip(0, final_video.duration)

    try:
        final_clip = final_video.with_audio(audio_clip)

    except:
        final_clip = final_video.set_audio(audio_clip)

    # Export
    output_filename = "output_video.mp4"

    final_clip.write_videofile(
        output_filename,
        codec="libx264",
        audio_codec="aac"
    )

    return output_filename

# =========================
# STREAMLIT PAGE
# =========================

st.set_page_config(
    page_title="PragyanAI Video Creator",
    layout="wide"
)

# Logo
if os.path.exists("PragyanAI_Transperent.png"):

    st.image("PragyanAI_Transperent.png")

# Title
st.title("🎬 PragyanAI Multimedia Merger")

st.markdown(
    "Upload multiple images and merge them with audio "
    "from a file or YouTube."
)

# =========================
# SIDEBAR
# =========================

with st.sidebar:

    st.header("⚙ Video Settings")

    fps = st.slider(
        "Frames Per Second (FPS)",
        1,
        60,
        24
    )

    duplicates = st.number_input(
        "Frames per Image",
        min_value=1,
        value=48
    )

    if st.button("🗑 Clear Temp Files"):

        cleanup_temp_files()

        st.success("Temporary files cleared!")

# =========================
# MAIN UI
# =========================

col1, col2 = st.columns(2)

# =========================
# IMAGE SECTION
# =========================

with col1:

    st.subheader("🖼 Upload Images")

    uploaded_images = st.file_uploader(
        "Upload Image Sequence",
        type=["jpg", "png", "jpeg"],
        accept_multiple_files=True
    )

    if uploaded_images:

        st.success(f"{len(uploaded_images)} images uploaded!")

# =========================
# AUDIO SECTION
# =========================

with col2:

    st.subheader("🎵 Audio Source")

    audio_option = st.radio(
        "Choose Audio Source",
        ["Upload Audio File", "YouTube Link"]
    )

    # Upload Audio
    if audio_option == "Upload Audio File":

        uploaded_audio = st.file_uploader(
            "Upload Audio",
            type=["mp3", "wav", "m4a"]
        )

        if uploaded_audio:

            audio_path = f"temp_audio_{uploaded_audio.name}"

            with open(audio_path, "wb") as f:
                f.write(uploaded_audio.getbuffer())

            st.session_state['audio_path'] = audio_path

            st.success("Audio uploaded successfully!")

    # YouTube Audio
    else:

        yt_url = st.text_input("Enter YouTube URL")

        if st.button("⬇ Download YouTube Audio"):

            if yt_url:

                with st.spinner("Downloading audio..."):

                    try:

                        downloaded_audio = download_youtube_audio(yt_url)

                        st.session_state['audio_path'] = downloaded_audio

                        st.success("YouTube audio downloaded!")

                    except Exception as e:

                        st.error(f"Download failed:\n\n{e}")

# =========================
# CREATE VIDEO BUTTON
# =========================

st.markdown("---")

if st.button("🎥 Create Video"):

    if not uploaded_images:

        st.error("Please upload images.")

    elif not st.session_state['audio_path']:

        st.error("Please upload or download audio.")

    else:

        with st.spinner("Creating video..."):

            try:

                output_video = create_video(
                    uploaded_images,
                    duplicates,
                    fps,
                    st.session_state['audio_path']
                )

                st.success("✅ Video created successfully!")

                # Preview
                st.video(output_video)

                # Download
                with open(output_video, "rb") as file:

                    st.download_button(
                        label="⬇ Download Video",
                        data=file,
                        file_name="PragyanAI_Output.mp4",
                        mime="video/mp4"
                    )

            except Exception as e:

                st.error(f"Video creation failed:\n\n{e}")
