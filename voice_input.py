import pvporcupine
import struct
import pyaudio
import wave
import time
import speech_recognition as sr

access_key = 'your_api_key'
porcupine = pvporcupine.create(
  access_key=access_key,
  keyword_paths=['smartER.ppn']
)


pa = pyaudio.PyAudio()
stream = pa.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=porcupine.sample_rate,
    input=True,
    frames_per_buffer=porcupine.frame_length  
)


recognizer = sr.Recognizer()

def get_next_audio_frame():
    return stream.read(porcupine.frame_length)

def start_recording():
    print("Recording...")
    frames = []
    silence_threshold = 3  # seconds before stop recording to process voice 2 text
    silent_frames = 0
    non_silent_duration = 0

    while True:
        audio_frame = get_next_audio_frame()
        frames.append(audio_frame)

        if is_silent(audio_frame):
            silent_frames += 1
            if silent_frames > silence_threshold * (porcupine.sample_rate / porcupine.frame_length):
                if non_silent_duration > 0.5:  
                    break
                else:
                    frames = []  
                    silent_frames = 0
        else:
            silent_frames = 0
            non_silent_duration += 1

    return frames

def is_silent(audio_frame):
    pcm_data = wave.struct.unpack_from("%dh" % porcupine.frame_length, audio_frame)
    return max(pcm_data) < 500 

def save_audio(frames, filename="recording.wav"):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
    wf.setframerate(porcupine.sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def recognize_speech(filename):
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        print("You said: " + text)
    except sr.UnknownValueError:
        print("Google Speech Unknown Error;")
    except sr.RequestError as e:
        print(f"Google Speech Request Error; {e}")

print("Listening for wake words...")
try:
    while True:
        audio_frame = get_next_audio_frame()
        audio_frame = struct.unpack_from("h" * porcupine.frame_length, audio_frame)
        keyword_index = porcupine.process(audio_frame)
        
        if keyword_index >= 0:
            print("Wake word detected!")
            frames = start_recording()
            save_audio(frames)
            recognize_speech("recording.wav")
except KeyboardInterrupt:
    print("Stopping...")
finally:
    # Cleanup
    stream.stop_stream()
    stream.close()
    pa.terminate()
    porcupine.delete()