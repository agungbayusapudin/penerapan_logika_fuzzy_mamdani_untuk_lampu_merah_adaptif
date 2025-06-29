import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from flask import Flask, render_template, request, jsonify
import cv2
import os
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'MP4', 'AVI', 'MOV'}

# Inisialisasi sistem fuzzy
sisi_aktif = ctrl.Antecedent(np.arange(0, 151, 1), 'sisi_aktif')  # Jumlah kendaraan di sisi aktif
durasi_hijau = ctrl.Consequent(np.arange(10, 91, 1), 'durasi_hijau')

# Fungsi keanggotaan untuk jumlah kendaraan
sisi_aktif['sepi'] = fuzz.trimf(sisi_aktif.universe, [0, 0, 50])
sisi_aktif['sedang'] = fuzz.trimf(sisi_aktif.universe, [30, 75, 120])
sisi_aktif['padat'] = fuzz.trimf(sisi_aktif.universe, [100, 150, 150])

# Fungsi keanggotaan untuk durasi lampu hijau
durasi_hijau['pendek'] = fuzz.trimf(durasi_hijau.universe, [10, 10, 35])  # 10-35 detik untuk sepi
durasi_hijau['sedang'] = fuzz.trimf(durasi_hijau.universe, [25, 50, 75])  # 25-75 detik untuk sedang
durasi_hijau['lama'] = fuzz.trimf(durasi_hijau.universe, [65, 90, 90])    # 65-90 detik untuk padat

# Aturan fuzzy
rule_sepi = ctrl.Rule(sisi_aktif['sepi'], durasi_hijau['pendek'])
rule_sedang = ctrl.Rule(sisi_aktif['sedang'], durasi_hijau['sedang'])
rule_padat = ctrl.Rule(sisi_aktif['padat'], durasi_hijau['lama'])

fuzzy_system_sisi_aktif = ctrl.ControlSystem([rule_sepi, rule_sedang, rule_padat])
sim_sisi_aktif = ctrl.ControlSystemSimulation(fuzzy_system_sisi_aktif)

# Variabel global
vehicle_counts = {'sisi_a': 0, 'sisi_b': 0, 'sisi_c': 0, 'sisi_d': 0}
processing_threads = {}
current_side_index = 0  # Untuk melacak sisi saat ini dalam siklus (0: sisi_a, 1: sisi_b, 2: sisi_c, 3: sisi_d)

