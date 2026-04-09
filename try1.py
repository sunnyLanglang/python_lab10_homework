# -*- coding: utf-8 -*-
import json, time, requests
import pyaudio, vosk
import win32com.client

# ========== 语音合成（win32com，选择俄语语音）==========
def speak(text):
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    for voice in speaker.GetVoices():
        if "Irina" in voice.GetDescription() or "Russian" in voice.GetDescription():
            speaker.Voice = voice
            break
    speaker.Speak(text)

# ========== 语音识别（增加语法限制）==========
class Recognize:
    def __init__(self):
        model = vosk.Model('vosk-model-small-ru-0.22')
        self.rec = vosk.KaldiRecognizer(model, 16000)
        # 添加语法限制：只识别这些俄语命令
        grammar = '["погода","ветер","записать","прогулка","закрыть","[unk]"]'
        try:
            self.rec.SetGrammar(grammar)
            print("语法限制已启用")
        except Exception as e:
            print(f"语法限制失败（模型可能不支持）: {e}")
        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000,
                              input=True, frames_per_buffer=8000)

    def pause(self):
        if self.stream and not self.stream.is_stopped():
            self.stream.stop_stream()
            time.sleep(0.05)

    def resume(self):
        if self.stream and self.stream.is_stopped():
            self.stream.start_stream()
            time.sleep(0.05)

    def listen(self):
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.rec.AcceptWaveform(data):
                res = json.loads(self.rec.Result())
                text = res.get('text', '')
                if text:
                    yield text

# ========== 天气功能 ==========
def get_weather(city="Saint-Petersburg"):
    url = f"https://wttr.in/{city}?format=j1"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        c = r.json()['current_condition'][0]
        return {
            'temp': int(c['temp_C']),
            'wind': int(c['windspeedKmph']),
            'dir': c['winddir16Point'],
            'cond': c['weatherDesc'][0]['value']
        }
    except:
        return None

# ========== 主程序 ==========
if __name__ == "__main__":
    rec = Recognize()
    rec.pause()
    speak("Starting")
    rec.resume()
    time.sleep(0.5)
    print("Слушаю... команды: погода, ветер, записать, прогулка, закрыть")

    for text in rec.listen():
        print("->", text)
        cmd = text.lower()

        if 'закрыть' in cmd:
            rec.pause()
            speak("До свидания")
            rec.resume()
            break
        elif 'погода' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                speak(f"Погода: {w['cond']}, {w['temp']} градуса")
            else:
                speak("Не удалось получить погоду")
            rec.resume()
        elif 'ветер' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                speak(f"Ветер: {w['dir']}, {w['wind']} километров в час")
            else:
                speak("Не удалось получить ветер")
            rec.resume()
        elif 'записать' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                with open('weather_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{w['temp']}C, {w['wind']}км/ч {w['dir']}, {w['cond']}\n")
                speak("Сохранено в файл")
            else:
                speak("Ошибка сохранения")
            rec.resume()
        elif 'прогулка' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                if w['temp'] < 5 or w['wind'] > 15:
                    speak("Прогулка не рекомендуется")
                else:
                    speak("Прогулка рекомендуется")
            else:
                speak("Не могу определить погоду")
            rec.resume()
        else:
            rec.pause()
            speak("Команда не распознана")
            rec.resume()