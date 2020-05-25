# Планы на ближайшее будущее:
# Задание констант отдельным файлом
# Поддержка .mp3 файлов, введя их форматирование в .wav
# Доделать функцию check()

# Несбыточные планы на ближайшее будущее:
# Введение "нарезки" входных файлов на отрезки заданной длины
# и "сборки" синтезированной речи из отрезков для поддержки файлов длиной более минуты

# Входные данные должны храниться в папке input/
# Выходные данные помещаются в папку output/названиеаудиофайла/
# Поддерживаются только .wav файлы длительностью не более минуты

# Пример:
# Входной файл: input/example.wav
# Выходной файл: output/example/example.wav

import os
import io
from pydub import AudioSegment
import wave
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums

# Эти 3 значения должны задаваться через конфиг
WAVE_RNN_PATH = "/home/host/WaveRNN"
WAVE_RNN_OUTPUT_DIRNAME = "quick_start"
WAVE_RNN_MAIN_FILE = "quick_start.py"

WAVE_RNN_OUTPUT_PATH = WAVE_RNN_PATH + "/" + WAVE_RNN_OUTPUT_DIRNAME


# Очистка выходного файла WaveRNN
def clearOutputDirectory():
    if (os.path.exists(WAVE_RNN_OUTPUT_PATH)) and (os.path.isdir(WAVE_RNN_OUTPUT_PATH)):
        os.system("rm -r " + WAVE_RNN_OUTPUT_PATH)
    os.system("mkdir " + WAVE_RNN_OUTPUT_PATH)


# Скрипт, запускаюший синтез переданного текста
def runWaveRNN(phrase):
    clearOutputDirectory()
    savedPath = os.getcwd()
    os.chdir(WAVE_RNN_PATH)
    command = 'python3 ' + WAVE_RNN_MAIN_FILE + ' --input_text "' + phrase + '" --batched'
    os.system(command)
    os.chdir(savedPath)


# Приведение аудиофайла к моноканальности
def transformToMono(filePath):
    sound = AudioSegment.from_wav(filePath)
    sound = sound.set_channels(1)
    sound.export(filePath, format="wav")


# Получение частоты дискретизации аудиофайла, заодно гарантирует его моноканальность (это необходимое условие)
def getFrameRate(filePath):
    with wave.open(filePath, "rb") as wavFile:
        frameRate = wavFile.getframerate()
        channels = wavFile.getnchannels()
        if channels > 1:
            transformToMono(filePath)
        return frameRate


# Скрипт, возвращающий распознанный в аудиофайле текст
def recognizeFile(filePath):
    client = speech_v1.SpeechClient()
    config = {
        "language_code": "en-US",
        "sample_rate_hertz": getFrameRate(filePath),
        "encoding": enums.RecognitionConfig.AudioEncoding.LINEAR16,
    }
    with io.open(filePath, "rb") as f:
        content = f.read()
    audio = {"content": content}
    response = client.recognize(config, audio)
    for result in response.results:
        alternative = result.alternatives[0]
        return alternative.transcript + "."


# Комплесная проверка на корректность конфигурации и введённых данных
def check(filePath):
    if (not os.path.exists(filePath)) or (not os.path.isfile(filePath)):
        print("There is no such file.")
        return False
    extension = filePath.split('.', 2)[1]
    if extension != "wav":
        print("The program supports .WAV files only.")
        return False
    return True


# Проверка на существование (или создание) папки output, также удаление уже существующей папки результата для данного файла
def checkOutputFolder(OutputFolderPath):
    if (not os.path.exists("output")) or (not os.path.isdir("output")):
        os.system("mkdir output")
    if (os.path.exists(OutputFolderPath)) and (os.path.isdir(OutputFolderPath)):
        os.system("rm -r " + OutputFolderPath)


# Перенос синтезированной речи в папку ouoput/названиеисходногоаудиофайла/названиеисходногоаудиофайла.wav
def formatResult(fileNameNoExt):
    OutputFolderPath = 'output/' + fileNameNoExt
    checkOutputFolder(OutputFolderPath)
    os.system('cp -r ' + WAVE_RNN_OUTPUT_PATH + ' ' + os.path.abspath("") + '/' + OutputFolderPath)
    if (os.path.exists(OutputFolderPath + "/tts_weights")) and (os.path.isdir(OutputFolderPath + "/tts_weights")):
        os.system('rm -r ' + OutputFolderPath + '/tts_weights')
    if (os.path.exists(OutputFolderPath + "/voc_weights")) and (os.path.isdir(OutputFolderPath + "/voc_weights")):
        os.system('rm -r ' + OutputFolderPath + '/voc_weights')
    oldResultFileName = os.listdir(OutputFolderPath)[0]
    os.system('mv ' + OutputFolderPath + '/"' + oldResultFileName + '" ' + OutputFolderPath + '/"' + fileNameNoExt + '".wav')


print("The program supports .WAV files only!")
print("Input file should be less than a minute long!")
print("Input file name can not contain spaces!")
fileName = input("Input file: ")
filePath = "input/" + fileName
fileNameNoExt = fileName.split('.', 2)[0]
if check(filePath):
    runWaveRNN(recognizeFile(filePath))
    formatResult(fileNameNoExt)
    print('The result is in "output" folder.')
