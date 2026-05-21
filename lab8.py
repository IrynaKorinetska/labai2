import telebot
import re
import cv2
import numpy as np
import io
from PIL import Image, ImageFilter
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.tree import DecisionTreeClassifier
import warnings
import gc

warnings.filterwarnings("ignore")

# ==========================================
# 1. ДЕРЕВО РІШЕНЬ (КЛАСИФІКАЦІЯ НОМЕРІВ)
# ==========================================
print("Навчання Дерева рішень...")

# Розширена база країн світу
ALL_COUNTRIES = {
    1: "США / Канада", 7: "Казахстан", 20: "Єгипет", 27: "ПАР",
    30: "Греція", 31: "Нідерланди", 32: "Бельгія", 33: "Франція", 34: "Іспанія",
    36: "Угорщина", 39: "Італія", 40: "Румунія", 41: "Швейцарія", 43: "Австрія",
    44: "Великобританія", 45: "Данія", 46: "Швеція", 47: "Норвегія", 48: "Польща", 49: "Німеччина",
    52: "Мексика", 54: "Аргентина", 55: "Бразилія", 61: "Австралія", 66: "Таїланд",
    81: "Японія", 82: "Південна Корея", 86: "Китай",
    90: "Туреччина", 91: "Індія", 972: "Ізраїль", 971: "ОАЕ",
    351: "Португалія", 358: "Фінляндія", 359: "Болгарія",
    370: "Литва", 371: "Латвія", 372: "Естонія", 373: "Молдова", 374: "Вірменія",
    381: "Сербія", 385: "Хорватія", 420: "Чехія", 421: "Словаччина", 995: "Грузія"
}

X_train = [
    [380, 67, 0], [380, 68, 0], [380, 96, 0], [380, 97, 0], [380, 98, 0], # Київстар
    [380, 50, 0], [380, 66, 0], [380, 95, 0], [380, 99, 0],               # Vodafone
    [380, 63, 0], [380, 73, 0], [380, 93, 0],                             # Lifecell
    [380, 44, 2], [380, 44, 4], [380, 44, 5], [380, 44, 8], [380, 32, 0]  # Стаціонарні/Прямі
]

# Відповіді для українських номерів
y_train = [
    "Країна: Україна, Оператор: Київстар", 
    "Країна: Україна, Оператор: Київстар", 
    "Країна: Україна, Оператор: Київстар", 
    "Країна: Україна, Оператор: Київстар", 
    "Країна: Україна, Оператор: Київстар",
    "Країна: Україна, Оператор: Vodafone", 
    "Країна: Україна, Оператор: Vodafone", 
    "Країна: Україна, Оператор: Vodafone", 
    "Країна: Україна, Оператор: Vodafone",
    "Країна: Україна, Оператор: Lifecell", 
    "Країна: Україна, Оператор: Lifecell", 
    "Країна: Україна, Оператор: Lifecell",
    "Країна: Україна, Оператор: Стаціонарна лінія (Укртелеком)", 
    "Країна: Україна, Оператор: Стаціонарна лінія (Укртелеком)", 
    "Країна: Україна, Оператор: Прямий міський номер (SIP)", 
    "Країна: Україна, Оператор: Прямий міський номер (SIP)", 
    "Країна: Україна, Оператор: Стаціонарна лінія (Укртелеком)"
]

# Динамічне додавання всіх країн до Дерева рішень
for code, country_name in ALL_COUNTRIES.items():
    X_train.append([code, 0, 0])
    y_train.append(f"Країна: {country_name}")

tree_model = DecisionTreeClassifier()
tree_model.fit(X_train, y_train)

# ==========================================
# 2. НАВЧАННЯ ВЛАСНОЇ CNN (РОЗПІЗНАВАННЯ ЦИФР)
# ==========================================
print("\nЗавантаження даних MNIST...")
mnist = tf.keras.datasets.mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()

x_train = x_train.astype(np.float16) / 255.0
x_train = x_train.reshape(-1, 28, 28, 1)
gc.collect()

print("Створення архітектури Згорткової Нейронної Мережі (CNN)...")
cnn_model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(10, activation='softmax')
])

cnn_model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Навчаємо 3 епохи, щоб бот запускався швидше, цього достатньо для високої точності
print("Починаємо навчання CNN (це займе близько хвилини)...")
cnn_model.fit(x_train, y_train, epochs=3, batch_size=32, verbose=1)
print("✅ Нейромережу успішно навчено!\n")

