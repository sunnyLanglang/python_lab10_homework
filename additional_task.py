# -*- coding: utf-8 -*-
import json, time, requests, webbrowser
from datetime import datetime
import pyaudio, vosk, pyttsx3

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    # 选英文语音，找不到就用默认
    for v in engine.getProperty('voices'):
        if 'english' in v.id.lower() or 'zira' in v.name.lower() or 'david' in v.name.lower():
            engine.setProperty('voice', v.id); break
    engine.say(text); engine.runAndWait()

class Recognize:
    def __init__(self, model_path='vosk-model-small-en-us-0.15'):
        self.rec = vosk.KaldiRecognizer(vosk.Model(model_path), 16000)
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paInt16, channels=1,
                                   rate=16000, input=True, frames_per_buffer=8000)

    def pause(self):
        if self.stream.is_active(): self.stream.stop_stream()
        time.sleep(0.05)

    def resume(self):
        if self.stream.is_stopped(): self.stream.start_stream()
        time.sleep(0.05)

    def listen(self):
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.rec.AcceptWaveform(data) and (text := json.loads(self.rec.Result()).get('text', '')):
                yield text

    def close(self):
        try:
            if self.stream:
                if self.stream.is_active(): self.stream.stop_stream()
                self.stream.close()
            self.pa.terminate()
        except: pass

def lookup(word):
    try:
        r = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}', timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def get_info(data):
    """返回 (meaning, example) 两个值"""
    try:
        d = data[0]['meanings'][0]['definitions'][0]
        return d.get('definition'), d.get('example')
    except: return None, None

# ---------- 主程序 ----------
cur_word, cur_data = None, None
rec = Recognize()
rec.pause(); speak("Starting word assistant"); rec.resume()
time.sleep(0.3)
print("Commands: find <word>, meaning, example, save, link, exit")

try:
    for text in rec.listen():
        print("->", text)
        cmd = text.lower().strip()
        rec.pause()

        if 'exit' in cmd:
            speak("Goodbye"); break

        elif 'find' in cmd:
            parts = cmd.split('find', 1)
            if len(parts) > 1 and (word := parts[1].strip().split()[0]):
                speak(f"Searching for {word}")
                data = lookup(word)
                if data:
                    cur_word, cur_data = word, data
                    meaning, _ = get_info(data)
                    speak(f"Found. {meaning}" if meaning else "Found, no definition")
                else:
                    speak(f"Could not find {word}")
                    cur_word = cur_data = None
            else:
                speak("Say find followed by a word")

        elif 'meaning' in cmd:
            if cur_data:
                meaning, _ = get_info(cur_data)
                speak(meaning if meaning else "No definition")
            else: speak("No word yet")

        elif 'example' in cmd:
            if cur_data:
                _, example = get_info(cur_data)
                speak(f"Example: {example}" if example else "No example")
            else: speak("No word yet")

        elif 'save' in cmd:
            if cur_word and cur_data:
                meaning, example = get_info(cur_data)
                try:
                    with open('words.txt', 'a', encoding='utf-8') as f:
                        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n"
                                f"Word: {cur_word}\nMeaning: {meaning or 'N/A'}\n"
                                + (f"Example: {example}\n" if example else '')
                                + '-'*30 + '\n')
                    speak("Saved")
                except: speak("Save failed")
            else: speak("Nothing to save")

        elif 'link' in cmd:
            if cur_word:
                webbrowser.open(f"https://dictionaryapi.dev/entries/en/{cur_word}")
                speak("Opening link")
            else: speak("No word")

        else:
            speak("Unknown command. Try: find, meaning, example, save, link, or exit.")

        rec.resume()
finally:
    rec.close()
    print("Assistant stopped.")