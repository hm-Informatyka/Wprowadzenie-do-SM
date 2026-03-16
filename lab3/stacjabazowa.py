import tkinter as tk
from tkinter import ttk
import random
import math
import csv
import matplotlib.pyplot as plt


# =====================================================
# Klasa reprezentująca jedno połączenie (zgłoszenie)
# =====================================================

class Call:

    def __init__(self, duration, arrival_time):

        # całkowity czas rozmowy
        self.duration = duration

        # pozostały czas obsługi w kanale
        self.remaining = duration

        # moment pojawienia się zgłoszenia w systemie
        self.arrival = arrival_time

        # moment rozpoczęcia obsługi w kanale
        self.start = None


# =====================================================
# Główna klasa symulatora stacji bazowej
# =====================================================

class Simulator:

    def __init__(self, channels, lam, mean, sigma, min_d, max_d, queue_limit, time):

        # liczba kanałów obsługi w stacji bazowej
        self.channels_count = channels

        # parametr λ (intensywność napływu zgłoszeń)
        self.lam = lam

        # średni czas rozmowy
        self.mean = mean

        # odchylenie standardowe czasu rozmowy
        self.sigma = sigma

        # minimalny czas rozmowy
        self.min = min_d

        # maksymalny czas rozmowy
        self.max = max_d

        # maksymalna długość kolejki
        self.queue_limit = queue_limit

        # całkowity czas symulacji
        self.sim_time = time

        # lista kanałów (None oznacza kanał wolny)
        self.channels = [None] * channels

        # kolejka zgłoszeń oczekujących
        self.queue = []

        # aktualny czas symulacji
        self.t = 0

        # liczba obsłużonych zgłoszeń
        self.served = 0

        # liczba odrzuconych zgłoszeń
        self.rejected = 0

        # suma czasów oczekiwania
        self.wait_total = 0

        # listy do zapisu parametrów w czasie
        self.rho = []
        self.q = []
        self.w = []
        self.time = []

    # =====================================================
    # Generowanie liczby zdarzeń wg rozkładu Poissona
    # =====================================================

    def poisson(self, lam):

        # algorytm Knutha do generowania zmiennej Poissona

        L = math.exp(-lam)
        k = 0
        p = 1

        while p > L:
            k += 1
            p *= random.random()

        return k - 1

    # =====================================================
    # Losowanie czasu rozmowy
    # =====================================================

    def duration(self):

        # losowanie czasu rozmowy z rozkładu normalnego
        d = random.gauss(self.mean, self.sigma)

        # ograniczenie wartości do przedziału [min, max]
        d = max(self.min, min(self.max, d))

        # zaokrąglenie do sekund
        return int(round(d))

    # =====================================================
    # Dodanie nowego zgłoszenia do systemu
    # =====================================================

    def add_call(self, call):

        # sprawdzamy czy istnieje wolny kanał

        for i in range(self.channels_count):

            if self.channels[i] is None:

                # jeśli kanał jest wolny – zgłoszenie trafia do kanału
                call.start = self.t
                self.channels[i] = call
                return

        # jeśli wszystkie kanały są zajęte

        if len(self.queue) < self.queue_limit:

            # zgłoszenie trafia do kolejki
            self.queue.append(call)

        else:

            # kolejka jest pełna → zgłoszenie odrzucone
            self.rejected += 1

    # =====================================================
    # Aktualizacja kanałów (zmniejszanie czasu rozmowy)
    # =====================================================

    def update_channels(self):

        for i in range(self.channels_count):

            if self.channels[i]:

                # zmniejszamy pozostały czas rozmowy
                self.channels[i].remaining -= 1

                # jeśli rozmowa się zakończyła
                if self.channels[i].remaining <= 0:

                    # kanał staje się wolny
                    self.channels[i] = None

                    # zwiększamy licznik obsłużonych połączeń
                    self.served += 1

    # =====================================================
    # Przenoszenie zgłoszeń z kolejki do wolnych kanałów
    # =====================================================

    def move_queue(self):

        for i in range(self.channels_count):

            if self.channels[i] is None and self.queue:

                # pobieramy pierwsze zgłoszenie z kolejki
                call = self.queue.pop(0)

                # obliczamy czas oczekiwania
                wait = self.t - call.arrival
                self.wait_total += wait

                # zgłoszenie trafia do kanału
                call.start = self.t
                self.channels[i] = call

    # =====================================================
    # Obliczanie parametrów systemu
    # =====================================================

    def metrics(self):

        # liczba zajętych kanałów
        busy = sum(1 for c in self.channels if c)

        # intensywność ruchu (stopień zajętości kanałów)
        rho = busy / self.channels_count

        # aktualna długość kolejki
        q = len(self.queue)

        # średni czas oczekiwania
        if self.served:
            w = self.wait_total / self.served
        else:
            w = 0

        # zapis wartości do list
        self.rho.append(rho)
        self.q.append(q)
        self.w.append(w)
        self.time.append(self.t)

    # =====================================================
    # Jeden krok symulacji (1 sekunda)
    # =====================================================

    def step(self):

        # generujemy liczbę nowych zgłoszeń
        new = self.poisson(self.lam)

        # tworzymy nowe zgłoszenia
        for _ in range(new):

            d = self.duration()

            c = Call(d, self.t)

            self.add_call(c)

        # aktualizacja kanałów
        self.update_channels()

        # przeniesienie zgłoszeń z kolejki
        self.move_queue()

        # obliczenie parametrów
        self.metrics()

        # zwiększenie czasu symulacji
        self.t += 1

    # =====================================================
    # Zapis wyników symulacji do pliku CSV
    # =====================================================

    def save(self):

        with open("wyniki.csv", "w", newline="") as f:

            writer = csv.writer(f, delimiter=';')

            writer.writerow(["t", "rho", "Q", "W"])

            for i in range(len(self.time)):

                writer.writerow([self.time[i], self.rho[i], self.q[i], self.w[i]])