# ==========================================
# 3. ОБРОБКА ФОТО (OPENCV + CNN)
# ==========================================
def extract_number_from_image(image_bytes):
    """Шукає контури цифр на фото і передає кожну в CNN"""
    # Читаємо зображення через OpenCV у відтінках сірого
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    # Інвертуємо кольори (робимо фон чорним, а текст білим, як в MNIST)
    _, thresh = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    # Шукаємо окремі цифри (контури)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    digit_rects = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h > 15 and w > 5:  # Відфільтровуємо дрібний шум
            digit_rects.append((x, y, w, h))
            
    # Сортуємо контури зліва направо (щоб читати номер по порядку)
    digit_rects.sort(key=lambda b: b[0])
    
    recognized_string = ""
    
    # Обробляємо кожну знайдену цифру
    for x, y, w, h in digit_rects:
        # Вирізаємо цифру
        digit_roi = thresh[y:y+h, x:x+w]
        img_pil = Image.fromarray(digit_roi)
        
        # Підганяємо розмір під 20x20, зберігаючи пропорції (як у твоєму коді!)
        max_dim = max(w, h)
        ratio = 20.0 / max_dim
        new_size = (int(w * ratio), int(h * ratio))
        if new_size[0] == 0 or new_size[1] == 0: continue
        resized_image = img_pil.resize(new_size, Image.Resampling.LANCZOS)
        
        # Вставляємо в центр чорного квадрата 28x28 (формат MNIST)
        new_image = Image.new("L", (28, 28), "black")
        paste_x = (28 - new_size[0]) // 2
        paste_y = (28 - new_size[1]) // 2
        new_image.paste(resized_image, (paste_x, paste_y))
        
        # Легке розмиття для згладжування країв
        new_image = new_image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Передаємо у твою навчену нейромережу!
        img_array = np.array(new_image) / 255.0
        img_array = img_array.reshape(1, 28, 28, 1)
        
        prediction = cnn_model.predict(img_array, verbose=0)
        predicted_digit = np.argmax(prediction)
        recognized_string += str(predicted_digit)
        
    return recognized_string

# ==========================================
# 4. ЛОГІКА РОЗПІЗНАВАННЯ (ДЕРЕВО РІШЕНЬ)
# ==========================================
def analyze_number(text_number):
    digits = re.sub(r'\D', '', text_number)
    if not digits: return "❌ Цифр не знайдено."
    
    if len(digits) == 10 and digits.startswith('0'): digits = '38' + digits
    elif len(digits) == 9: digits = '380' + digits

    if len(digits) > 15: return f"❌ Занадто багато цифр ({len(digits)})."

    country_code = 0
    for length in [4, 3, 2, 1]:
        if len(digits) >= length:
            candidate = int(digits[:length])
            if candidate in ALL_COUNTRIES or candidate == 380:
                country_code = candidate
                break

    if country_code == 0: return "⚠️ Код країни не знайдено."

    network, prefix = 0, 0
    if country_code == 380:
        if len(digits) != 12: return f"❌ Номер має містити 12 цифр."
        network = int(digits[3:5])
        prefix = int(digits[5])

    try:
        prediction = tree_model.predict([[country_code, network, prefix]])
        return f"✅ {prediction[0]}"
    except Exception:
        return "❓ Невідомий оператор."

# ==========================================
# 5. TELEGRAM БОТ
# ==========================================
TOKEN = '8645409840:AAFSMaD6zjoGKhh8638JoPpD0IYREsPLKdk'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привіт! Надішли мені фото з рукописним номером. Моя власна CNN спробує його прочитати!")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    bot.reply_to(message, analyze_number(message.text))

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "Фото отримано. Моя CNN аналізує кожну цифру...")
    try:
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Використовуємо власну нейромережу замість Tesseract!
        recognized_text = extract_number_from_image(downloaded_file)
        
        if not recognized_text:
            bot.reply_to(message, "❌ Не вдалося знайти чіткі цифри на фото.")
            return
            
        result = analyze_number(recognized_text)
        bot.reply_to(message, f"🔢 Нейромережа розпізнала: {recognized_text}\n\n{result}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка при обробці: {e}")

if __name__ == "__main__":
    print("✅ Бот успішно запущений і чекає на повідомлення!")
    bot.polling(none_stop=True)