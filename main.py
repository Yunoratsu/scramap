import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import sys

from engine.scraper import GoogleMapsScraper
from engine.miner import extract_email
from engine.processor import DataCleaner


class LeadSystem(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("Scramap Pro")
        self.geometry("500x750")
        self.resizable(False, False)

        self.scraper = GoogleMapsScraper()
        self.cleaner = DataCleaner()
        self.stop_event = threading.Event()

        self._build_ui()

    def _build_ui(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=40, pady=40)

        # Dados
        self.file_cities = ctk.StringVar()
        self.file_niches = ctk.StringVar()
        self.output_dir = ctk.StringVar(value=os.getcwd())
        self.scroll_val = ctk.IntVar(value=10)

        # Inputs
        self._add_input("Cidades (.txt)", self.file_cities, False)
        self._add_input("Nichos (.txt)", self.file_niches, False)
        self._add_input("Salvar em", self.output_dir, True)

        # Slider
        slider_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        slider_frame.pack(fill="x", pady=(20, 10))
        ctk.CTkLabel(slider_frame, text="Profundidade Scroll", font=("Arial", 12)).pack(anchor="w")
        self.slider = ctk.CTkSlider(slider_frame, from_=1, to=50, number_of_steps=49,
                                    variable=self.scroll_val, command=self._update_slider)
        self.slider.pack(fill="x", pady=5)
        self.val_lbl = ctk.CTkLabel(slider_frame, text="10", font=("Arial", 14, "bold"))
        self.val_lbl.pack(anchor="e")

        stats_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)
        self.lbl_total = ctk.CTkLabel(stats_frame, text="Total: 0", font=("Arial", 12))
        self.lbl_total.pack(side="left")
        self.lbl_completos = ctk.CTkLabel(stats_frame, text="Email: 0", font=("Arial", 12), text_color="#28a745")
        self.lbl_completos.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(self.container)
        self.progress_bar.pack(fill="x", pady=(0, 20))
        self.progress_bar.set(0)

        # Botões
        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.btn_start = ctk.CTkButton(btn_frame, text="INICIAR", height=40, fg_color="#1f538d",
                                       hover_color="#14375e", command=self.run_threaded)
        self.btn_start.pack(side="left", expand=True, padx=(0, 5))

        self.btn_stop = ctk.CTkButton(btn_frame, text="PARAR", height=40, fg_color="#555",
                                      hover_color="#333", state="disabled", command=self._stop)
        self.btn_stop.pack(side="right", expand=True, padx=(5, 0))

        # Log
        self.log_box = ctk.CTkTextbox(self.container, height=120, fg_color="#1a1a1a")
        self.log_box.pack(fill="both", expand=True, pady=20)

    def _add_input(self, label, var, is_dir):
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text=label, font=("Arial", 11)).pack(anchor="w")
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x")
        ctk.CTkEntry(inner, textvariable=var, height=35, fg_color="#1a1a1a").pack(side="left", fill="x", expand=True,
                                                                                  padx=(0, 5))
        cmd = lambda: var.set(filedialog.askdirectory() if is_dir else filedialog.askopenfilename())
        ctk.CTkButton(inner, text="📁", width=40, height=35, fg_color="#333", command=cmd).pack(side="right")

    def _update_slider(self, val):
        self.val_lbl.configure(text=str(int(val)))

    def log(self, msg):
        self.after(0, lambda: (self.log_box.insert("end", f"  {msg}\n"), self.log_box.see("end")))

    def run_threaded(self):
        self.stop_event.clear()
        self.btn_start.configure(state="disabled", text="Processando...")
        self.btn_stop.configure(state="normal")
        threading.Thread(target=self.start_process, daemon=True).start()

    def _stop(self):
        self.stop_event.set()
        self.log("Parada solicitada...")
        self.btn_stop.configure(state="disabled")

        def start_process(self):
        # 1. RESET E PREPARAÇÃO DA UI
        self.after(0, lambda: self.progress_bar.set(0))
        self.after(0, lambda: self.lbl_total.configure(text="Total: 0"))
        self.after(0, lambda: self.lbl_completos.configure(text="Email: 0"))
        self.log("Iniciando processo...")

        interrupted = False  # <--- FLAG PARA SABER SE O USUÁRIO PAROU
        all_leads = []

        try:
            with open(self.file_cities.get(), 'r') as f:
                cidades = [l.strip() for l in f if l.strip()]
            with open(self.file_niches.get(), 'r') as f:
                nichos = [l.strip() for l in f if l.strip()]

            total_queries = len(cidades) * len(nichos)
            count_total = 0
            count_email = 0
            current_query = 0

            for nicho in nichos:
                for cidade in cidades:
                    if self.stop_event.is_set():
                        interrupted = True
                        break  # Sai do loop das cidades

                    current_query += 1
                    query = f"{nicho} em {cidade}"
                    self.log(f"Busca: {query}")

                    leads = self.scraper.run(query, self.scroll_val.get())

                    for item in leads:
                        if self.stop_event.is_set():
                            interrupted = True
                            break  # Sai do loop dos itens

                        count_total += 1
                        email = extract_email(item['Site'])
                        if email:
                            item['Email'] = email
                            all_leads.append(item)
                            self.save_lead_incremental(item)
                            count_email += 1

                    if interrupted: break  # Sai do loop das cidades se foi interrompido

                    # Atualização fluida da UI
                    progress = current_query / total_queries
                    self.after(0, lambda p=progress, t=count_total, e=count_email: self._update_stats(p, t, e))

                if interrupted: break  # Sai do loop dos nichos se foi interrompido

            if all_leads:
                output_path = os.path.join(self.output_dir.get(), "data.csv")
                self.cleaner.save_and_clean(all_leads, filename=output_path)
                msg = f"Processo finalizado!\nLeads salvos: {len(all_leads)}"
                self.log(msg)
                self.after(0, lambda: messagebox.showinfo("Sucesso", msg))
            else:
                self.log("Processo encerrado sem dados para salvar.")


        except Exception as e:
            self.log(f"ERRO: {e}")
            self.after(0, lambda err=e: messagebox.showerror("Erro", f"Ocorreu um erro:\n{err}"))

        finally:
            self.after(0, lambda: self.btn_start.configure(state="normal", text="INICIAR"))
            self.after(0, lambda: self.btn_stop.configure(state="disabled"))
            self.after(0, lambda: self.progress_bar.set(0))

        # Cuidar de crashes/fechamento do programa antes da conclusão da busca
        def save_lead_incremental(self, lead):
        output_path = os.path.join(self.output_dir.get(), "data.csv")
        fieldnames = ['Nome', 'Site', 'Email', 'Telefone']

        file_exists = os.path.exists(output_path)

        with open(output_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')

            if not file_exists:
                writer.writeheader()
            writer.writerow(lead)
    
    
    def _update_stats(self, progress, total, email):
        self.progress_bar.set(progress)
        self.lbl_total.configure(text=f"Total: {total}")
        self.lbl_completos.configure(text=f"Email: {email}")


if __name__ == "__main__":
    app = LeadSystem()
    app.mainloop()
