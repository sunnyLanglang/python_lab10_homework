# -*- coding: utf-8 -*-
import json, time, requests
import pyaudio, vosk
import win32com.client

# ========== 语音合成（简单函数）==========
def speak(text):
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    # 选择英文语音（David 或 Zira）
    for voice in speaker.GetVoices():
        if "David" in voice.GetDescription() or "Zira" in voice.GetDescription():
            speaker.Voice = voice
            break
    speaker.Speak(text)

# ========== 语音识别（简化版，只保留必要方法）==========
class Recognize:
    def __init__(self):
        model = vosk.Model('vosk-model-small-en-us-0.15')
        self.rec = vosk.KaldiRecognizer(model, 16000)
        self.rec.SetGrammar('["weather","wind","save","walk","exit","[unk]"]')
        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000,
                              input=True, frames_per_buffer=8000)

    def pause(self):
        """暂停麦克风流（说话前调用）"""
        if self.stream and not self.stream.is_stopped():
            self.stream.stop_stream()
            time.sleep(0.05)

    def resume(self):
        """恢复麦克风流（说话后调用）"""
        if self.stream and self.stream.is_stopped():
            self.stream.start_stream()
            time.sleep(0.05)

    def listen(self):
        """生成器：不断返回识别到的命令文本"""
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.rec.AcceptWaveform(data):
                res = json.loads(self.rec.Result())
                text = res.get('text', '')
                if text:
                    yield text

# ========== 天气功能（直接调用，无装饰器）==========
def get_weather():
    try:
        r = requests.get('https://wttr.in/Saint-Petersburg?format=j1', timeout=5)
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

# ========== 主程序（最简单直接的 if-elif）==========
if __name__ == "__main__":
    rec = Recognize()
    rec.pause()
    speak("Starting")
    rec.resume()
    time.sleep(0.5)
    print("Listening... say: weather, wind, save, walk, exit")

    for text in rec.listen():
        print("->", text)
        cmd = text.lower()

        # 退出命令
        if 'exit' in cmd:
            rec.pause()
            speak("Goodbye")
            rec.resume()
            break

        # 天气命令
        elif 'weather' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                speak(f"Weather: {w['cond']}, {w['temp']} degrees")
            else:
                speak("Failed to get weather")
            rec.resume()

        # 风速命令
        elif 'wind' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                speak(f"Wind: {w['dir']}, {w['wind']} km/h")
            else:
                speak("Failed to get wind")
            rec.resume()

        # 保存命令
        elif 'save' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                with open('weather_1.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{w['temp']}C, {w['wind']}km/h {w['dir']}, {w['cond']}\n")
                speak("Saved to file")
            else:
                speak("Failed to save")
            rec.resume()

        # 散步建议命令
        elif 'walk' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                if w['temp'] < 5 or w['wind'] > 15:
                    speak("Walk not recommended")
                else:
                    speak("Walk recommended")
            else:
                speak("Unable to determine weather")
            rec.resume()

        # 未知命令
        else:
            rec.pause()
            speak("Unknown command")
            rec.resume()