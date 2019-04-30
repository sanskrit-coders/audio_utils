# Inspirations: https://stackoverflow.com/questions/44894796/pyaudio-and-pynput-recording-while-a-key-is-being-pressed-held-down, https://gist.github.com/sloria/5693955
import logging
import os
import sched
import time
import wave

import pyaudio
from pydub import AudioSegment
from pynput import keyboard


for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:%(asctime)s:%(module)s:%(lineno)d %(message)s"
)


class KeyPressTriggeredRecorder(object):
    '''Helps record audio during the duration of key-presses.
    Records in mono by default.
    
    Example usage:
        recorder.KeyPressTriggeredRecorder("test.wav").record()
    '''

    def __init__(self, trigger_key=keyboard.Key.ctrl_l, channels=1, rate=44100, frames_per_buffer=1024):
        self.trigger_key = trigger_key
        self._key_pressed = False
        self._recording_started = False
        self._recording_stopped = False
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self._key_listener = keyboard.Listener(self._on_press, self._on_release)
        self._task_scheduler = sched.scheduler(time.time, time.sleep)
        self._pa = pyaudio.PyAudio()

    def reset(self):
        self._key_pressed = False
        self._recording_started = False
        self._recording_stopped = False

    def _on_press(self, key):
        # logging.info(key)
        if key == self.trigger_key:
            self._key_pressed = True
        return True

    def _on_release(self, key):
        # logging.info(key)
        if key == self.trigger_key:
            self._key_pressed = False
            # Close listener
            return False
        return True

    def record(self, fname):
        self.reset()
        self._key_listener.start()
        recording_file = RecordingFile(
            fname=fname, mode='wb', channels=self.channels, rate=self.rate,
            frames_per_buffer=self.frames_per_buffer, pyaudio_obj=self._pa)
        logging.info("Recording: %s at %s", os.path.basename(fname), fname )
        logging.info("Record while you keep pressing: %s", self.trigger_key)
        while not self._recording_stopped:
            if self._key_pressed and not self._recording_started:
                recording_file.start_recording()
                self._recording_started = True
            elif not self._key_pressed and self._recording_started:
                recording_file.stop_recording()
                self._recording_stopped = True
            time.sleep(.1)


class RecordingFile(object):
    """"Type of object corresponding to a particular recording.
    
    See :py:class:KeyPressTriggeredRecorder for example usage.
    """
    def __init__(self, fname, mode, channels,
                 rate, frames_per_buffer, pyaudio_obj):
        self.final_fname = fname
        self._fname_wav = fname.replace(".mp3", ".wav")
        self.mode = mode
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self._pa = pyaudio_obj
        self._wavefile = self._prepare_file(self._fname_wav, self.mode)
        self._stream = None

    def __enter__(self):
        return self

    def __exit__(self, exception, value, traceback):
        self.close()

    def start_recording(self):
        # Use a stream with a callback in non-blocking mode
        # logging.info("Starting recording")
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                     channels=self.channels,
                                     rate=self.rate,
                                     input=True,
                                     frames_per_buffer=self.frames_per_buffer,
                                     stream_callback=self._get_callback())
        self._stream.start_stream()
        return self

    def stop_recording(self):
        self._stream.stop_stream()

        if self.final_fname.endswith(".mp3"):
            self.to_normalized_mp3()
            os.remove(self._fname_wav)
        return self

    def _get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self._wavefile.writeframes(in_data)
            return in_data, pyaudio.paContinue
        return callback

    def close(self):
        self._stream.close()
        self._pa.terminate()
        self._wavefile.close()

    def to_normalized_mp3(self):
        sound = AudioSegment.from_wav(self._fname_wav)
        from audio_utils import audio_segment
        sound = audio_segment.normalize(sound)
        sound.export(self.final_fname, format="mp3")

    def _prepare_file(self, fname, mode='wb'):
        import os
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        wavefile = wave.open(fname, mode)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile
