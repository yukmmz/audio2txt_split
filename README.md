# audio2txt_split
audio2txt_split handles transcription of long audio files.
It first splits the audio files, and then transcribe each of them with [openai-whisper](https://github.com/openai/whisper). 
This splitting process somehow leads to better results than just throwing the long audio files to openai-whisper.

## Installation
1. Clone or download this repository.
1. install some libraries.
    ```
    pip install ffmpeg-python
    pip install git+https://github.com/openai/whisper.git
    ```
1. You also need to install [ffmpeg](https://ffmpeg.org/download.html), then add its "bin" directory to PATH, or copy three executable files to "src" directory of audio2txt_split.

## Usage
Run `src/audio2txt_split.py`, then answer the question about the audio file path and options.

After execution, you can find `output\transcribe_{audio_filename}.txt`.
Some execution options are written in `output\log_{audio_file_name}.txt`.

