import random
import json
import os
import copy

# ==========================================
# ПІДГОТОВКА ДАНИХ
# ==========================================
DATA_FILE = "school_data.json"

def create_initial_data():
    data = {
        "classes": ["1-А", "1-Б"], 
        "rooms": {
            "standard": ["Каб.1", "Каб.2"], 
            "special": {"Фізкультура": "Спортзал", "Хореографія": "Зал хореографії", "Музика": "Музичний клас"}
        },
        # НОВЕ: Кожен спец. предмет має свого профільного вчителя
        "teachers": [
            "Вчитель_А (Кер. 1-А)", 
            "Вчитель_Б (Кер. 1-Б)", 
            "Вчитель фізкультури", 
            "Вчитель музики", 
            "Вчитель хореографії"
        ],
        "subjects": ["Математика", "Читання", "Письмо", "ЯДС", "Мистецтво", "Фізкультура", "Музика", "Хореографія"]
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return data

def load_data():
    if not os.path.exists(DATA_FILE):
        return create_initial_data()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data.get("rooms"), list):
        return create_initial_data()
    return data

db = load_data()

# Жорстка прив'язка класів до їхніх постійних кабінетів
CLASS_ROOM_MAP = {
    "1-А": "Каб.1",
    "1-Б": "Каб.2"
}

SPECIAL_ROOMS_NAMES = set(db["rooms"]["special"].values())
SPECIAL_SUBJECTS = set(db["rooms"]["special"].keys())

def generate_curriculum():
    curriculum = []
    lesson_id = 0
    for cls in db["classes"]:
        homeroom_teacher = "Вчитель_А (Кер. 1-А)" if cls == "1-А" else "Вчитель_Б (Кер. 1-Б)"
        
        # Основні уроки (Мистецтво тепер веде класний керівник - це звичайна практика для початкової школи)
        for _ in range(4): curriculum.append({"id": (lesson_id := lesson_id + 1), "class": cls, "subject": "Математика", "teacher": homeroom_teacher})
        for _ in range(4): curriculum.append({"id": (lesson_id := lesson_id + 1), "class": cls, "subject": "Читання", "teacher": homeroom_teacher})
        for _ in range(4): curriculum.append({"id": (lesson_id := lesson_id + 1), "class": cls, "subject": "Письмо", "teacher": homeroom_teacher})
        for _ in range(3): curriculum.append({"id": (lesson_id := lesson_id + 1), "class": cls, "subject": "ЯДС", "teacher": homeroom_teacher})
        for _ in range(2): curriculum.append({"id": (lesson_id := lesson_id + 1), "class": cls, "subject": "Мистецтво", "teacher": homeroom_teacher})
        
        # НОВЕ: Спец уроки ведуть різні спеціалізовані вчителі
        for _ in range(3): curriculum.append({"id": (lesson_id := lesson_id + 1), "class": cls, "subject": "Фізкультура", "teacher": "Вчитель фізкультури"})
        for _ in range(2): curriculum.append({"id": (lesson_id := lesson_id + 1), "class": cls, "subject": "Музика", "teacher": "Вчитель музики"})
        for _ in range(2): curriculum.append({"id": (lesson_id := lesson_id + 1), "class": cls, "subject": "Хореографія", "teacher": "Вчитель хореографії"})
        
    return curriculum

CURRICULUM = generate_curriculum()

# Щільні слоти (без вікон)
PERFECT_SLOTS = [(day, slot) for day in range(4) for slot in range(5)] + [(4, slot) for slot in range(4)]

# ==========================================
# ЕТАП 1: Структура хромосоми
# ==========================================
def create_random_chromosome():
    chromosome = []
    for cls in db["classes"]:
        class_lessons = [l for l in CURRICULUM if l["class"] == cls]
        slots = copy.deepcopy(PERFECT_SLOTS)
        random.shuffle(slots)
        
        for i, lesson in enumerate(class_lessons):
            gene = copy.deepcopy(lesson)
            gene["day"], gene["slot"] = slots[i]
            
            # Призначення кабінетів
            if gene["subject"] in SPECIAL_SUBJECTS:
                gene["room"] = db["rooms"]["special"][gene["subject"]]
            else:
                gene["room"] = CLASS_ROOM_MAP[gene["class"]]
            
            chromosome.append(gene)
    return chromosome

# ==========================================
# ЕТАП 2: Цільова функція (Fitness)
# ==========================================
def calculate_fitness(chromosome):
    penalty = 0
    teacher_schedule = {}
    
    for gene in chromosome:
        t_key = (gene["teacher"], gene["day"], gene["slot"])
        teacher_schedule[t_key] = teacher_schedule.get(t_key, 0) + 1

        # Перевірка на правильність кабінетів
        if gene["subject"] in SPECIAL_SUBJECTS:
            if gene["room"] != db["rooms"]["special"][gene["subject"]]: penalty += 500
        else:
            if gene["room"] != CLASS_ROOM_MAP[gene["class"]]: penalty += 500 

    # Штраф за накладки вчителів
    for count in teacher_schedule.values():
        if count > 1: penalty += 200 * (count - 1)

    return 1.0 / (1.0 + penalty)

