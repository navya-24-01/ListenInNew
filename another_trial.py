

from langchain_openai import ChatOpenAI
import base64
import os
from typing import List

from gtts import gTTS


llm = ChatOpenAI(
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key="sk-proj-L8hAwiCGh9EuhwDNHiIXT3BlbkFJeneRXBwVVXcHoSWg9l2T",
)

print(llm.invoke("Good mo"))


def load_image(inputs: dict) -> dict:
    """Load image from file and encode it as base64."""
    image_path = inputs["image_path"]

    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    image_base64 = encode_image(image_path)
    return {"image": image_base64}

from langchain.chains import TransformChain
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain import globals
from langchain_core.runnables import chain

load_image_chain = TransformChain(
    input_variables=["image_path"],
    output_variables=["image"],
    transform=load_image
)

# Set verbose
globals.set_debug(True)

@chain
def image_model(inputs: dict) -> str:
    model = ChatOpenAI(temperature=0.5, max_tokens=1024, model="gpt-4o", api_key="sk-proj-L8hAwiCGh9EuhwDNHiIXT3BlbkFJeneRXBwVVXcHoSWg9l2T")
    msg = model.invoke(
        [HumanMessage(
            content=[
                {"type": "text", "text": inputs["prompt"]},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{inputs['image']}"}},
            ])]
    )
    return msg.content if msg else ""

def get_image_information(image_path: str) -> str:
    vision_prompt = "Describe the image you see.limit to 15 words, cannot exceed! Reading the description should be limited to 5 seconds"
    vision_chain = load_image_chain | image_model 
    response = vision_chain.invoke({'image_path': image_path, 'prompt': vision_prompt})
    return response



from moviepy.editor import VideoFileClip

def extract_audio_from_video(video_path, output_audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    if audio is None:
        print("No audio track found in the video.")
        return "No audio track found in the video."
    audio.write_audiofile(output_audio_path)


import whisper
import ssl
import certifi
from urllib.request import urlopen

# Set SSL context globally
context = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: context

def transcribe_audio(audio_file_path):
    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_file_path)
        print(result["text"])
        return result["text"]
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return f"Error: {e}"

text_transcribed = ""



import cv2
import os
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip

def extract_frames(video_path, frames_directory, num_descriptions):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open the video file: Check the path or file format.")
    if not os.path.exists(frames_directory):
        os.makedirs(frames_directory)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    frame_id = 0
    video_duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / frame_rate
    frame_interval = max(int((video_duration * frame_rate) / num_descriptions),40)
    while True:
        success, frame = cap.read()
        if not success:
            break
        if frame_id % frame_interval == 0:
            timestamp = frame_id / frame_rate
            timestamp_formatted = f'{timestamp:.2f}'
            frame_filename = os.path.join(frames_directory, f'timestamp_{timestamp_formatted}.jpg')
            if frame is not None and not frame.size == 0:
                cv2.imwrite(frame_filename, frame)
        frame_id += 1
    cap.release()
    return frame_rate


##generate every four frames
def create_srt_file(descriptions, output_srt_path, frame_rate):
    with open(output_srt_path, 'w') as f:
        for i, description in enumerate(descriptions):
            start_time = (i) / frame_rate
            end_time = ((i + 1)) / frame_rate
            start_time_str = format_time(start_time)
            end_time_str = format_time(end_time)
            f.write(f"{i + 1}\n")
            f.write(f"{start_time_str} --> {end_time_str}\n")
            f.write(f"{description}\n\n")

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def create_audio_from_descriptions(descriptions, text_transcribed, output_audio_path):
    full_descriptions = " ".join(descriptions)
    full_text = full_descriptions + text_transcribed
    summary_prompt = f"The following descriptions are for video frames, followed by transcribed text for the entire video. Paraphrase a bit to have coherence and connection between sentences, and be shorter. Do not exceed the total length of the original text ({len(full_descriptions)})!!:\n\n{full_text}"

    summary_message = llm.invoke(summary_prompt)
    tts = gTTS(text=summary_message.content, lang='en')
    tts.save(output_audio_path)


def merge_audio_with_video(video_path, audio_path, output_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")


# ---transcribe, if needed---
