import ffmpeg
import sys
import os
import speech_recognition as speech_recog
from deep_translator import GoogleTranslator

DURATION = 19


def convert_to_time_format(sec):
    sec = sec % (24 * 3600)
    hour = sec // 3600
    sec %= 3600
    min = sec // 60
    sec %= 60
    millisec = sec % 1
    return "%02d:%02d:%02d,%02d" % (hour, min, sec, millisec)


def extract_audio(filename):
    try:
        (
            ffmpeg
                .input(filename)
                .output('test.wav')
                .overwrite_output()
                .run()
        )
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)


outputSpeech = []


def speech_recognize(in_time):
    sample_audio = speech_recog.AudioFile('test.wav')
    recog = speech_recog.Recognizer()
    with sample_audio as audio_file:
        recog.adjust_for_ambient_noise(audio_file)
        audio_content = recog.record(audio_file, offset=in_time, duration=4)
    try:
        outputSpeech.append(recog.recognize_google(audio_content, language='en-IN'))
    except Exception as e:
        print("Error: " + str(e))


def replace_subs(file_path, input_text):
    f = open(file_path, "w", encoding='UTF-16')
    episode = 4
    if DURATION % episode == 0:
        for i in range(DURATION // episode):
            f.write(str(i + 1) + '\n')
            f.write(convert_to_time_format(i * episode) + '-->' + convert_to_time_format((i + 1) * episode) + '\n')
            f.write(input_text[i] + '\n')
    else:
        for i in range((DURATION // episode) + 1):
            f.write(str(i + 1) + '\n')
            f.write(convert_to_time_format(i * episode) + ' --> ' + convert_to_time_format((i + 1) * episode) + '\n')
            f.write(input_text[i] + '\n')


def main():
    filename = input("Введите имя видео, на которое нужно наложить субтитры: ")
    extract_audio(filename)
    episode = 4
    if DURATION % episode == 0:
        for i in range(DURATION // episode):
            speech_recognize(i * episode)
    else:
        for i in range((DURATION // episode) + 1):
            speech_recognize(i * episode)
    translated = GoogleTranslator(source='auto', target='ru').translate_batch(outputSpeech)
    replace_subs("subtitles.srt", translated)
    replace_subs("subtitles2.srt", outputSpeech)
    try:
        (
            ffmpeg
                .input(filename)
                .filter("subtitles", "subtitles.srt")
                .output("outputPartial.mp4")
                .run()
        )
        (
            ffmpeg
            .input(filename)
            .filter("subtitles", "subtitles2.srt")
            .output("outputPartial2.mp4")
            .run()
        )
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

    os.system("ffmpeg -i outputPartial.mp4 -i test.wav -shortest -c:v copy -c:a aac -b:a 256k output.mp4")
    os.remove("outputPartial.mp4")
    os.system("ffmpeg -i outputPartial2.mp4 -i test.wav -shortest -c:v copy -c:a aac -b:a 256k output2.mp4")
    os.remove("outputPartial2.mp4")


if __name__ == "__main__":
    main()