# Fungsi untuk deteksi kendaraan dari video
def detect_vehicles(video_path, side_key):
    global vehicle_counts
    min_contour_width = 40
    min_contour_height = 40
    offset = 10
    line_height = 550
    matches = []
    vehicles = 0

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    if not cap.isOpened():
        print(f"Error opening video file for {side_key}: {video_path}")
        return

    ret, frame1 = cap.read()
    ret, frame2 = cap.read()
    if not ret:
        print(f"Failed to read video frames for {side_key}")
        cap.release()
        return

    while ret:
        d = cv2.absdiff(frame1, frame2)
        grey = cv2.cvtColor(d, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(grey, (5, 5), 0)
        ret, th = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(th, np.ones((3, 3)))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        closing = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            (x, y, w, h) = cv2.boundingRect(c)
            contour_valid = (w >= min_contour_width) and (h >= min_contour_height)
            if not contour_valid:
                continue
            cx, cy = get_centroid(x, y, w, h)
            matches.append((cx, cy))
            for (x, y) in matches[:]:
                if (line_height - offset) < y < (line_height + offset):
                    vehicles += 1
                    matches.remove((x, y))

        vehicle_counts[side_key] = vehicles
        frame1 = frame2
        ret, frame2 = cap.read()
        time.sleep(0.033)  # Simulasi 30 FPS

    cap.release()
    print(f"Finished processing video for {side_key}, total vehicles: {vehicles}")

def get_centroid(x, y, w, h):
    x1 = int(w / 2)
    y1 = int(h / 2)
    cx = x + x1
    cy = y + y1
    return cx, cy

# Fungsi untuk menghitung durasi hijau berdasarkan jumlah kendaraan di sisi aktif
def hitung_durasi_untuk_sisi(target_sisi, all_sisi_data):
    try:
        sim_sisi_aktif.input['sisi_aktif'] = all_sisi_data[target_sisi]
        sim_sisi_aktif.compute()
        return sim_sisi_aktif.output['durasi_hijau']
    except ValueError as e:
        print(f"Error computing fuzzy output for {target_sisi}: {e}")
        return 30

def kurangi_kendaraan(sisi, jumlah_kendaraan, durasi_hijau):
    kendaraan_lewat = int(jumlah_kendaraan * 0.8)  # 80% kendaraan lewat
    kendaraan_sisa = max(0, jumlah_kendaraan - kendaraan_lewat)
    print(f"Sisi {sisi.upper()}: {jumlah_kendaraan} kendaraan -> {kendaraan_lewat} lewat, sisa {kendaraan_sisa}")
    return kendaraan_sisa

# Cek ekstensi file yang diizinkan
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    side_key = request.form.get('side')
    if side_key not in ['sisi_a', 'sisi_b', 'sisi_c', 'sisi_d']:
        print(f"Invalid side: {side_key}")
        return jsonify({'error': 'Invalid side'}), 400

    if 'video' not in request.files:
        print("No video file in request")
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']
    if file.filename == '':
        print("No selected file")
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    print(f"Received file: {filename}, MIME type: {file.mimetype}, allowed: {allowed_file(filename)}")
    if file and allowed_file(filename):
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(video_path)
        print(f"File saved to: {video_path}")

        thread = threading.Thread(target=detect_vehicles, args=(video_path, side_key))
        thread.daemon = True
        processing_threads[side_key] = thread
        thread.start()

        return jsonify({'message': f'Video for {side_key} uploaded and processing started'}), 200
    else:
        print(f"Invalid file type for {filename}")
        return jsonify({'error': 'Invalid file type'}), 400

@app.route('/get_vehicle_counts', methods=['GET'])
def get_vehicle_counts():
    return jsonify(vehicle_counts)

@app.route('/get_durations', methods=['POST'])
def get_durations():
    global vehicle_counts, current_side_index
    data = request.json or vehicle_counts
    data_kendaraan = {
        'sisi_a': int(data.get('sisi_a', vehicle_counts.get('sisi_a', 0))),
        'sisi_b': int(data.get('sisi_b', vehicle_counts.get('sisi_b', 0))),
        'sisi_c': int(data.get('sisi_c', vehicle_counts.get('sisi_c', 0))),
        'sisi_d': int(data.get('sisi_d', vehicle_counts.get('sisi_d', 0)))
    }

    # Daftar sisi dalam urutan siklus
    sides = ['sisi_a', 'sisi_b', 'sisi_c', 'sisi_d']
    current_side = sides[current_side_index]
    durasi_prioritas = round(hitung_durasi_untuk_sisi(current_side, data_kendaraan), 1)

    # Kurangi jumlah kendaraan di sisi saat ini
    data_kendaraan[current_side] = kurangi_kendaraan(current_side, data_kendaraan[current_side], durasi_prioritas)
    vehicle_counts.update(data_kendaraan)

    # Hitung durasi untuk semua sisi berdasarkan data terbaru
    all_durations = {}
    for sisi_key in sides:
        if data_kendaraan[sisi_key] > 0:
            all_durations[sisi_key] = round(hitung_durasi_untuk_sisi(sisi_key, data_kendaraan), 1)
        else:
            all_durations[sisi_key] = 0

    # Persiapkan respons
    response = {
        'durations': all_durations,
        'prioritas': current_side,
        'durasi_prioritas': durasi_prioritas,
        'updated_vehicle_counts': data_kendaraan
    }

    # Pindah ke sisi berikutnya untuk siklus berikutnya
    current_side_index = (current_side_index + 1) % 4

    return jsonify(response)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)