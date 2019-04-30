import logging
logging.getLogger("pydub.converter").setLevel(logging.WARNING)

def normalize(sound):
    # logging.debug(sound.dBFS)
    # Convert to mono.
    normalized_sound = sound.set_channels(1)
    # Set loudness to the standard level:  -16LUFS or roughly -16dbFS
    # Eventually we would want to use LUFS. One would need to switch libraries or await resolution of https://github.com/jiaaro/pydub/issues/321 .
    normalized_sound = normalized_sound.apply_gain(-16 - sound.dBFS)
    return normalized_sound

## TODO: Move this to pydub.silence - https://github.com/jiaaro/pydub/pull/335
def detect_leading_silence(sound, silence_threshold=-50.0, chunk_size=10):
    '''
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    '''
    trim_ms = 0 # ms

    assert chunk_size > 0 # to avoid infinite loop
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size

    return trim_ms

def strip_leading_trailing_silence(sound, max_init_silence_ms, max_trailing_silence_ms):
    # Remove leading and ending silence beyond 1s and .5s respectively
    start_trim = max(detect_leading_silence(sound) - max_init_silence_ms, 0)
    end_trim = max(detect_leading_silence(sound.reverse()) - max_trailing_silence_ms, 0)

    duration = len(sound)
    return sound[start_trim:duration-end_trim]
    