import streamlit as st
import pandas as pd

# TODO: Import fungsi dari repo mnf94/getcontact milikmu di sini
# Contoh: from getcontact_api import get_phone_info

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Live Dashboard GetContact", 
    page_icon="📞", 
    layout="centered"
)

st.title("📞 GetContact Live Dashboard")
st.write("Cari informasi nomor telepon dan lihat tag yang tersimpan.")

st.markdown("---")

# Input nomor telepon dari pengguna
phone_number = st.text_input("Masukkan Nomor Telepon (Gunakan kode negara, misal: +6281234...)", "")

# Tombol untuk memicu pencarian
if st.button("Cari Info", type="primary"):
    if phone_number:
        with st.spinner("Menghubungi server GetContact..."):
            try:
                # ==========================================
                # GANTI BAGIAN INI DENGAN FUNGSI ASLI KAMU
                # ==========================================
                # raw_data = get_phone_info(phone_number)
                
                # Ini adalah data simulasi (Dummy Data)
                mock_data = {
                    "name": "Budi Santoso",
                    "trust_score": 85,
                    "tags": [
                        "Budi Kantor", 
                        "Budi IT", 
                        "Pak Budi", 
                        "Penipu Paket (Jangan Angkat)"
                    ]
                }
                # ==========================================

                st.success("Data berhasil ditemukan!")

                # Menampilkan Profil Utama
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("👤 Profil Utama")
                    st.info(f"**Nama:** {mock_data['name']}")
                
                with col2:
                    st.subheader("🛡️ Keamanan")
                    # Mengubah warna berdasarkan skor
                    score = mock_data['trust_score']
                    if score > 70:
                        st.success(f"**Trust Score:** {score}/100")
                    else:
                        st.error(f"**Trust Score:** {score}/100")

                st.markdown("---")

                # Menampilkan Daftar Tag dalam bentuk Tabel
                st.subheader("🏷️ Daftar Tag (Nama Tersimpan)")
                if mock_data['tags']:
                    # Konversi list ke DataFrame agar rapi
                    df_tags = pd.DataFrame(mock_data['tags'], columns=["Tag Name"])
                    
                    # Menambahkan nomor urut (index + 1)
                    df_tags.index = df_tags.index + 1 
                    
                    st.dataframe(df_tags, use_container_width=True)
                else:
                    st.write("Tidak ada tag yang ditemukan untuk nomor ini.")

            except Exception as e:
                st.error(f"Terjadi kesalahan saat mengambil data: {e}")
    else:
        st.warning("Silakan masukkan nomor telepon terlebih dahulu.")
