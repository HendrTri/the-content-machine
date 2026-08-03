import streamlit as st
import os
import PyPDF2
import requests 
import re       
import base64

from crewai import Agent, Task, Crew, Process

st.set_page_config(page_title="AI Content Crew", page_icon="🚀", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0E1117; color: #FFFFFF; }
.st-emotion-cache-16idsys p { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 The Content Machine Markom UEI")
st.markdown("3 Output : SEO Article, Script Storyboard, Design Brief Carosel")

with st.sidebar:
    st.header("⚙️ Setup Kunci AI")
    api_key = st.text_input("🔑 Gemini API Key", type="password", help="Ambil kuncinya di Google AI Studio")
    st.markdown("---")
    st.markdown("**Tim AI yang bekerja hari ini:**")
    st.markdown("- 🕵️‍♂️ **Data Researcher** (Tukang bedah brosur)\n- 🥷 **SEO Ninja** (Penulis Blog Ranking 1)\n- 🎬 **Storyboard Director** (Penulis Naskah Video)\n- 🎠 **Visual Designer** (Pembuat Carousel + Visual)")

def generate_carousel_image(prompt, api_key, reference_images=None):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
    
    final_prompt = prompt
    if reference_images and len(reference_images) > 0:
        final_prompt += " (Ensure the vehicle strictly matches standard heavy equipment industrial design). "

    payload = {
        "instances": [
            {
                "prompt": final_prompt
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        response.raise_for_status() 
        res_data = response.json()
        
        if 'predictions' in res_data and len(res_data['predictions']) > 0:
            prediction = res_data['predictions'][0]
            b64_data = prediction.get('bytesBase64Encoded')
            mime = prediction.get('mimeType', 'image/jpeg')
            if b64_data:
                return b64_data, mime
                
        print(f"DEBUG: Response API tidak memiliki gambar. Raw response: {res_data}")
        return None, None
        
    except requests.exceptions.RequestException as e:
        print(f"DEBUG API ERROR: {e}")
        if response.text:
             print(f"DEBUG API RESPONSE BODY: {response.text}")
        return None, None
    except Exception as e:
        print(f"DEBUG PARSING ERROR: {e}")
        return None, None

col1, col2 = st.columns(2)
with col1:
    campaign_topic = st.text_input("🎯 Judul Campaign", placeholder="Contoh: Launching Unit Alat Berat HL665L+")
with col2:
    target_audience = st.text_input("👥 Target Audience", placeholder="Contoh: Perusahaan Tambang, Kontraktor")

st.markdown("### 📄 Data Brosur / Spesifikasi Unit")
st.info("Upload file PDF brosur untuk diekstrak otomatis oleh AI.")

uploaded_file = st.file_uploader("Upload File Brosur (Format .pdf)", type="pdf")

st.markdown("### 🖼️ Referensi Visual Unit (Opsional)")
uploaded_images = st.file_uploader("Upload Foto/Render Unit (Bisa pilih beberapa file .png/.jpg).", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

st.markdown("### 🪄 Instruksi Tambahan (Custom Instructions)")
custom_instructions = st.text_area("Berikan instruksi spesifik di luar SOP (Opsional). Contoh: 'Bikin artikelnya gaya santai', 'Fokus video ke bagian ban', dll.", height=100)

if st.button("🚀 Eksekusi CrewAI", use_container_width=True):
    
    brochure_data = ""
    if uploaded_file is not None:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            extracted = page.extract_text()
            if extracted:
                brochure_data += extracted + "\n"

    ref_images_data = []
    if uploaded_images:
        for img_file in uploaded_images:
            img_bytes = img_file.getvalue()
            encoded = base64.b64encode(img_bytes).decode('utf-8')
            ref_images_data.append({
                "mimeType": img_file.type,
                "data": encoded
            })

    # Validasi input sebelum jalan
    if not api_key:
        st.error("⚠️ Masukkan Gemini API Key dulu di sidebar, bre!")
    elif not brochure_data.strip():
        st.warning("⚠️ Jangan lupa masukin Data Brosur (Upload PDF)!")
    elif not campaign_topic:
        st.warning("⚠️ Jangan lupa isi Judul Campaign!")
    else:
        with st.status("🤖 Membangunkan AI Crew... (Bisa makan waktu 1-2 menit)", expanded=True) as status:
            os.environ["GEMINI_API_KEY"] = api_key

            try:
                status.update(label="🕵️‍♂️ Agen Data sedang mempelajari brosur lu...", state="running")

                # Format custom instruction text
                instruction_text = ""
                if custom_instructions.strip():
                    instruction_text = f"\n\n🚨 INSTRUKSI TAMBAHAN DARI USER:\n{custom_instructions}\n(Wajib ikuti instruksi tambahan ini dalam menyelesaikan tugas!)"

                # ==========================================
                # 1. SETUP AGENTS
                # ==========================================
                researcher = Agent(
                    role='Data Researcher',
                    goal='Mengekstrak spesifikasi teknis, fitur unggulan (USP), dan benefit produk dari brosur alat berat.',
                    backstory='Ahli analisis data teknis yang jago merangkum brosur alat berat jadi poin-poin jualan yang mematikan.',
                    llm='gemini/gemini-3.5-flash',
                    verbose=True,
                    allow_delegation=False
                )

                seo_ninja = Agent(
                    role='SEO Ninja',
                    goal='Menulis artikel blog SEO friendly yang siap ranking 1 di Google seputar alat berat. WAJIB diakhiri dengan Call to Action (CTA) ke UNIQCALL di 1500 163.',
                    backstory='Pakar SEO B2B. Sangat paham penempatan keyword, LSI, dan struktur H1, H2, H3 yang disukai algoritma Google.',
                    llm='gemini/gemini-3.5-flash',
                    verbose=True,
                    allow_delegation=False
                )

                scriptwriter = Agent(
                    role='Storyboard Director',
                    goal='Menulis script video vertikal 60 detik. SETIAP SCENE MAKSIMAL BERDURASI 10 DETIK. Beri CTA ke UNIQCALL di 1500 163 pada scene terakhir.',
                    backstory='Sutradara konten B2B. Ahli memecah adegan agar pacing cepat (maksimal 10 detik per scene) dan ahli menyisipkan Voice Over persuasif.',
                    llm='gemini/gemini-3.5-flash',
                    verbose=True,
                    allow_delegation=False
                )

                designer = Agent(
                    role='Visual Designer',
                    goal='Membuat konsep Carousel Social Media (3 Slide). Tuliskan [IMAGE_PROMPT: ...] untuk tiap slide. Sertakan CTA UNIQCALL 1500 163 di slide 3.',
                    backstory='Desainer grafis kreatif. Kamu tahu bahwa gambar referensi produk akan disisipkan, jadi buat prompt yang fokus pada environment dan mood.',
                    llm='gemini/gemini-3.5-flash',
                    verbose=True,
                    allow_delegation=False
                )

                status.update(label="📝 Membagikan tugas ke agen-agen...", state="running")

                # ==========================================
                # 2. SETUP TASKS (Menyisipkan instruksi tambahan)
                # ==========================================
                task1 = Task(
                    description=f"Analisis data brosur berikut:\n{brochure_data}\n\nBuat rangkuman 5 USP (Unique Selling Proposition) relevan untuk target: {target_audience}.{instruction_text}",
                    expected_output="Bullet points 5 USP utama dengan penjelasan teknis namun mudah dipahami.",
                    agent=researcher
                )

                task2 = Task(
                    description=f"Dari USP Task 1, tulis Artikel Blog SEO untuk campaign: {campaign_topic}. Harus ada H1, H2, paragraf pembuka, dan minimal 400 kata. Target pembaca: {target_audience}. WAJIB diakhiri dengan Call to Action (CTA) untuk menghubungi UNIQCALL di 1500 163.{instruction_text}",
                    expected_output="Artikel blog B2B lengkap dengan format Markdown dan penutup CTA UNIQCALL.",
                    agent=seo_ninja
                )

                task3 = Task(
                    description=f"Dari USP Task 1, buat Storyboard Script video vertikal 60 detik. Bagi jadi 3 kolom: [DURASI], [VISUAL / ADEGAN], dan [AUDIO / VO]. \n\nATURAN MUTLAK: Setiap scene/adegan MAKSIMAL berdurasi 10 detik. Pada scene TERAKHIR, WAJIB masukkan CTA untuk menghubungi UNIQCALL di 1500 163.{instruction_text}",
                    expected_output="Script video lengkap. Durasi maksimal 10 detik per scene. Ada CTA UNIQCALL di akhir.",
                    agent=scriptwriter
                )

                task4 = Task(
                    description=f"Dari USP Task 1, buat konsep Carousel Social Media (3 Slide). Slide 1-2 fokus ke USP, Slide 3 fokus ke CTA UNIQCALL di 1500 163. Sertakan persis satu prompt gambar AI per slide dengan format: [IMAGE_PROMPT: detailed description in english, 4k].{instruction_text}",
                    expected_output="Konsep 3 slide carousel lengkap dengan copy text dan format [IMAGE_PROMPT: ...].",
                    agent=designer
                )

                status.update(label="🔥 Mesin AI sedang bekerja keras merakit 3 Output (Harap sabar menunggu)...", state="running")

                # ==========================================
                # 3. KICKOFF CREWAI
                # ==========================================
                content_crew = Crew(
                    agents=[researcher, seo_ninja, scriptwriter, designer],
                    tasks=[task1, task2, task3, task4],
                    process=Process.sequential,
                    verbose=True
                )

                content_crew.kickoff()

                status.update(label="✅ Selesai! Strategi konten, script, dan visual siap.", state="complete")
                st.success("🎉 BOOM! 3 Output Utama lu udah jadi!")

                tab1, tab2, tab3 = st.tabs(["🌐 1. SEO Article", "🎬 2. Storyboard Script", "🎠 3. Carousel & Visuals"])
                
                with tab1:
                    st.markdown("### 🏆 Artikel SEO (Siap Publish)")
                    st.markdown(str(task2.output))
                
                with tab2:
                    st.markdown("### 🎬 Naskah & Storyboard Video (Maks 10s per scene)")
                    st.markdown(str(task3.output))
                
                with tab3:
                    st.markdown("### 🎠 Konsep Carousel Social Media")
                    designer_out = str(task4.output)
                    st.markdown(designer_out)
                    
                    st.markdown("---")
                    st.markdown("### 🎨 Visualisasi AI (Generated with Imagen 3)")
                    
                    prompts = re.findall(r'\[IMAGE_PROMPT:\s*(.*?)\]', designer_out, re.IGNORECASE)
                    
                    if prompts:
                        cols = st.columns(len(prompts))
                        for idx, prompt in enumerate(prompts):
                            with cols[idx]:
                                st.info(f"✨ Rendering Visual Slide {idx+1}...")
                                img_data, mime = generate_carousel_image(prompt, api_key, ref_images_data)
                                if img_data:
                                    st.image(f"data:{mime};base64,{img_data}", caption=f"Slide {idx+1} Visualization", use_container_width=True)
                                else:
                                    st.error("❌ Gagal render. (Cek Terminal hitam lu buat liat pesan error Google).")
                    else:
                        st.warning("Agen Desainer lupa ngasih prompt gambar.")

            except Exception as e:
                status.update(label="❌ Waduh, Terjadi Error", state="error")
                st.error(f"Pesan Error: {e}")