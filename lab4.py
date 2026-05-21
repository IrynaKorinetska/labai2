import random
import json
import os
import math
import matplotlib.pyplot as plt

# --- Етап 1: Генерація карти (як координати точок) ---

def generate_and_save_map(filename="route_map.json"):
    # Кількість міст N у діапазоні 25...35
    N = random.randint(25, 35)
    
    cities = []
    for _ in range(N):
        x = random.randint(0, 500)
        y = random.randint(0, 500)
        cities.append((x, y))
        
    with open(filename, 'w') as f:
        json.dump(cities, f)
    return cities

def load_map(filename="route_map.json"):
    with open(filename, 'r') as f:
        return [tuple(city) for city in json.load(f)]

def calculate_distance(city1, city2):
    return math.sqrt((city1[0] - city2[0])**2 + (city1[1] - city2[1])**2)

def build_distance_matrix(cities):
    N = len(cities)
    matrix = [[0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if i != j:
                matrix[i][j] = calculate_distance(cities[i], cities[j])
    return matrix

# --- Етап 2: Реалізація мурашиного алгоритму ---

def run_aco(distances, num_ants, alpha, beta, rho, iterations=30):
    N = len(distances)
    pheromones = [[0.1] * N for _ in range(N)]
    
    best_overall_distance = float('inf')
    best_overall_tour = []
    Q = 100 

    for _ in range(iterations):
        all_tours = []
        all_tour_distances = []

        for _ in range(num_ants):
            start_city = random.randint(0, N - 1)
            tour = [start_city]
            unvisited = set(range(N))
            unvisited.remove(start_city)
            
            current_city = start_city
            tour_dist = 0

            while unvisited:
                probs = []
                total_prob = 0.0
                
                for city in unvisited:
                    tau = pheromones[current_city][city] ** alpha
                    eta = (1.0 / distances[current_city][city]) ** beta
                    prob = tau * eta
                    probs.append((city, prob))
                    total_prob += prob
                
                if total_prob > 0:
                    rand_val = random.uniform(0, total_prob)
                    cumulative = 0.0
                    next_city = list(unvisited)[0]
                    for city, prob in probs:
                        cumulative += prob
                        if cumulative >= rand_val:
                            next_city = city
                            break
                else:
                    next_city = random.choice(list(unvisited))
                        
                tour.append(next_city)
                unvisited.remove(next_city)
                tour_dist += distances[current_city][next_city]
                current_city = next_city
                
            tour_dist += distances[current_city][start_city]
            all_tours.append(tour)
            all_tour_distances.append(tour_dist)
            
            if tour_dist < best_overall_distance:
                best_overall_distance = tour_dist
                best_overall_tour = tour

        for i in range(N):
            for j in range(N):
                pheromones[i][j] *= (1.0 - rho)
                
        for tour, dist in zip(all_tours, all_tour_distances):
            for i in range(N):
                from_city = tour[i]
                to_city = tour[(i + 1) % N]
                pheromones[from_city][to_city] += Q / dist
                pheromones[to_city][from_city] += Q / dist

    return best_overall_distance, best_overall_tour

# --- Функція для малювання карти ---

def draw_route(cities, best_tour, best_dist):
    plt.figure(figsize=(10, 7))
    plt.title(f"Найкращий маршрут ", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    xs = [city[0] for city in cities]
    ys = [city[1] for city in cities]
    
    # Всі міста (червоні)
    plt.scatter(xs, ys, c='red', s=50, edgecolors='black', zorder=5)
    
    # Початкове та кінцеве місто (фізично це одне місто в циклі)
    start_idx = best_tour[0]
    plt.scatter(cities[start_idx][0], cities[start_idx][1], c='green', s=180, label="START", zorder=6)
    
    # Позначимо останнє місто перед поверненням як "FINISH" для відповідності вашому зразку
    finish_idx = best_tour[-1]
    plt.scatter(cities[finish_idx][0], cities[finish_idx][1], c='purple', s=180, label="FINISH", zorder=6)

    # Номерація міст з 1
    for i, (x, y) in enumerate(cities):
        plt.text(x + 5, y + 5, str(i + 1), fontsize=9, fontweight='bold')

    # Маршрут стрілочками
    for i in range(len(best_tour)):
        from_city = cities[best_tour[i]]
        to_city = cities[best_tour[(i + 1) % len(best_tour)]]
        plt.annotate('', xy=to_city, xytext=from_city,
                     arrowprops=dict(arrowstyle='->', color='blue', lw=1, alpha=0.8),
                     zorder=4)

    plt.legend()
    plt.xlabel("X координата")
    plt.ylabel("Y координата")
    plt.savefig("route_map.png", bbox_inches='tight')
    plt.show()

# --- Етап 3: Симуляції ---

def run_experiments():
    map_file = "route_map.json"
    
    # Видалення старого файлу, якщо він має невірний формат (матриця замість координат)
    if os.path.exists(map_file):
        with open(map_file, 'r') as f:
            data = json.load(f)
            if data and isinstance(data[0], list) and len(data[0]) > 2:
                os.remove(map_file)

    if not os.path.exists(map_file):
        cities = generate_and_save_map(map_file)
        print("Карту згенеровано та збережено.")
    else:
        cities = load_map(map_file)
        print("Карту завантажено з файлу.")
        
    distances = build_distance_matrix(cities)

    print("\nЗАПУСК СИМУЛЯЦІЙ:")
    experiments = [
        {"ants": 10, "rho": 0.3, "a": 1, "b": 3},
        {"ants": 10, "rho": 0.3, "a": 1, "b": 5},
        {"ants": 10, "rho": 0.7, "a": 1, "b": 3},
        {"ants": 10, "rho": 0.7, "a": 1, "b": 5},
        {"ants": 30, "rho": 0.3, "a": 1, "b": 3},
        {"ants": 30, "rho": 0.3, "a": 1, "b": 5},
        {"ants": 30, "rho": 0.7, "a": 1, "b": 3},
        {"ants": 30, "rho": 0.7, "a": 1, "b": 5},
        {"ants": 40, "rho": 0.5, "a": 1, "b": 4}, 
        {"ants": 20, "rho": 0.4, "a": 2, "b": 2}, 
    ]

    for exp in experiments:
        dist, _ = run_aco(distances, exp["ants"], exp["a"], exp["b"], exp["rho"])
        print(f"Ants:{exp['ants']:<2} | Rho:{exp['rho']} | a/b:{exp['a']}/{exp['b']} -> Avg Length: {dist:.2f}")

    print("\nБудуємо фінальний маршрут...")
    # Фінальний пошук для найкращого малюнка
    best_dist, best_tour = run_aco(distances, num_ants=40, alpha=1, beta=4, rho=0.3, iterations=100)
    
    # ---> ДОДАНИЙ КОД ДЛЯ ВИВОДУ МАРШРУТУ <---
    # Додаємо +1 до кожного міста, щоб індекси збігалися з малюнком (де нумерація з 1)
    route_str = " -> ".join(str(city + 1) for city in best_tour) + f" -> {best_tour[0] + 1}"
    print(f"\nНайкраща довжина маршруту: {best_dist:.2f}")
    print(f"Найкращий маршрут: {route_str}\n")
    
    draw_route(cities, best_tour, best_dist)

if __name__ == "__main__":
    run_experiments()