# =====================================================
# Klasa odpowiedzialna za interfejs graficzny
# =====================================================

class App:

    def __init__(self, root):

        self.root = root
        root.title("Symulator stacji bazowej")

        # ustawienie rozmiaru okna
        root.geometry("800x600")

        self.sim = None

        # tworzenie elementów interfejsu
        self.create_ui()

    # =====================================================
    # Tworzenie interfejsu użytkownika
    # =====================================================

    def create_ui(self):

        frame = ttk.LabelFrame(self.root, text="Parametry")

        frame.pack(padx=10, pady=10, fill="x")

        self.entries = {}

        # lista parametrów do wprowadzenia przez użytkownika
        params = [
            ("Kanały", "5"),
            ("Lambda", "2"),
            ("Śr. czas rozmowy", "10"),
            ("Sigma", "3"),
            ("Min", "3"),
            ("Max", "20"),
            ("Kolejka", "10"),
            ("Czas symulacji", "60")
        ]

        # tworzenie pól tekstowych
        for i, (name, val) in enumerate(params):

            ttk.Label(frame, text=name).grid(row=i, column=0)

            e = ttk.Entry(frame)
            e.insert(0, val)
            e.grid(row=i, column=1)

            self.entries[name] = e

        # przycisk startu symulacji
        ttk.Button(self.root, text="Uruchom symulację",
                   command=self.start).pack(pady=5)

        # przycisk rysowania wykresów
        ttk.Button(self.root, text="Pokaż wykresy",
                   command=self.plot).pack()

        # etykieta statusu
        self.info = ttk.Label(self.root, text="Stan: gotowy")
        self.info.pack()

        # pole tekstowe pokazujące stan kanałów
        self.text = tk.Text(self.root, height=20)
        self.text.pack(fill="both", expand=True)

    # =====================================================
    # Start symulacji
    # =====================================================

    def start(self):

        # pobranie wartości z pól tekstowych

        c = int(self.entries["Kanały"].get())
        l = float(self.entries["Lambda"].get())
        m = float(self.entries["Śr. czas rozmowy"].get())
        s = float(self.entries["Sigma"].get())
        mi = int(self.entries["Min"].get())
        ma = int(self.entries["Max"].get())
        q = int(self.entries["Kolejka"].get())
        t = int(self.entries["Czas symulacji"].get())

        # utworzenie symulatora
        self.sim = Simulator(c, l, m, s, mi, ma, q, t)

        # uruchomienie pętli symulacji
        self.run()

    # =====================================================
    # Wykonywanie kolejnych kroków symulacji
    # =====================================================

    def run(self):

        if self.sim.t < self.sim.sim_time:

            self.sim.step()

            self.update()

            # opóźnienie aby symulacja była widoczna
            self.root.after(200, self.run)

        else:

            self.sim.save()

            self.info.config(text="Symulacja zakończona")

    # =====================================================
    # Aktualizacja informacji w interfejsie
    # =====================================================

    def update(self):

        s = self.sim

        self.text.delete("1.0", tk.END)

        self.text.insert(tk.END, f"Czas: {s.t}/{s.sim_time}\n")
        self.text.insert(tk.END, f"Obsłużone: {s.served}\n")
        self.text.insert(tk.END, f"Odrzucone: {s.rejected}\n")
        self.text.insert(tk.END, f"Kolejka: {len(s.queue)}\n\n")

        # wyświetlenie stanu każdego kanału
        for i, ch in enumerate(s.channels):

            if ch:
                self.text.insert(
                    tk.END,
                    f"Kanał {i+1}: zajęty (pozostało {ch.remaining}s)\n"
                )
            else:
                self.text.insert(tk.END, f"Kanał {i+1}: wolny\n")

    # =====================================================
    # Rysowanie wykresów parametrów
    # =====================================================

    def plot(self):

        if not self.sim:
            return

        plt.plot(self.sim.time, self.sim.rho)
        plt.title("ρ - intensywność ruchu")
        plt.show()

        plt.plot(self.sim.time, self.sim.q)
        plt.title("Q - długość kolejki")
        plt.show()

        plt.plot(self.sim.time, self.sim.w)
        plt.title("W - średni czas oczekiwania")
        plt.show()


# =====================================================
# Uruchomienie programu
# =====================================================

root = tk.Tk()
app = App(root)
root.mainloop()
