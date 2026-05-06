# -*- coding: utf-8 -*-
import json, time, requests
import pyaudio, vosk
import pyttsx3

# ---------- 天气代码 → 描述（英文）----------
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    95: "Thunderstorm"
}

def get_weather():
    """Free API, no key needed. Always accessible from Russia."""
    try:
        url = ('https://api.open-meteo.com/v1/forecast'
               '?latitude=59.9343&longitude=30.3351'   # Saint Petersburg
               '&current_weather=true')
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        c = r.json()['current_weather']
        code = c['weathercode']
        desc = WEATHER_CODES.get(code, "Unknown")
        # 风向角度 → 16 方位
        dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE',
                'S','SSW','SW','WSW','W','WNW','NW','NNW']
        idx = int((c['winddirection'] + 11.25) / 22.5) % 16
        return {
            'temp': int(c['temperature']),
            'wind': int(c['windspeed']),
            'dir': dirs[idx],
            'cond': desc
        }
    except Exception as e:
        print('Open-Meteo error:', e)
        return None

# ---------- 语音合成 ----------
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    voices = engine.getProperty('voices')
    for v in voices:
        if 'english' in v.id.lower() or 'zira' in v.name.lower() or 'david' in v.name.lower():
            engine.setProperty('voice', v.id)
            break
    engine.say(text)
    engine.runAndWait()

# ---------- 语音识别 ----------
class Recognize:
    def __init__(self):
        model = vosk.Model('vosk-model-small-en-us-0.15')
        self.rec = vosk.KaldiRecognizer(model, 16000)
        self.rec.SetGrammar('["weather","wind","save","walk","exit","direction","[unk]"]')
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paInt16,
                                   channels=1,
                                   rate=16000,
                                   input=True,
                                   frames_per_buffer=8000)

    def pause(self):
        if self.stream.is_active():
            self.stream.stop_stream()
        time.sleep(0.1)

    def resume(self):
        if self.stream.is_stopped():
            self.stream.start_stream()
        time.sleep(0.1)

    def listen(self):
        while True:
            try:
                data = self.stream.read(4000, exception_on_overflow=False)
                if self.rec.AcceptWaveform(data):
                    res = json.loads(self.rec.Result())
                    text = res.get('text', '')
                    if text:
                        yield text
            except:
                break

    def close(self):
        if self.stream.is_active():
            self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

# ---------- 主程序 ----------
if __name__ == "__main__":
    rec = Recognize()
    rec.pause()
    speak("Starting")
    rec.resume()
    time.sleep(0.5)
    print("Listening... say: weather, wind, direction, save, walk, exit")

    for text in rec.listen():
        print("->", text)
        cmd = text.lower().strip()

        if 'exit' in cmd:
            rec.pause()
            speak("Goodbye")
            rec.resume()
            break

        elif 'weather' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                speak(f"Weather: {w['cond']}, {w['temp']} degrees Celsius")
            else:
                speak("Could not get weather")
            rec.resume()

        elif 'direction' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                speak(f"Wind direction is {w['dir']}")
            else:
                speak("Could not get wind direction")
            rec.resume()

        elif 'wind' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                speak(f"Wind: {w['dir']}, {w['wind']} km/h")
            else:
                speak("Could not get wind data")
            rec.resume()

        elif 'save' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                with open('weather_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{w['temp']}C, {w['wind']}km/h {w['dir']}, {w['cond']}\n")
                speak("Saved")
            else:
                speak("Failed to save")
            rec.resume()

        elif 'walk' in cmd:
            rec.pause()
            w = get_weather()
            if w:
                t, s = w['temp'], w['wind']
                if t < 5 or s > 15:
                    speak(f"Walk not recommended. Temp {t} degrees, wind {s} km/h")
                else:
                    speak(f"Walk is fine. Temp {t} degrees, wind {s} km/h")
            else:
                speak("Unable to check walking conditions")
            rec.resume()

        else:
            rec.pause()
            speak("Command not recognized")
            rec.resume()

    rec.close()
    print("Assistant stopped.")