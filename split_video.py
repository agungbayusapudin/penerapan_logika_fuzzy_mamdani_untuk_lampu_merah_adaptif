import ffmpeg
import os

def split_video(input_path, output_dir, segment_duration=300, num_segments=4):
    """
    Memotong video menjadi 4 bagian dengan durasi maksimum 5 menit per bagian menggunakan FFmpeg.
    
    Parameters:
    - input_path: Path ke file video input (misalnya, 'video.mp4')
    - output_dir: Direktori untuk menyimpan video hasil potongan
    - segment_duration: Durasi setiap segmen dalam detik (default: 300 detik = 5 menit)
    - num_segments: Jumlah segmen maksimum (default: 4)
    """
    try:
        # Pastikan direktori output ada
        os.makedirs(output_dir, exist_ok=True)
        
        # Dapatkan durasi total video menggunakan FFmpeg probe
        probe = ffmpeg.probe(input_path)
        total_duration = float(probe['format']['duration'])
        print(f"Durasi total video: {total_duration:.2f} detik")
        
        # Hitung durasi per segmen
        actual_segment_duration = min(segment_duration, total_duration / num_segments)
        
        # Potong video menjadi hingga num_segments bagian
        for i in range(num_segments):
            start_time = i * actual_segment_duration
            end_time = min((i + 1) * actual_segment_duration, total_duration)
            
            # Pastikan start_time tidak melebihi durasi total
            if start_time >= total_duration:
                print(f"Segmen {i+1} dilewati karena durasi video habis.")
                break
            
            # Nama file output
            output_filename = os.path.join(output_dir, f"segment_{i+1}.mp4")
            
            # Potong video menggunakan FFmpeg
            stream = ffmpeg.input(input_path, ss=start_time, t=end_time - start_time)
            stream = ffmpeg.output(stream, output_filename, c='copy', loglevel='error')
            ffmpeg.run(stream)
            
            print(f"Segmen {i+1} disimpan: {output_filename} (durasi: {end_time - start_time:.2f} detik)")
        
        print("Pemotongan video selesai.")
        
    except FileNotFoundError:
        print(f"Error: File video '{input_path}' tidak ditemukan.")
    except ffmpeg.Error as e:
        print(f"Terjadi kesalahan FFmpeg: {e.stderr.decode()}")
    except Exception as e:
        print(f"Terjadi kesalahan: {str(e)}")

if __name__ == "__main__":
    # Konfigurasi
    input_video = "/Users/macbook/Documents/Documents/fuzzy/uploads/segment_2.mp4"  
    output_directory = "output_segments"  # Direktori untuk menyimpan hasil
    segment_duration = 300  # 5 menit dalam detik
    num_segments = 4  # Jumlah segmen maksimum
    
    # Validasi file input
    if not os.path.exists(input_video):
        print(f"Error: File '{input_video}' tidak ditemukan.")
    else:
        split_video(input_video, output_directory, segment_duration, num_segments)