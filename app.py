import streamlit as st
import pandas as pd
import subprocess
import ast
import sys

st.set_page_config(
    page_title="Live Dashboard GetContact", 
    page_icon="📞", 
    layout="centered"
)

st.title("📞 GetContact Live Dashboard")
st.write("Cari informasi nomor telepon dan lihat tag yang tersimpan dari database.")
st.markdown("---")

phone_number = st.text_input("Masukkan Nomor Telepon (Gunakan kode negara, misal: +6281234...)", "")

if st.button("Cari Info", type="primary"):
    if phone_number:
        with st.spinner("Menghubungi server GetContact... (Proses ini memakan waktu beberapa detik)"):
            try:
                # Memanggil script asli via terminal di background dengan sys.executable
                result = subprocess.run(
                    [sys.executable, "src/main.py", "-j", "-p", phone_number],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    output_str = result.stdout.strip()
                    start_idx = output_str.find('{')
                    
                    if start_idx != -1:
                        dict_str = output_str[start_idx:]
                        
                        try:
                            # Konversi output terminal menjadi dictionary Python
                            hasil_asli = ast.literal_eval(dict_str)

                            nama_asli = hasil_asli.get('name') or hasil_asli.get('displayName') or "Tidak Diketahui"
                            daftar_tags = hasil_asli.get('tags', [])
                            is_spam = hasil_asli.get('is_spam', False)

                            st.success("Data berhasil ditemukan!")

                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader("👤 Profil Utama")
                                st.info(f"**Nama:** {nama_asli}")
                            
                            with col2:
                                st.subheader("🛡️ Info Tambahan")
                                if is_spam:
                                    st.error("**Status:** Terindikasi Spam 🚨")
                                else:
                                    st.success("**Status:** Aman ✅")

                            st.markdown("---")
                            st.subheader("🏷️ Daftar Tag (Nama Tersimpan)")
                            
                            if daftar_tags:
                                df_tags = pd.DataFrame(daftar_tags, columns=["Tag Name"])
                                df_tags.index = df_tags.index + 1 
                                st.dataframe(df_tags, width='stretch')
                            else:
                                st.write("Tidak ada tag yang ditemukan untuk nomor ini.")

                        except Exception as parse_err:
                            st.error("Terjadi kesalahan saat membaca format data.")
                            st.code(output_str) 
                            
                    else:
                        st.warning("Data tidak ditemukan, atau format log tidak sesuai.")
                        st.code(output_str)
                else:
                    st.error("Gagal menjalankan pencarian. Cek log di bawah ini.")
                    st.code(result.stderr)

            except Exception as e:
                st.error(f"Terjadi kesalahan sistem: {e}")
    else:
        st.warning("Silakan masukkan nomor telepon terlebih dahulu.")
