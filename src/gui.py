"""
Graphical User Interface (GUI)
==============================
Functional Feature Owned By: Aishwarya A (PES2UG24AM001)

A responsive desktop UI built using standard library Tkinter (ttk):
- Tab 1: Single File Compression
- Tab 2: File Decompression
- Tab 3: Directory / Batch Archiving
- Tab 4: Live Statistics & Archive Inspector
- Integrated file pickers, status progress indicators, and safety prompts.
"""

from __future__ import annotations
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from src.compress import compress_file, EmptyFileError, CompressionError
from src.decompress import decompress_file, CorruptedFileError, DecompressionError
from src.batch import compress_batch, decompress_batch, inspect_archive
from src.report import format_report, format_bytes


class HuffmanApp(tk.Tk):
    """Main Application Window for Huffman Compression Tool."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Huffman Compression Studio")
        self.geometry("960x800")
        self.minsize(860, 740)

        # Apply a clean, modern ttk theme
        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self._configure_styles()
        self._build_ui()

    def _configure_styles(self) -> None:
        """Configure modern font and color palette."""
        bg_main = "#f3f5fa"
        accent_color = "#4f46e5"
        header_bg = "#17213b"
        self.configure(bg=bg_main)

        self.style.configure(".", background=bg_main, foreground="#24314b", font=("Segoe UI", 10))
        self.style.configure("TFrame", background="#ffffff")
        self.style.configure("TLabel", background="#ffffff")
        self.style.configure("TCheckbutton", background="#ffffff", padding=4)
        self.style.configure("TEntry", padding=9, fieldbackground="#f8f9fd", bordercolor="#d9dfec")
        self.style.configure("TButton", padding=(16, 10), background="#e9edf7", borderwidth=0)
        self.style.configure("TLabelframe", background=bg_main, borderwidth=0)
        self.style.configure("TLabelframe.Label", background=bg_main, foreground="#65708a", font=("Segoe UI", 9, "bold"))
        self.style.configure("Header.TLabel", background=header_bg, foreground="#ffffff", font=("Segoe UI", 24, "bold"), padding=(28, 24, 28, 5))
        self.style.configure("SubHeader.TLabel", background=header_bg, foreground="#bdc8e3", font=("Segoe UI", 10), padding=(28, 0, 28, 22))
        self.style.configure("Card.TFrame", background="#ffffff", relief="ridge", borderwidth=1)
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), background=accent_color, foreground="#ffffff")
        self.style.map("Accent.TButton", background=[("pressed", "#3730a3"), ("active", "#6366f1")])
        self.style.configure("TNotebook", background=bg_main, borderwidth=0, tabmargins=(0, 0, 0, 10))
        self.style.configure("TNotebook.Tab", padding=(20, 12), background=bg_main, foreground="#65708a", font=("Segoe UI", 10, "bold"), borderwidth=0)
        self.style.map("TNotebook.Tab", background=[("selected", "#ffffff")], foreground=[("selected", accent_color)])

    def _build_ui(self) -> None:
        """Construct application layout and tabs."""
        # Top banner
        header_frame = tk.Frame(self, bg="#17213b")
        header_frame.pack(fill="x")

        title_lbl = ttk.Label(header_frame, text="Huffman Compression Studio", style="Header.TLabel")
        title_lbl.pack(anchor="w")
        sub_lbl = ttk.Label(
            header_frame,
            text="UE24CS341A Software Engineering Mini-Project\nAishwarya, Chiranth, Jashruth, Nandan",
            style="SubHeader.TLabel",
        )
        sub_lbl.pack(anchor="w")

        # Main notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=24, pady=(20, 12))

        # Create tabs
        self.tab_compress = ttk.Frame(self.notebook)
        self.tab_decompress = ttk.Frame(self.notebook)
        self.tab_batch = ttk.Frame(self.notebook)
        self.tab_inspect = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_compress, text=" Compress File ")
        self.notebook.add(self.tab_decompress, text=" Decompress Archive ")
        self.notebook.add(self.tab_batch, text=" Batch / Directory ")
        self.notebook.add(self.tab_inspect, text=" Archive Info ")

        self._build_compress_tab()
        self._build_decompress_tab()
        self._build_batch_tab()
        self._build_inspect_tab()

        # Bottom Log / Status Card
        log_frame = ttk.LabelFrame(self, text="ACTIVITY & RESULTS", padding=8)
        log_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 10), wrap="word", bg="#17213b", fg="#dce5fa", relief="flat", padx=16, pady=12, highlightthickness=0)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True)

        self._log("System initialized. Ready for compression or decompression operations.")

    def _log(self, message: str) -> None:
        """Append timestamped message to the log area."""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    # ---------------- Compress Single File Tab ----------------
    def _build_compress_tab(self) -> None:
        f = ttk.Frame(self.tab_compress, padding=16)
        f.pack(fill="both", expand=True)

        lbl = ttk.Label(f, text="Select an input file of any type (text, PDF, image, binary):", font=("Segoe UI", 10, "bold"))
        lbl.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        self.comp_input_var = tk.StringVar()
        entry = ttk.Entry(f, textvariable=self.comp_input_var, width=54)
        entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 6), pady=4)

        btn_browse = ttk.Button(f, text="Browse...", command=self._browse_compress_file)
        btn_browse.grid(row=1, column=2, sticky="e")

        out_lbl = ttk.Label(f, text="Destination .huff archive path (optional):")
        out_lbl.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 2))

        self.comp_output_var = tk.StringVar()
        out_entry = ttk.Entry(f, textvariable=self.comp_output_var, width=54)
        out_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 6), pady=4)

        btn_out_browse = ttk.Button(f, text="Save As...", command=self._browse_compress_dest)
        btn_out_browse.grid(row=3, column=2, sticky="e")

        btn_run = ttk.Button(f, text="🚀 Compress File Losslessly", style="Accent.TButton", command=self._run_compress_file)
        btn_run.grid(row=4, column=0, columnspan=3, pady=(16, 0), sticky="ew")

        ttk.Label(f, text="Creates a .huff archive. Use Decompress to open the original file again.\nAlready compressed files (Excel, JPEG, ZIP) may produce a larger archive.", foreground="#65708a", wraplength=720).grid(row=5, column=0, columnspan=3, sticky="w", pady=(12, 0))

        f.columnconfigure(0, weight=1)

    def _browse_compress_file(self) -> None:
        path = filedialog.askopenfilename(title="Select File to Compress")
        if path:
            self.comp_input_var.set(path)
            if not self.comp_output_var.get():
                self.comp_output_var.set(path + ".huff")

    def _browse_compress_dest(self) -> None:
        path = filedialog.asksaveasfilename(title="Destination File", defaultextension=".huff", filetypes=[("Huffman Archive", "*.huff"), ("All Files", "*.*")])
        if path:
            self.comp_output_var.set(path)

    def _run_compress_file(self) -> None:
        inp = self.comp_input_var.get().strip()
        out = self.comp_output_var.get().strip() or None
        if not inp:
            messagebox.showwarning("Input Required", "Please select an input file to compress.")
            return

        def task():
            try:
                self._log(f"Starting compression on: {inp}")
                out_path, stats = compress_file(inp, out)
                self._log(format_report(stats))
                if stats['space_saved_bytes'] <= 0:
                    messagebox.showwarning("Archive created — no size savings", f"Saved to:\n{out_path}\n\nThe archive is {format_bytes(-stats['space_saved_bytes'])} larger than the original.\nThis file's contents did not shrink enough to offset archive metadata.\nThe original can still be restored losslessly.")
                else:
                    messagebox.showinfo("Compression complete", f"Saved to:\n{out_path}\n\nSize reduced by {stats['ratio_percent']}%\nSpace saved: {format_bytes(stats['space_saved_bytes'])}")
            except EmptyFileError as e:
                self._log(f"Error (REQ-4): {e}")
                messagebox.showerror("Empty File Error (REQ-4)", str(e))
            except Exception as e:
                self._log(f"Compression failed: {e}")
                messagebox.showerror("Error", str(e))

        threading.Thread(target=task, daemon=True).start()

    # ---------------- Decompress Archive Tab ----------------
    def _build_decompress_tab(self) -> None:
        f = ttk.Frame(self.tab_decompress, padding=16)
        f.pack(fill="both", expand=True)

        lbl = ttk.Label(f, text="Select a compressed archive (.huff or .huffz):", font=("Segoe UI", 10, "bold"))
        lbl.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        self.decomp_input_var = tk.StringVar()
        entry = ttk.Entry(f, textvariable=self.decomp_input_var, width=54)
        entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 6), pady=4)

        btn_browse = ttk.Button(f, text="Browse...", command=self._browse_decomp_file)
        btn_browse.grid(row=1, column=2, sticky="e")

        out_lbl = ttk.Label(f, text="Extract Destination Directory (optional):")
        out_lbl.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 2))

        self.decomp_output_var = tk.StringVar()
        out_entry = ttk.Entry(f, textvariable=self.decomp_output_var, width=54)
        out_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 6), pady=4)

        btn_out_browse = ttk.Button(f, text="Choose Dir...", command=self._browse_decomp_dest)
        btn_out_browse.grid(row=3, column=2, sticky="e")

        self.decomp_force_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(f, text="Allow overwriting existing files (Safety override)", variable=self.decomp_force_var)
        chk.grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))

        btn_run = ttk.Button(f, text="🔓 Restore Original File(s)", style="Accent.TButton", command=self._run_decompress_file)
        btn_run.grid(row=5, column=0, columnspan=3, pady=(16, 0), sticky="ew")

        f.columnconfigure(0, weight=1)

    def _browse_decomp_file(self) -> None:
        path = filedialog.askopenfilename(title="Select Archive", filetypes=[("Huffman Files", "*.huff;*.huffz"), ("All Files", "*.*")])
        if path:
            self.decomp_input_var.set(path)

    def _browse_decomp_dest(self) -> None:
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.decomp_output_var.set(path)

    def _run_decompress_file(self) -> None:
        inp = self.decomp_input_var.get().strip()
        out = self.decomp_output_var.get().strip() or None
        overwrite = self.decomp_force_var.get()
        if not inp:
            messagebox.showwarning("Input Required", "Please select an archive file to decompress.")
            return

        def task():
            try:
                self._log(f"Starting decompression on: {inp}")
                with open(inp, "rb") as f:
                    header = f.read(16)
                if b"HUFZ" in header:
                    dest = out if out else os.path.dirname(inp)
                    stats = decompress_batch(inp, dest, overwrite=overwrite)
                    self._log(f"Batch Archive restored to: {stats['output_directory']}\nFiles: {stats['files_extracted']}")
                    messagebox.showinfo("Success", f"Extracted {stats['files_extracted']} files to:\n{stats['output_directory']}")
                else:
                    out_path, stats = decompress_file(inp, out, overwrite=overwrite)
                    self._log(format_report(stats))
                    messagebox.showinfo("Decompression Successful", f"Restored file verified losslessly:\n{out_path}")
            except CorruptedFileError as e:
                self._log(f"Integrity Error (REQ-7): {e}")
                messagebox.showerror("Corruption Detected (REQ-7)", str(e))
            except Exception as e:
                self._log(f"Decompression error: {e}")
                messagebox.showerror("Error", str(e))

        threading.Thread(target=task, daemon=True).start()

    # ---------------- Batch Directory Archiving Tab ----------------
    def _build_batch_tab(self) -> None:
        f = ttk.Frame(self.tab_batch, padding=16)
        f.pack(fill="both", expand=True)

        lbl = ttk.Label(f, text="Select a folder to archive. Its subfolder structure will be preserved:", font=("Segoe UI", 10, "bold"))
        lbl.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        self.batch_dir_var = tk.StringVar()
        entry = ttk.Entry(f, textvariable=self.batch_dir_var, width=54)
        entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 6), pady=4)

        btn_browse = ttk.Button(f, text="Choose Folder...", command=self._browse_batch_folder)
        btn_browse.grid(row=1, column=2, sticky="e")

        out_lbl = ttk.Label(f, text="Destination .huffz archive path:")
        out_lbl.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 2))

        self.batch_out_var = tk.StringVar()
        out_entry = ttk.Entry(f, textvariable=self.batch_out_var, width=54)
        out_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 6), pady=4)

        btn_out = ttk.Button(f, text="Save As...", command=self._browse_batch_dest)
        btn_out.grid(row=3, column=2, sticky="e")

        btn_run = ttk.Button(f, text="📦 Create Batch Archive (.huffz)", style="Accent.TButton", command=self._run_batch_compress)
        btn_run.grid(row=4, column=0, columnspan=3, pady=(16, 0), sticky="ew")

        f.columnconfigure(0, weight=1)

    def _browse_batch_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Folder to Compress")
        if folder:
            self.batch_dir_var.set(folder)
            if not self.batch_out_var.get():
                self.batch_out_var.set(folder.rstrip("/\\") + ".huffz")

    def _browse_batch_dest(self) -> None:
        path = filedialog.asksaveasfilename(title="Save Batch Archive", defaultextension=".huffz", filetypes=[("Huffman Batch Archive", "*.huffz")])
        if path:
            self.batch_out_var.set(path)

    def _run_batch_compress(self) -> None:
        folder = self.batch_dir_var.get().strip()
        dest = self.batch_out_var.get().strip()
        if not folder or not dest:
            messagebox.showwarning("Input Required", "Please specify both source folder and destination archive.")
            return

        def task():
            try:
                self._log(f"Archiving directory: {folder} -> {dest}")
                stats = compress_batch([folder], dest)
                self._log(f"Batch Archive Created: {stats['file_count']} files, {stats['ratio_percent']}% compression ratio.")
                messagebox.showinfo("Batch Complete", f"Created archive:\n{dest}\n\nFiles: {stats['file_count']}\nRatio: {stats['ratio_percent']}%")
            except Exception as e:
                self._log(f"Batch archive failed: {e}")
                messagebox.showerror("Error", str(e))

        threading.Thread(target=task, daemon=True).start()

    # ---------------- Inspect Archive Tab ----------------
    def _build_inspect_tab(self) -> None:
        f = ttk.Frame(self.tab_inspect, padding=16)
        f.pack(fill="both", expand=True)

        lbl = ttk.Label(f, text="Inspect .huffz archive metadata and file manifest without extraction:", font=("Segoe UI", 10, "bold"))
        lbl.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        self.inspect_file_var = tk.StringVar()
        entry = ttk.Entry(f, textvariable=self.inspect_file_var, width=54)
        entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 6), pady=4)

        btn_browse = ttk.Button(f, text="Browse...", command=self._browse_inspect_file)
        btn_browse.grid(row=1, column=2, sticky="e")

        btn_run = ttk.Button(f, text="🔍 Inspect Archive Manifest", command=self._run_inspect)
        btn_run.grid(row=2, column=0, columnspan=3, pady=(10, 0), sticky="ew")

        f.columnconfigure(0, weight=1)

    def _browse_inspect_file(self) -> None:
        path = filedialog.askopenfilename(title="Select Archive to Inspect", filetypes=[("Huffman Archives", "*.huffz;*.huff")])
        if path:
            self.inspect_file_var.set(path)

    def _run_inspect(self) -> None:
        path = self.inspect_file_var.get().strip()
        if not path:
            messagebox.showwarning("Input Required", "Please select an archive to inspect.")
            return

        try:
            info = inspect_archive(path)
            self._log(f"Inspected archive '{os.path.basename(path)}': {info['file_count']} files, {format_bytes(info['uncompressed_size'])} total.")
            for file_entry in info["files"]:
                self._log(f"  - {file_entry['path']} ({format_bytes(file_entry['size'])}, CRC 0x{file_entry['crc32']})")
        except Exception as e:
            self._log(f"Inspect failed: {e}")
            messagebox.showerror("Error", str(e))


def launch_gui() -> None:
    """Launch the Huffman Compression desktop GUI."""
    app = HuffmanApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
