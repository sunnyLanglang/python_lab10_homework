# -*- coding: utf-8 -*-
import json, time, requests, webbrowser
import pyaudio, vosk
import win32com.client

# ===== 语音合成（win32com，选英文语音）=====
def speak(text):
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    for voice in speaker.GetVoices():
        if "David" in voice.GetDescription() or "Zira" in voice.GetDescription():
            speaker.Voice = voice
            break
    speaker.Speak(text)

# ===== 语音识别（无语法限制，自由识别单词）=====
class Recognize:
    def __init__(self):
        model = vosk.Model('vosk-model-small-en-us-0.15')
        self.rec = vosk.KaldiRecognizer(model, 16000)
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
                if text := res.get('text'):
                    yield text

# ===== 单词查询 API =====
def lookup(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_meaning(data):
    try:
        return data[0]['meanings'][0]['definitions'][0]['definition']
    except:
        return None

def get_example(data):
    try:
        return data[0]['meanings'][0]['definitions'][0].get('example')
    except:
        return None

# ===== 全局变量：当前查询的单词和数据 =====
cur_word = None
cur_data = None

# ===== 主程序 =====
if __name__ == "__main__":
    rec = Recognize()
    rec.pause()
    speak("Starting word assistant")
    rec.resume()
    time.sleep(0.5)
    print("Commands: find <word>, meaning, example, save, link, exit")

    for text in rec.listen():
        print("->", text)
        low = text.lower()

        if 'exit' in low:
            rec.pause(); speak("Goodbye"); rec.resume()
            break

        elif 'find' in low:
            # 提取 find 后面的单词（如 "find apple" -> "apple"）
            parts = low.split('find', 1)
            if len(parts) > 1:
                word = parts[1].strip()
                rec.pause()
                speak(f"Searching for {word}")
                data = lookup(word)
                if data:
                    cur_word, cur_data = word, data
                    m = get_meaning(data)
                    speak(f"Found. {m}" if m else "No definition")
                else:
                    speak(f"Word {word} not found")
                rec.resume()
            else:
                rec.pause(); speak("Say find followed by a word"); rec.resume()

        elif 'meaning' in low:
            rec.pause()
            if cur_data:
                m = get_meaning(cur_data)
                speak(m if m else "No definition")
            else:
                speak("No word yet")
            rec.resume()

        elif 'example' in low:
            rec.pause()
            if cur_data:
                ex = get_example(cur_data)
                speak(ex if ex else "No example")
            else:
                speak("No word yet")
            rec.resume()

        elif 'save' in low:
            rec.pause()
            if cur_data:
                m = get_meaning(cur_data)
                ex = get_example(cur_data)
                with open('words.txt', 'a', encoding='utf-8') as f:
                    f.write(f"Word: {cur_word}\nMeaning: {m}\n")
                    if ex:
                        f.write(f"Example: {ex}\n")
                    f.write("-"*20 + "\n")
                speak("Saved")
            else:
                speak("Nothing to save")
            rec.resume()

        elif 'link' in low:
            rec.pause()
            if cur_word:
                webbrowser.open(f"https://dictionaryapi.dev/entries/en/{cur_word}")
                speak("Opening link")
            else:
                speak("No word")
            rec.resume()

        else:
            rec.pause(); speak("Unknown command"); rec.resume()