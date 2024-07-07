import os
import streamlit as st
import cv2
from another_trial import *
import moviepy.editor as mp
from pydub import AudioSegment
import uuid

# Set up Streamlit
st.title("Video Summary Generator")
st.write("Upload a video file and get a summary of its content.")

# File uploader
uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi", "mkv"])

# Directories to save frames, audio, and output video
frames_directory = "uploaded_frames"
output_directory = "output_videos"
temp_directory = "temp"

# Create directories if they don't exist
for directory in [frames_directory, output_directory, temp_directory]:
    if not os.path.exists(directory):
        os.makedirs(directory)

if uploaded_file is not None:
    # Save the uploaded video to a temporary file
    temp_video_path = os.path.join(temp_directory, uploaded_file.name)
    
    with open(temp_video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.write(f"Uploaded {uploaded_file.name}")

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
        temp_audio_path = os.path.join(temp_directory, f"temp_audio_{uuid.uuid4()}.mp3")
        if extract_audio_from_video(temp_video_path, temp_audio_path) != "No audio track found in the video.":
            text_transcribed = transcribe_audio("original_audio.mp3")

        create_audio_from_descriptions(descriptions, text_transcribed, temp_audio_path)

        # Merge audio with video
        output_video_path = os.path.join(output_directory, f"output_video_with_audio_{video_name}.mp4")
        merge_audio_with_video(temp_video_path, temp_audio_path, output_video_path)
        
        # Merge the SRT file with the video using ffmpeg
        final_output_path = os.path.join(output_directory, f"output_video_with_captions_{video_name}.mp4")
        os.system(f'ffmpeg -i {output_video_path} -vf "subtitles={output_srt_path}:force_style=\'Fontsize=24\'" {final_output_path}')

        st.success("Summary generated!")
        
        # Display the output video with captions
        st.video(final_output_path)

    except Exception as e:
        st.error(f"An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        for file in os.listdir(frames_directory):
            os.remove(os.path.join(frames_directory, file))
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

else:
    st.write("Please upload a video file.")
