import os
import streamlit as st
import cv2
import moviepy.editor as mp
from pydub import AudioSegment
import uuid
import tempfile
import subprocess
from another_trial import (
    extract_frames, get_image_information, create_srt_file, 
    extract_audio_from_video, transcribe_audio, 
    create_audio_from_descriptions, merge_audio_with_video
)

# Path to ffmpeg executable (use just 'ffmpeg' to rely on the PATH)
ffmpeg_path = "ffmpeg"

# Set up Streamlit
st.title("📽️ Video Summary Generator")
st.write("Upload a video file and get an audio transcription of its content.")

# Foldable sidebar for settings and controls
with st.sidebar:
    st.markdown("""
    ### ListenIn
    ListenIn is an AI-powered tool that allows you to upload a video file and get a detailed summary of its content, including transcriptions and scene descriptions. Simply upload your video, and let ListenIn do the rest!
    """)
 
# Create temporary directories
temp_dir = tempfile.TemporaryDirectory()
frames_directory = os.path.join(temp_dir.name, "uploaded_frames")
output_directory = os.path.join(temp_dir.name, "output_videos")
temp_audio_directory = os.path.join(temp_dir.name, "temp_audio")

# Ensure directories exist
for directory in [frames_directory, output_directory, temp_audio_directory]:
    os.makedirs(directory, exist_ok=True)

# File uploader
uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    # Save the uploaded video to a temporary file
    temp_video_path = os.path.join(temp_audio_directory, uploaded_file.name)
    
    with open(temp_video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.write(f"Uploaded {uploaded_file.name}")

    # Initialize temp_audio_path with None
    temp_audio_path = None

    try:
        # Extract frames
        video_clip = mp.VideoFileClip(temp_video_path)
        video_duration = video_clip.duration
        num_descriptions = int(video_duration // 5)
        frame_rate = extract_frames(temp_video_path, frames_directory, num_descriptions)
        
        # Generate descriptions for frames (example, replace with your logic)
        frame_files = sorted([os.path.join(frames_directory, f) for f in os.listdir(frames_directory) if f.endswith('.jpg')])
        descriptions = [get_image_information(frame) for frame in frame_files]

        # Create SRT file
        video_name = os.path.splitext(os.path.basename(temp_video_path))[0]
        output_srt_path = os.path.join(output_directory, f"video_captions_{video_name}.srt")
        create_srt_file(descriptions, output_srt_path, frame_rate)
        
        text_transcribed = ""
        # Process audio
        temp_audio_path = os.path.join(temp_audio_directory, f"temp_audio_{uuid.uuid4()}.mp3")
        audio_extraction_result = extract_audio_from_video(temp_video_path, temp_audio_path)
        if audio_extraction_result != "No audio track found in the video.":
            text_transcribed = transcribe_audio(temp_audio_path)
            create_audio_from_descriptions(descriptions, text_transcribed, temp_audio_path)
        else:
            temp_audio_path = None

        # Merge audio with video
        output_video_path = os.path.join(output_directory, f"output_video_with_audio_{video_name}.mp4")
        if temp_audio_path:
            merge_audio_with_video(temp_video_path, temp_audio_path, output_video_path)
        else:
            output_video_path = temp_video_path
        
        # Merge the SRT file with the video using ffmpeg
        final_output_path = os.path.join(output_directory, f"output_video_with_captions_{video_name}.mp4")
        ffmpeg_command = [
            ffmpeg_path, '-i', output_video_path, '-vf', 
            f"subtitles='{output_srt_path}:force_style=Fontsize=24'", final_output_path
        ]

        # Print the command for debugging
        #st.write("Running ffmpeg command:", " ".join(ffmpeg_command))

        result = subprocess.run(ffmpeg_command, capture_output=True, text=True, bufsize=1048576)
        #st.write("FFmpeg stdout:", result.stdout)
        #st.write("FFmpeg stderr:", result.stderr)

        # Check if ffmpeg was successful
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed with return code {result.returncode}")

        st.success("Summary generated!")
        
        # Verify if the final output file exists before displaying
        if os.path.exists(final_output_path):
            st.video(final_output_path)
        else:
            st.error(f"Final output video not found at {final_output_path}")

    except Exception as e:
        st.error(f"An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        for file in os.listdir(frames_directory):
            os.remove(os.path.join(frames_directory, file))
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        temp_dir.cleanup()
else:
    st.write("Please upload a video file.")
