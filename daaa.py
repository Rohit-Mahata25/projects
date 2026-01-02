import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import fitz # PyMuPDF

class PDFReader:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Reader with Integrated Editor")
        self.root.geometry("1200x800")
        self.root.configure(bg="#F4F4F9")

        self.pdf_doc = None
        self.current_page = 0
        self.page_count = 0
        self.pdf_path = ""
        self.zoom_level = 1.0
        self.edit_mode = False
        
        # New widget for overlaying text editing
        self.edit_overlay = None
        self.original_page_text = ""

        # --- Layout Frames ---
        self.main_frame = tk.Frame(root, bg="#F4F4F9")
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # --- Navigation and Controls (Top bar) ---
        nav_frame = tk.Frame(self.main_frame, bg="#E0E7FF", relief=tk.GROOVE, bd=1)
        nav_frame.pack(fill='x', pady=(0, 10))
        
        button_style = {'bg': '#007BFF', 'fg': 'white', 'relief': tk.FLAT, 'font': ('Helvetica', 10, 'bold'), 'padx': 10, 'pady': 5}
        
        tk.Button(nav_frame, text="< Previous", command=self.prev_page, **button_style).pack(side='left', padx=(10, 5), pady=5)
        tk.Button(nav_frame, text="Next >", command=self.next_page, **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(nav_frame, text="Zoom In (+)", command=self.zoom_in, **button_style).pack(side='left', padx=(15, 5), pady=5)
        tk.Button(nav_frame, text="Zoom Out (-)", command=self.zoom_out, **button_style).pack(side='left', padx=5, pady=5)
        
        # Search button
        tk.Button(nav_frame, text="Search Text", command=self.search_text, 
                  bg='#FFC107', fg='#333333', relief=tk.FLAT, font=('Helvetica', 10, 'bold')).pack(side='left', padx=(15, 10), pady=5)
        
        # NEW: Edit button to toggle editing mode
        self.edit_button = tk.Button(nav_frame, text="Edit Page Text", command=self.toggle_edit_mode, 
                                     bg='#DC3545', fg='white', relief=tk.FLAT, font=('Helvetica', 10, 'bold'))
        self.edit_button.pack(side='left', padx=10, pady=5)
        
        # Page counter label
        self.page_label = tk.Label(nav_frame, text="Page: -/-", font=('Helvetica', 10, 'bold'), bg="#E0E7FF", fg="#333333")
        self.page_label.pack(side='right', padx=10, pady=5)

        # --- PDF Canvas with Scrollbars (Central area) ---
        self.canvas_container = tk.Frame(self.main_frame, bg="white", bd=1, relief=tk.SUNKEN)
        self.canvas_container.pack(fill='both', expand=True)
        
        self.v_scrollbar = tk.Scrollbar(self.canvas_container, orient=tk.VERTICAL)
        self.h_scrollbar = tk.Scrollbar(self.canvas_container, orient=tk.HORIZONTAL)

        # Canvas for PDF pages
        self.canvas = tk.Canvas(self.canvas_container, bg='white', highlightthickness=0,
                                yscrollcommand=self.v_scrollbar.set,
                                xscrollcommand=self.h_scrollbar.set)
        
        self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.config(command=self.canvas.xview)
        
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)

        # Menu
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open PDF", command=self.open_pdf)
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)

    # --- Editing Functions ---
    def toggle_edit_mode(self):
        if not self.pdf_doc:
            messagebox.showwarning("Warning", "No PDF open to edit.")
            return

        if self.edit_mode:
            # Exit Edit Mode
            self.exit_edit_mode()
        else:
            # Enter Edit Mode
            self.enter_edit_mode()

    def enter_edit_mode(self):
        self.edit_mode = True
        self.edit_button.config(text="Exit Edit Mode (Cancel)", bg='#333333')

        # 1. Fetch text
        page = self.pdf_doc.load_page(self.current_page)
        self.original_page_text = page.get_text()
        
        # 2. Hide Canvas and Show Text Widget
        self.canvas.grid_remove()
        self.v_scrollbar.grid_remove()
        self.h_scrollbar.grid_remove()
        
        # Create text area with scrollbar
        text_scroll = tk.Scrollbar(self.canvas_container)
        self.edit_overlay = tk.Text(self.canvas_container, wrap='word', 
                                    yscrollcommand=text_scroll.set, bd=1, relief=tk.SUNKEN, 
                                    font=('Consolas', 10), padx=10, pady=10)
        text_scroll.config(command=self.edit_overlay.yview)
        
        # Place text area and scrollbar using grid
        self.edit_overlay.grid(row=0, column=0, sticky='nsew')
        text_scroll.grid(row=0, column=1, sticky='ns')
        
        # Insert text
        self.edit_overlay.insert(tk.END, self.original_page_text)
        
        # 3. Add Save button below the editor
        self.save_button = tk.Button(self.main_frame, text="✅ SAVE EDITED PAGE TO NEW PDF FILE...", 
                                     command=self.save_modified_pdf, 
                                     bg="#28A745", fg="white", font=("Arial", 11, "bold"), relief=tk.FLAT)
        self.save_button.pack(fill='x', padx=10, pady=5)
        
        messagebox.showinfo("Edit Mode", "You are now editing the current page's text.\nPress 'Exit Edit Mode' to cancel, or the green button to save.")

    def exit_edit_mode(self):
        self.edit_mode = False
        self.edit_button.config(text="Edit Page Text", bg='#DC3545')
        
        # 1. Destroy editor and save button
        if self.edit_overlay:
            self.edit_overlay.destroy()
            self.edit_overlay = None
        if hasattr(self, 'save_button'):
            self.save_button.destroy()

        # 2. Show Canvas and Scrollbars
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        
        self.show_page(self.current_page, reload_text=False)


    # --- Document Handling Functions (Modified show_page) ---
    def open_pdf(self):
        file_path = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            try:
                if self.pdf_doc:
                    self.pdf_doc.close()
                
                # Exit edit mode if active
                if self.edit_mode:
                    self.exit_edit_mode()
                    
                self.pdf_doc = fitz.open(file_path)
                self.pdf_path = file_path
                self.page_count = len(self.pdf_doc)
                self.current_page = 0
                self.zoom_level = 1.0
                self.show_page(self.current_page, reload_text=False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF:\n{e}")

    def show_page(self, page_number, reload_text=True):
        if self.pdf_doc:
            if self.edit_mode:
                messagebox.showwarning("Editing Active", "Please exit Edit Mode before navigating pages.")
                return
            
            page_number = max(0, min(page_number, self.page_count - 1))
            self.current_page = page_number
            
            page = self.pdf_doc.load_page(page_number)
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self.tk_image = ImageTk.PhotoImage(img)
            
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
            self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)

            self.root.title(f"PDF Reader - {self.pdf_path.split('/')[-1] if self.pdf_path else 'No File'} (Page {self.current_page + 1}/{self.page_count})")
            self.page_label.config(text=f"Page: {self.current_page + 1}/{self.page_count}")

    def next_page(self):
        if self.pdf_doc and self.current_page + 1 < self.page_count:
            self.show_page(self.current_page + 1)

    def prev_page(self):
        if self.pdf_doc and self.current_page > 0:
            self.show_page(self.current_page - 1)

    def zoom_in(self):
        if self.edit_mode:
            messagebox.showwarning("Editing Active", "Exit Edit Mode to zoom.")
            return
        self.zoom_level += 0.2
        self.show_page(self.current_page)

    def zoom_out(self):
        if self.edit_mode:
            messagebox.showwarning("Editing Active", "Exit Edit Mode to zoom.")
            return
        if self.zoom_level > 0.4:
            self.zoom_level -= 0.2
            self.show_page(self.current_page)

    def search_text(self):
        if self.edit_mode:
            messagebox.showwarning("Editing Active", "Exit Edit Mode to search.")
            return
        if self.pdf_doc:
            query = simpledialog.askstring("Search Text", "Enter text to search:")
            if query:
                found = False
                for page_num in range(self.page_count):
                    page = self.pdf_doc.load_page(page_num)
                    if page.search_for(query):
                        self.current_page = page_num
                        self.show_page(self.current_page)
                        messagebox.showinfo("Found", f"Text found on page {page_num + 1}")
                        found = True
                        break
                if not found:
                    messagebox.showinfo("Not Found", "Text not found in PDF.")

    def save_modified_pdf(self):
        if not self.pdf_doc or not self.edit_overlay:
            messagebox.showwarning("Warning", "Not currently in editing mode.")
            return

        new_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            title="Save Modified PDF As"
        )
        if not new_path:
            return

        try:
            page = self.pdf_doc.load_page(self.current_page)
            new_text = self.edit_overlay.get('1.0', tk.END).strip()
            
            
            page.clean_contents() 
            text_rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
            
            page.insert_textbox(text_rect, new_text, 
                                 fontsize=10, 
                                 fontname="helv", 
                                 align=fitz.TEXT_ALIGN_LEFT) 

            self.pdf_doc.save(new_path, garbage=4, deflate=True)

            messagebox.showinfo("Saved", f"Modified PDF saved successfully to:\n{new_path}")
            
            
            self.exit_edit_mode()
            self.show_page(self.current_page)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFReader(root)
    root.mainloop()