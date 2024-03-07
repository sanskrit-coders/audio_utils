import logging
import os
from indic_transliteration import sanscript
from curation_utils import file_helper

from audio_utils import audio_segment
from mutagen.easyid3 import EasyID3
# Remove all handlers associated with the root logger object.
from mutagen.id3 import ID3NoHeaderError

for handler in logging.root.handlers[:]:
  logging.root.removeHandler(handler)
logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s:%(asctime)s:%(module)s:%(lineno)d %(message)s"
)


# logging.warning("Logging.warning functional!")
# logging.info("Logging.info functional!")
# logging.getLogger('eyed3').setLevel(logging.INFO)


def get_easyId_metadata(key, audiofile):
  if key in audiofile:
    return audiofile[key][0]
  else:
    return None


class Mp3Metadata(object):
  """
  Models the metadata in an mp3 file.
  """

  def __init__(self, title=None, artist=None, album=None, album_artist=None):
    self.title = title
    self.artist = artist
    self.album = album
    self.album_artist = album_artist

  def __repr__(self):
    return "Title: %s, Artist: %s, Album: %s, Album artist: %s" % (
      self.title, self.artist, self.album, self.album_artist)

  @classmethod
  def from_file(cls, file_path):
    self = Mp3Metadata()
    self.get_from_file(file_path)
    return self

  def get_from_file(self, file_path):
    """

    """
    if not os.path.exists(file_path):
      raise FileNotFoundError(file_path)
    # eyed3 seems to fail in case of some files (" I use my iPhone (Voice Memos) to record and then use Apple iTunes to convert to MP3 format...").
    try:
      audiofile = EasyID3(file_path)
      if audiofile is None:
        raise Exception("Failed to load:" + file_path)
      # logging.debug("Loaded: " + file_path)
      self.artist = get_easyId_metadata("artist", audiofile=audiofile)
      self.title = get_easyId_metadata("title", audiofile=audiofile)
      self.album = get_easyId_metadata("album", audiofile=audiofile)
      self.album_artist = get_easyId_metadata("albumartist", audiofile=audiofile)
    except ID3NoHeaderError:
      audiofile = EasyID3()
      audiofile.save(file_path)

  def set_from_md_repo(self, mp3_path, ref_dir, id_maker=None):
    from doc_curation.md import library
    from doc_curation.md.file import MdFile
    sub_path_to_reference = library.get_sub_path_to_reference_map(ref_dir=ref_dir)
    def id_maker_default(x, sub_path_to_reference):
      id = library.get_sub_path_id(sub_path=id)
      return id
    if id_maker is None:
      id_maker = id_maker_default
    id = id_maker(mp3_path, sub_path_to_reference)
    if id in sub_path_to_reference:
      md_file = sub_path_to_reference[id]
      self.title = md_file.get_title(ref_dir_for_ancestral_title=ref_dir)

  def set_in_file(self, file_path):
    """

    """
    assert file_path.endswith(".mp3")
    # eyed3 seems to fail in case of some files (" I use my iPhone (Voice Memos) to record and then use Apple iTunes to convert to MP3 format...").
    audiofile = EasyID3(file_path)
    if audiofile is None:
      raise Exception("Failed to load:" + file_path)
    local_tag_update_needed = (get_easyId_metadata("artist", audiofile=audiofile) != self.artist) or (
        get_easyId_metadata("title", audiofile=audiofile) != self.title) or (
                                  get_easyId_metadata("album", audiofile=audiofile) != self.album) or (
                                  get_easyId_metadata("albumartist", audiofile=audiofile) != self.album_artist)

    if local_tag_update_needed:
      logging.info("***Updating %s locally." % file_path)
      logging.info("***Info: %s" % self)
      if self.artist is not None:
        audiofile["artist"] = self.artist
      if self.title is not None:
        audiofile["title"] = self.title
      if self.album is not None:
        audiofile["album"] = self.album
      if self.album_artist is not None:
        audiofile["albumartist"] = self.album_artist
      audiofile.save()


