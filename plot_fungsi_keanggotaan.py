import numpy as np
import matplotlib.pyplot as plt
import skfuzzy as fuzz

# Data universum
x = np.arange(0, 151, 1)
y_durasi = np.arange(10, 91, 1)

# Fungsi keanggotaan input
sepi = fuzz.trimf(x, [0, 0, 50])
sedang = fuzz.trimf(x, [30, 75, 120])
padat = fuzz.trimf(x, [100, 150, 150])

# Fungsi keanggotaan output
pendek = fuzz.trimf(y_durasi, [10, 10, 35])
sedang_out = fuzz.trimf(y_durasi, [25, 50, 75])
lama = fuzz.trimf(y_durasi, [65, 90, 90])

# Plot input
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.plot(x, sepi, 'b', label='Sepi')
plt.plot(x, sedang, 'g', label='Sedang')
plt.plot(x, padat, 'r', label='Padat')
plt.title('Fungsi Keanggotaan Jumlah Kendaraan')
plt.xlabel('Jumlah Kendaraan')
plt.ylabel('Derajat Keanggotaan')
plt.legend()
plt.grid(True)

# Plot output
plt.subplot(1, 2, 2)
plt.plot(y_durasi, pendek, 'b', label='Pendek')
plt.plot(y_durasi, sedang_out, 'g', label='Sedang')
plt.plot(y_durasi, lama, 'r', label='Lama')
plt.title('Fungsi Keanggotaan Durasi Hijau')
plt.xlabel('Durasi (detik)')
plt.ylabel('Derajat Keanggotaan')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()