from deep_translator import GoogleTranslator
import time

text = "穿紅衣服的人"
print(f"Original: {text}")

try:
    # Test 1: Auto source
    print("Testing auto source...")
    res = GoogleTranslator(source='auto', target='en').translate(text)
    print(f"Auto result: {res}")
    
    # Test 2: Explicit source
    print("Testing zh-TW source...")
    res2 = GoogleTranslator(source='zh-TW', target='en').translate(text)
    print(f"Explicit result: {res2}")

    # Test 3: Microsoft Translator (if available, mostly needs key, let's stick to Google)
    
except Exception as e:
    print(f"Error: {e}")
