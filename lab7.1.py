import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import tkinter as tk
from PIL import Image, ImageDraw, ImageFilter
import gc

# --- 1. ПІДГОТОВКА ДАНИХ ТА НАВЧАННЯ ЗГОРТКОВОЇ МЕРЕЖІ (CNN) ---
print("Завантаження даних...")
mnist = tf.keras.datasets.mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Нормалізація та оптимізація пам'яті: спочатку змінюємо тип, потім ділимо
x_train = x_train.astype(np.float16) / 255.0
x_test = x_test.astype(np.float16) / 255.0

# ВАЖЛИВО: Для згорткової мережі потрібно додати вимір "каналу" (чорно-білий = 1)
x_train = x_train.reshape(-1, 28, 28, 1)
x_test = x_test.reshape(-1, 28, 28, 1)

# Примусове очищення оперативної пам'яті перед початком навчання
gc.collect()

print("Створення архітектури Згорткової Нейронної Мережі (CNN)...")
model = models.Sequential([
    # Перший згортковий шар (виділяє базові лінії та краї)
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
    layers.MaxPooling2D((2, 2)), # Зменшує розмір, залишаючи найважливіше
    
    # Другий згортковий шар (шукає складніші фігури: кути, овали)
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    
    # Третій згортковий шар
    layers.Conv2D(64, (3, 3), activation='relu'),
    
    # Перехід до класичного шару для прийняття рішення
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(10, activation='softmax')
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

print("Починаємо навчання (це займе близько 30-60 секунд)...")
# Навчаємо 5 епох. Додано batch_size=16 для зменшення одночасного навантаження на пам'ять
model.fit(x_train, y_train, epochs=5, batch_size=16, validation_data=(x_test, y_test), verbose=1)
print("\nМодель успішно навчена! Відкриваю вікно...")

# --- 2. ІНТЕРФЕЙС ТА ОБРОБКА МАЛЮНКА ---
class DrawingApp:
    def __init__(self, root, trained_model):
        self.root = root
        self.root.title("Розпізнавання цифр (Згорткова мережа)")
        self.model = trained_model
        
        self.canvas_width = 280
        self.canvas_height = 280
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height, bg='black', cursor="cross")
        self.canvas.pack(pady=10)
        
        self.image = Image.new("L", (self.canvas_width, self.canvas_height), "black")
        self.draw = ImageDraw.Draw(self.image)
        
        self.canvas.bind("<B1-Motion>", self.paint)
        
        self.result_label = tk.Label(self.root, text="Намалюйте цифру (0-9)", font=("Helvetica", 14))
        self.result_label.pack(pady=10)
        
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)
        
        btn_predict = tk.Button(btn_frame, text="Розпізнати", font=("Helvetica", 12), command=self.predict_digit, bg="green", fg="white")
        btn_predict.pack(side=tk.LEFT, padx=10)
        
        btn_clear = tk.Button(btn_frame, text="Очистити", font=("Helvetica", 12), command=self.clear_canvas, bg="red", fg="white")
        btn_clear.pack(side=tk.LEFT, padx=10)

    def paint(self, event):
        brush_size = 22 # Оптимальна товщина
        x1, y1 = (event.x - brush_size), (event.y - brush_size)
        x2, y2 = (event.x + brush_size), (event.y + brush_size)
        
        self.canvas.create_oval(x1, y1, x2, y2, fill="white", outline="white")
        self.draw.ellipse([x1, y1, x2, y2], fill="white")

    def predict_digit(self):
        bbox = self.image.getbbox()
        if bbox is None:
            self.result_label.config(text="Спочатку намалюйте цифру!")
            return

        cropped_image = self.image.crop(bbox)

        width, height = cropped_image.size
        max_dim = max(width, height)
        ratio = 20.0 / max_dim
        new_size = (int(width * ratio), int(height * ratio))
        resized_image = cropped_image.resize(new_size, Image.Resampling.LANCZOS)

        new_image = Image.new("L", (28, 28), "black")
        paste_x = (28 - new_size[0]) // 2
        paste_y = (28 - new_size[1]) // 2
        new_image.paste(resized_image, (paste_x, paste_y))

        new_image = new_image.filter(ImageFilter.GaussianBlur(radius=0.5))

        # Підготовка масиву для згорткової мережі
        img_array = np.array(new_image) / 255.0
        img_array = img_array.reshape(1, 28, 28, 1)
        
        prediction = self.model.predict(img_array, verbose=0)
        predicted_digit = np.argmax(prediction)
        confidence = np.max(prediction) * 100
        
        self.result_label.config(text=f"Це цифра: {predicted_digit} (Впевненість: {confidence:.1f}%)")

    def clear_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new("L", (self.canvas_width, self.canvas_height), "black")
        self.draw = ImageDraw.Draw(self.image)
        self.result_label.config(text="Намалюйте цифру (0-9)")

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root, model)
    root.mainloop()