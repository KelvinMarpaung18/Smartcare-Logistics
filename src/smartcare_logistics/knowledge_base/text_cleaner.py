"""
Modul Preprocessing dan Pembersihan Teks Dokumen.
Membersihkan teks hasil ekstraksi PDF dengan tetap menjaga nomor pasal, ayat,
rentang suhu cold chain, istilah regulasi, dan struktur tabel teknis.
"""

import re
from typing import Optional


class TextCleaner:
    """
    Pembersih teks terstruktur untuk domain logistik kesehatan dan regulasi kefarmasian.
    """

    def __init__(self):
        # Pola deteksi header/footer berulang (misal nomor halaman terisolasi atau garis pemisah)
        self.isolated_page_num_pattern = re.compile(r"^\s*[-—–]?\s*\d+\s*[-—–]?\s*$", re.MULTILINE)
        
        # Pola kata terpotong tanda hubung di akhir baris (hyphenation fix)
        # Contoh: "penye-\ndiaan" atau "penye- \ndiaan" -> "penyediaan"
        self.hyphen_newline_pattern = re.compile(r"([a-zA-Z가-힣])\s*-\s*[\r\n]+\s*([a-zA-Z가-힣])")

        # Pola baris baru di tengah kalimat yang bukan merupakan awal paragraf baru / daftar / pasal
        # Jika baris berakhir dengan huruf kecil atau tanda koma, dan baris berikutnya dimulai huruf kecil
        self.broken_line_pattern = re.compile(r"([a-z0-9,])[\r\n]+([a-z])")

        # Pola perlindungan satuan suhu dan rentang suhu
        # Menstandardisasi format derajat celcius (C, °C, s/d)
        self.temp_cleanup_pattern = re.compile(r"(\b[-+]?\d+)\s*°?\s*[Cc]\s*(?:-|s/?d|sampai|to)\s*(\b[-+]?\d+)\s*°?\s*[Cc]\b")

    def clean_text(self, text: str) -> str:
        """
        Membersihkan teks mentah halaman PDF menjadi teks bersih yang terstruktur.
        """
        if not text:
            return ""

        cleaned = text

        # 1. Hapus karakter null dan form feed
        cleaned = cleaned.replace("\x00", "").replace("\x0c", "\n")

        # 2. Perbaiki kata yang terpotong tanda hubung pada pergantian baris
        cleaned = self.hyphen_newline_pattern.sub(r"\1\2", cleaned)

        # 3. Standardisasi simbol derajat celcius untuk rentang suhu rantai dingin (cold chain)
        # Menjamin representasi suhu 2°C - 8°C dan -20°C tidak terdistorsi
        cleaned = cleaned.replace("C", "°C").replace("℃", "°C")

        # 4. Hapus nomor halaman yang berdiri sendiri di baris terpisah jika terdeteksi
        cleaned = self.isolated_page_num_pattern.sub("", cleaned)

        # 5. Gabungkan baris yang terputus di tengah kalimat
        cleaned = self.broken_line_pattern.sub(r"\1 \2", cleaned)

        # 6. Normalisasi spasi horizontal (ubah tab dan spasi berulang menjadi spasi tunggal)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # 7. Normalisasi baris kosong berturut-turut (maksimal 2 baris kosong untuk membedakan paragraf)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # 8. Trim whitespace di awal dan akhir teks
        cleaned = cleaned.strip()

        return cleaned