class Mp3File(object):
  """
  Represents an mp3 file, together with its metadata.
  """

  def __init__(self, file_path, mp3_metadata=None, load_tags_from_file=False, ref_md_repo=None):
    self.file_path = file_path
    self.directory = os.path.dirname(file_path)
    self.basename = os.path.basename(file_path)
    self.metadata = mp3_metadata if mp3_metadata is not None else Mp3Metadata()
    if load_tags_from_file:
      self.metadata.get_from_file(self.file_path)
    if ref_md_repo is not None:
      self.metadata.set_from_md_repo(mp3_path=self.file_path, ref_dir=ref_dir)


  def __repr__(self):
    return "Mp3File(%s)" % self.file_path

  def save_metadata(self):
    """
    Saves metadata in the corresponding file on disk.
    """
    self.metadata.set_in_file(file_path=self.file_path)

  def check_loudness(self):
    """ Get some loudness metric.

    :return: 
    """
    from pydub import AudioSegment
    sound = AudioSegment.from_mp3(self.file_path)
    return sound.dBFS

  def save_normalized(self, normalized_file_path, overwrite=False, speed_multiplier=1):
    """ Save the sound-normalized version of this file. 

    Currently the normalzied file produced will be mono-channel, around -16dbFS loud, have the same metadata as the original file.
    :param overwrite: 
    :return: 
    """
    if (not overwrite) and (os.path.isfile(normalized_file_path)):
      logging.warning("Not overwriting %s" % normalized_file_path)
      return
    from pydub import AudioSegment
    sound = AudioSegment.from_mp3(self.file_path)
    normalized_sound = audio_segment.normalize(sound)
    normalized_sound = audio_segment.strip_leading_trailing_silence(normalized_sound, max_init_silence_ms=500,
                                                                    max_trailing_silence_ms=500)

    logging.info(normalized_sound.dBFS)
    os.makedirs(os.path.dirname(normalized_file_path), exist_ok=True)
    self.metadata.get_from_file(self.file_path)
    normalized_sound.export(normalized_file_path, format="mp3", tags={
      "artist": self.metadata.artist, "album_artist": self.metadata.album_artist, "title": self.metadata.title,
      "album": self.metadata.album
    })

    if speed_multiplier != 1:
      Mp3File(file_path=normalized_file_path).speedup(speed_multiplier=speed_multiplier)

  def rename_to_title(self):
    new_basename = filename_from_title(self.metadata.title)
    new_filepath = os.path.join(self.directory, new_basename)
    logging.info("renaming %s to %s", self.file_path, new_filepath)
    os.rename(self.file_path, new_filepath)
    self.basename = new_basename
    self.file_path = new_filepath

  def title_from_filename(self):
    return self.basename[:-4].replace("_", " ")

  def speedup(self, speed_multiplier=1, out_file=None):
    # Not using pydub: pydub speedup is noticably worse than audacity or ffmpeg "change tempo" output - introduces weird effects in case of gamaka-s.
    import ffmpy
    edit_in_place = False
    if out_file == None:
      # Editing in-place: Move the file to a temporary location. ffmpeg cannot edit in place.
      edit_in_place = True
      unsped_file = self.file_path + ".tmp.mp3"
      os.rename(self.file_path, unsped_file)
      out_file = self.file_path
    else:
      unsped_file = self.file_path
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    ff = ffmpy.FFmpeg(inputs={unsped_file: None}, outputs={out_file: ["-filter:a", "atempo=" + str(speed_multiplier)]},
                      global_options="-y")
    ff.run()
    if edit_in_place:
      os.remove(unsped_file)


def filename_from_title(title):
  title_optitrans = file_helper.get_storage_name(text=title)
  title_fixed = title_optitrans.replace(".mp3", "")
  return title_fixed + ".mp3"


def normalize_all_in_place(file_paths):
  for file_path in file_paths:
    mp3_file = Mp3File(file_path)
    mp3_file.save_normalized(normalized_file_path=file_path, overwrite=True)