# ==========================================
# ЕТАП 3: Ініціалізація популяції
# ==========================================
def init_population(pop_size):
    return [create_random_chromosome() for _ in range(pop_size)]

# ==========================================
# ЕТАП 4: Мутація
# ==========================================
def mutate(chromosome, mutation_rate=0.15):
    """Обмін часом між уроками одного класу"""
    for i in range(len(chromosome)):
        if random.random() < mutation_rate:
            cls = chromosome[i]["class"]
            same_class_indices = [j for j in range(len(chromosome)) if chromosome[j]["class"] == cls and j != i]
            if same_class_indices:
                j = random.choice(same_class_indices)
                chromosome[i]["day"], chromosome[j]["day"] = chromosome[j]["day"], chromosome[i]["day"]
                chromosome[i]["slot"], chromosome[j]["slot"] = chromosome[j]["slot"], chromosome[i]["slot"]

# ==========================================
# ЕТАП 5: Кросовер
# ==========================================
def crossover(parent1, parent2):
    """Обмін розкладом цілого класу між батьками"""
    child1 = copy.deepcopy(parent1)
    child2 = copy.deepcopy(parent2)
    swap_class = random.choice(db["classes"])
    
    for i in range(len(parent1)):
        if parent1[i]["class"] == swap_class:
            child1[i] = copy.deepcopy(parent2[i])
            child2[i] = copy.deepcopy(parent1[i])
                
    return child1, child2

# ==========================================
# ЕТАП 6: Безпосередньо генетичний алгоритм
# ==========================================
def run_genetic_algorithm(pop_size=100, generations=300, crossover_prob=0.8, mutation_prob=0.15):
    print("Ініціалізація популяції...")
    population = init_population(pop_size)
    best_chromosome = None
    best_fitness = 0

    for generation in range(generations):
        fitness_scores = [(chrom, calculate_fitness(chrom)) for chrom in population]
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        current_best_chrom, current_best_fit = fitness_scores[0]
        if current_best_fit > best_fitness:
            best_fitness = current_best_fit
            best_chromosome = copy.deepcopy(current_best_chrom)
            
        if generation % 20 == 0 or generation == generations - 1:
            penalty_display = 1.0/best_fitness - 1 if best_fitness > 0 else float('inf')
            print(f"Покоління {generation:3d} | Найкращий фітнес: {best_fitness:.5f} (Штраф: {penalty_display:.0f})")

        if best_fitness == 1.0:
            print(f"Знайдено ідеальний розклад на поколінні {generation}!")
            break

        new_population = [best_chromosome] 
        
        while len(new_population) < pop_size:
            p1 = max(random.sample(fitness_scores, 3), key=lambda x: x[1])[0]
            p2 = max(random.sample(fitness_scores, 3), key=lambda x: x[1])[0]
            
            if random.random() < crossover_prob:
                c1, c2 = crossover(p1, p2)
            else:
                c1, c2 = copy.deepcopy(p1), copy.deepcopy(p2)
                
            mutate(c1, mutation_prob)
            mutate(c2, mutation_prob)
            
            new_population.extend([c1, c2])
            
        population = new_population[:pop_size]
        
    return best_chromosome

# ==========================================
# ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ ВИВОДУ
# ==========================================
def print_schedule(schedule):
    days_name = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"]
    
    for cls in db["classes"]:
        print(f"\n{'='*75}\nРОЗКЛАД ДЛЯ КЛАСУ: {cls} (Основний кабінет: {CLASS_ROOM_MAP[cls]})\n{'='*75}")
        class_lessons = [g for g in schedule if g["class"] == cls]
        
        homeroom_teacher = "Вчитель_А (Кер. 1-А)" if cls == "1-А" else "Вчитель_Б (Кер. 1-Б)"
        total_lessons = len(class_lessons)
        homeroom_lessons = sum(1 for lesson in class_lessons if lesson["teacher"] == homeroom_teacher)
        percentage = (homeroom_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        print(f"Аналіз навантаження: Класний керівник ({homeroom_teacher})")
        print(f"Веде {homeroom_lessons} з {total_lessons} уроків на тиждень ({percentage:.1f}%)")
       

        for day in range(5):
            print(f"\n--- {days_name[day]} ---")
            day_lessons = [g for g in class_lessons if g["day"] == day]
            day_lessons.sort(key=lambda x: x["slot"])
            
            if not day_lessons:
                print("  Вихідний")
                continue
                
            for lesson in day_lessons:
                print(f" Урок {lesson['slot']+1}: {lesson['subject']:<12} | {lesson['room']:<17} | {lesson['teacher']}")

if __name__ == "__main__":
   
    print("Запуск оптимізації розкладу...")
    
    best_schedule = run_genetic_algorithm(pop_size=100, generations=300, mutation_prob=0.15)
    
    print("\nВивід найкращого знайденого розкладу:")
    print_schedule(best_schedule)
    
    with open("best_schedule.json", "w", encoding="utf-8") as f:
         json.dump(best_schedule, f, ensure_ascii=False, indent=4)
    print("\nРозклад успішно збережено у 'best_schedule.json'")