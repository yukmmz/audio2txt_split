# %%
import os
import subprocess
import whisper
import ffmpeg
import sys

# %%



# %% functions

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except FileNotFoundError:
        return False
# ### enddef check_ffmpeg

def split_media_with_overlap(input_file, output_dir, segment_sec=600, overlap_sec=10):
    """
    MP4, MP3, M4A ファイルを10分ごとに、前後10秒のオーバーラップ付きで分割する。

    :param input_file: 分割するメディアファイル（MP4, MP3, M4A）
    :param output_dir: 分割後のファイルを保存するディレクトリ
    :param segment_sec: 各セグメントの長さ（秒）。デフォルト600秒 = 10分
    :param overlap: 各セグメントのオーバーラップ時間（秒）。デフォルト10秒
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 入力ファイルの拡張子を判別
    ext = os.path.splitext(input_file)[1].lower()
    if ext not in {".mp4", ".mp3", ".m4a"}:
        raise ValueError("対応しているファイル形式は MP4, MP3, M4A のみです。")

    # メディアの全体の長さを取得
    probe = ffmpeg.probe(input_file)
    duration_sec = float(probe['format']['duration'])  # ファイルの全体長さ（秒）

    # 分割処理（開始時間をずらしながら `ffmpeg` を実行）
    start_time = 0
    index = 1
    output_file_list = []
    print("Split Audio File...", end="")
    while start_time < duration_sec:
        output_file = os.path.join(output_dir, f"segment_{index:03d}{ext}")
        output_file_list.append(output_file)

        # `ffmpeg` を実行
        (
            # ffmpeg
            # .input(input_file, ss=start_time)  # 開始時間を指定
            # .output(output_file, t=segment_sec)  # 長さを指定
            # .run(overwrite_output=True)
            
            ffmpeg.input(input_file, ss=start_time, t=segment_sec)  # 開始時間を指定
            .output(output_file)  # 長さを指定
            .run(overwrite_output=True)
        )

        # 次の開始時間を更新（オーバーラップを考慮）
        start_time += segment_sec - overlap_sec
        index += 1
    
    print("done.")

    out = {
        'duration_sec':duration_sec,
        'output_file_list':output_file_list
    }
    return out
# ### enddef split_media_with_overlap

def transcribe_audio(audio_path, model_size, log_path, language):
    
    # sys.stderr = sys.stdout
    
    # load model
    model = whisper.load_model(model_size)

    print('stdout will be saved to:', log_path)
    original_stdout = sys.stdout
    sys.stdout = open(log_path, 'a', encoding='utf-8')
    try:
        # transcribe audio file
        # result = model.transcribe(audio_path)
        # print("# start transcription. -------------------")
        result = model.transcribe(audio_path, verbose=True, fp16=False, language=language)
        # print("## end transcription. -------------------")

        # print("## Finished transcription.")

    except Exception as e:
        print(f"[Err] Error has raised!!!:{e}")
        print("[Err] Detail:")
        import traceback
        traceback.print_exc()
    sys.stdout.close()
    sys.stdout = original_stdout
# ### enddef transcribe_audio

def trunc_log_from_whisper(log_path, transcribe_res_path):
    with open(log_path, 'r', encoding='UTF-8') as fileobject:
        contents = fileobject.readlines() # list of lines

    with open(transcribe_res_path, 'w', encoding='UTF-8') as fileobject:
        flag_log = 0
        for i_line, line in enumerate(contents):
            # print(f'{i_line}: {line}', end='')
            if line.startswith('## end transcription.'):
                flag_log = 0
            elif line.startswith('# start transcription.'):
                flag_log = 1
            elif flag_log:
                # print log
                txt = line.split('] ')[1]
                fileobject.write(txt)
            
            # if line.startswith('['):
            #     txt = line.split('] ')[1]
            #     fileobject.write(txt)

    print(f'saved to {transcribe_res_path}')
# ### enddef trunc_log_from_whisper


def delete_file_if_exists(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f'deleted {file_path}')
    else:
        print(f'{file_path} not found.')
# ### enddef delete_file_if_exists

def make_dir_if_not_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f'directory created: {dir_path}')
    else:
        print(f'directory already exists: {dir_path}')
# ### enddef make_dir_if_not_exists

def make_or_clear_dir(dir_in):
    if not os.path.exists(dir_in):
        os.makedirs(dir_in)
    else:
        # delete all files in the directory
        for file_name in os.listdir(dir_in):
            file_path = os.path.join(dir_in, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
# ### enddef make_or_clear_dir



# %% main process
if __name__ == "__main__":
        
    # %% preprocess
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not check_ffmpeg():
        print("[Err] FFmpeg is not installed, or not added to PATH.")
        print("[Err] Please install FFmpeg and add to PATH, then try again.")
        exit()


    # %% get args
    audio_path = input("Input audio file path:")
    print(f"Audio file: {audio_path}")

    segment_sec = input("Segment length [s] (Enter->600[s]):")
    if segment_sec == "":
        segment_sec = 600
    else:
        segment_sec = int(segment_sec)
    print(f"Segment length: {segment_sec}[s]")

    overlap_sec = input("Overlap length [s] (Enter->10[s]):")
    if overlap_sec == "":
        overlap_sec = 10
    else:
        overlap_sec = int(overlap_sec)
    print(f"Overlap length: {overlap_sec}[s]")
    

    while 1:
        model_size = input("Model size (tiny, base, small, medium, large) (Enter->small):")
        if model_size == "":
            model_size = "small"
        if model_size not in ["tiny", "base", "small", "medium", "large", "turbo"]:
            print(f"Invalid model size: {model_size}")
            continue
        elif model_size == "turbo":
            ans = input("Model size 'turbo' is not recommended. continue? (y/n):")
            if ans.lower() == "y":
                break
            else:
                continue
        else:
            break
    print(f"Model size: {model_size}")

    language = input("Language (en, ja, de, fr...) (Enter->ja):")
    if language == "":
        language = "ja"
    print(f"Language: {language}")

    # %% setttings ------------------------
    audio_basename = os.path.splitext(os.path.basename(audio_path))[0]
    outputDirPath = os.path.join("..", "output")
    audio_split_dir = os.path.join("..", "tmp")
    log_path = os.path.join(outputDirPath, f"log_{audio_basename}.txt")
    transcribe_res_path = os.path.join(outputDirPath, f"transcribe_{audio_basename}.txt")
    ### ----------------------------------

    if not os.path.isfile(audio_path):
        print(f'[Err] Audio file not found: {audio_path}')
        exit()

    make_dir_if_not_exists(outputDirPath)
    delete_file_if_exists(log_path)

    print(f"Log file: {log_path}")
    print(f"Transcribe result file: {transcribe_res_path}")


    # %% split audio file
    make_or_clear_dir(audio_split_dir)
    out = split_media_with_overlap(audio_path, audio_split_dir, segment_sec, overlap_sec)

    # %% log settings and states
    with open(log_path, 'a', encoding='utf-8') as fileobject:
        fileobject.write(f"# Current Directory\n{os.getcwd()}\n")
        fileobject.write(f"# Input Audio File\n{audio_path}\n")
        fileobject.write(f"# audio length [min]\n{int(out['duration_sec']/60)}\n")
        fileobject.write(f"# number of audio split\n{len(out['output_file_list'])}\n")
        fileobject.write(f"# Model Size\n{model_size}\n")

    # %% transcribe each audio file
    with open(log_path, 'a', encoding='utf-8') as fileobject:
        fileobject.write("# start transcription. -------------------\n")
    for i_file, audio_path in enumerate(out['output_file_list']):
        print(f"[{i_file}/{len(out['output_file_list'])}] transcribing {audio_path}...", end="")
        transcribe_audio(audio_path, model_size, log_path, language)
        print("done")
    with open(log_path, 'a', encoding='utf-8') as fileobject:
        fileobject.write("## end transcription. -------------------\n")


    # %% edit log file.
    trunc_log_from_whisper(log_path, transcribe_res_path)

    print('Transcription completed.')
    exit()

# ### endif __name__ == "__main__"