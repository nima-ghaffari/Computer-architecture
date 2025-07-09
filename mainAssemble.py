# List of Functions:
# ------------------
# ArchSelectionWindow:
#   - __init__(self, master)
#   - select_architecture(self, arch)
#
# AssemblerApp:
#   - __init__(self, root, architecture)
#   - setup_riscv(self)
#   - setup_mips(self)
#   - create_widgets(self)
#   - create_menu(self)
#   - show_document(self)
#   - open_hex_file(self)
#   - disassemble_instruction(self, instruction_word)
#   - return_to_selection(self)
#   - sign_extend(self, val, bits)
#   - parse_inst(self, line)
#   - encode_inst(self, parts, labels, pc)
#   - encode_riscv(self, parts, labels, pc, _mem, instr, fmt)
#   - encode_mips(self, parts, labels, pc, _mem, instr, fmt)
#   - show_docs(self)
#   - save_hex_file(self)
#   - clear_all(self)
#   - on_exit(self)
#   - load_example(self, example_name)
#   - copy_selected(self)
#   - assemble_all(self)
#
# Global Functions:
#   - show_arch_selection()
#   - main()
# ------------------

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
from collections import namedtuple
import webbrowser

class ArchSelectionWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Select Architecture")
        self.master.geometry("400x200")

        self.selected_arch = None

        window_width = 400
        window_height = 200
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Define colors
        self.background_color = "#E0F2F7"  # Light blue/off-white
        self.button_bg_color = "#3498DB"  # Medium blue
        self.button_fg_color = "#FFFFFF"  # White
        self.label_fg_color = "#2C3E50"  # Dark blue/navy for text

        self.master.configure(bg=self.background_color)

        style = ttk.Style()
        style.theme_use('clam')  # A good theme to customize

        style.configure('TFrame', background=self.background_color)
        style.configure('TLabel', background=self.background_color, foreground=self.label_fg_color,
                        font=('Berlin Sans FB Demi', 14)) # Label for selection
        style.configure('Arch.TButton', font=('Berlin Sans FB Demi', 12), padding=10,
                        background=self.button_bg_color, foreground=self.button_fg_color,
                        relief="flat") # Flat relief for modern look
        style.map('Arch.TButton',
                  background=[('active', '#21618C')], # Darker blue on hover
                  foreground=[('active', self.button_fg_color)])


        frame = ttk.Frame(self.master, padding=20)
        frame.pack(fill="both", expand=True)

        label = ttk.Label(frame, text="Select Target Architecture")
        label.pack(pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)

        riscv_btn = ttk.Button(btn_frame, text="RISC-V", style='Arch.TButton',
                               command=lambda: self.select_architecture("RISC-V"))
        riscv_btn.pack(side="left", padx=20)

        mips_btn = ttk.Button(btn_frame, text="MIPS", style='Arch.TButton',
                               command=lambda: self.select_architecture("MIPS"))
        mips_btn.pack(side="left", padx=20)

    def select_architecture(self, arch):
        self.selected_arch = arch
        self.master.destroy()

class AssemblerApp:
    def __init__(self, root, architecture):
        self.root = root
        self.architecture = architecture
        self.root.title(f"{architecture} Mini Assembler")

        # Define colors for the main application
        self.background_color = "#E0F2F7"  # Light blue/off-white
        self.header_color = "#34495E" # Darker blue for headers/labels
        self.text_area_bg = "#FFFFFF" # White for text boxes
        self.text_area_fg = "#2C3E50" # Dark blue/navy for text
        self.button_bg_color = "#3498DB"  # Medium blue
        self.button_fg_color = "#FFFFFF"  # White

        self.root.configure(bg=self.background_color)

        if architecture == "RISC-V":
            self.setup_riscv()
        else:
            self.setup_mips()

        self.create_widgets()
        self.create_menu()

        self.assembled = []
        self.hex_map = {}

        self.documentation_url = "https://riscv.org/about/" if architecture == "RISC-V" else "https://www.mips.com/"

    def setup_riscv(self):
        Instr = namedtuple('Instr', 'fmt opcode funct3 funct7')

        self.OPCODES = {
            'add':  Instr('R', 0x33, 0b000, 0b0000000),
            'sub':  Instr('R', 0x33, 0b000, 0b0100000),
            'sll':  Instr('R', 0x33, 0b001, 0b0000000),
            'slt':  Instr('R', 0x33, 0b010, 0b0000000),
            'sltu': Instr('R', 0x33, 0b011, 0b0000000),
            'xor':  Instr('R', 0x33, 0b100, 0b0000000),
            'srl':  Instr('R', 0x33, 0b101, 0b0000000),
            'sra':  Instr('R', 0x33, 0b101, 0b0100000),
            'or':   Instr('R', 0x33, 0b110, 0b0000000),
            'and':  Instr('R', 0x33, 0b111, 0b0000000),
            'mul':  Instr('R', 0x33, 0b000, 0b0000001),
            'addi': Instr('I', 0x13, 0b000, None),
            'lw':   Instr('I', 0x03, 0b010, None),
            'jalr': Instr('I', 0x67, 0b000, None),
            'sw':   Instr('S', 0x23, 0b010, None),
            'beq':  Instr('SB',0x63, 0b000, None),
            'blt':  Instr('SB',0x63, 0b100, None),
            'jal':  Instr('UJ',0x6F, None, None),
            'j':    Instr('UJ',0x6F, None, None),
        }

        self.REGS = {f'x{i}': i for i in range(32)}
        self.REV_REGS = {v: k for k, v in self.REGS.items()}

        self.REV_OPCODES = {}
        for name, instr in self.OPCODES.items():
            if instr.fmt == 'R':
                key = (instr.opcode, instr.funct3, instr.funct7)
            elif instr.fmt == 'I':
                key = (instr.opcode, instr.funct3)
            elif instr.fmt == 'S':
                key = (instr.opcode, instr.funct3)
            elif instr.fmt == 'SB':
                key = (instr.opcode, instr.funct3)
            elif instr.fmt == 'UJ':
                key = (instr.opcode,)
            self.REV_OPCODES[key] = (name, instr.fmt)


        self.EXAMPLES = {
            "Basic Arithmetic": "addi x1, x0, 10\naddi x2, x0, 20\nadd x3, x1, x2\nsub x4, x2, x1\nsll x5, x1, x2 # x5 = x1 << x2 (10 << 20)\nsrl x6, x2, x1 # x6 = x2 >> x1 (20 >> 10)\nsra x7, x2, x1 # x7 = x2 >> x1 (arithmetic shift)\nslt x8, x1, x2 # x8 = 1 if x1 < x2 else 0\nsltu x9, x2, x1 # x9 = 1 if x2 < x1 (unsigned) else 0\nxor x10, x1, x2\nor x11, x1, x2\nand x12, x1, x2",
            "Memory Access": "addi x1, x0, 42\nsw x1, 0(x0)\nlw x2, 0(x0)",
            "Branching": "addi x1, x0, 10\naddi x2, x0, 20\nloop:\naddi x1, x1, 1\nblt x1, x2, loop",
            "Function Call": "main:\naddi x1, x0, 5\njal x10, factorial\nj end\n\nfactorial:\naddi x2, x0, 1\naddi x3, x0, 1\nfact_loop:\nblt x3, x1, fact_continue\nj end_factorial_jump\nend_factorial_jump:\nfact_continue:\nmul x2, x2, x3\naddi x3, x3, 1\nj fact_loop\n\nfact_end:\njalr x0, 0(x10)\n\nend:"
        }

    def setup_mips(self):
        Instr = namedtuple('Instr', 'fmt opcode funct')

        self.OPCODES = {
            'add':  Instr('R', 0x00, 0x20),
            'sub':  Instr('R', 0x00, 0x22),
            'and':  Instr('R', 0x00, 0x24),
            'or':   Instr('R', 0x00, 0x25),
            'slt':  Instr('R', 0x00, 0x2A),
            'sll':  Instr('R', 0x00, 0x00),
            'srl':  Instr('R', 0x00, 0x02),
            'sra':  Instr('R', 0x00, 0x03),
            'addi': Instr('I', 0x08, None),
            'lw':   Instr('I', 0x23, None),
            'sw':   Instr('I', 0x2B, None),
            'beq':  Instr('I', 0x04, None),
            'blt':  Instr('I', 0x01, None),
            'j':    Instr('J', 0x02, None),
            'jal':  Instr('J', 0x03, None),
            'jr':   Instr('R', 0x00, 0x08),
        }

        self.REGS = {
            '$zero': 0, '$at': 1, '$v0': 2, '$v1': 3,
            '$a0': 4, '$a1': 5, '$a2': 6, '$a3': 7,
            '$t0': 8, '$t1': 9, '$t2': 10, '$t3': 11,
            '$t4': 12, '$t5': 13, '$t6': 14, '$t7': 15,
            '$t8': 24, '$t9': 25, '$k0': 26, '$k1': 27,
            '$s0': 16, '$s1': 17, '$s2': 18, '$s3': 19,
            '$s4': 20, '$s5': 21, '$s6': 22, '$s7': 23,
            '$gp': 28, '$sp': 29, '$fp': 30, '$ra': 31
        }
        self.REV_REGS = {v: k for k, v in self.REGS.items()}
        self.REV_OPCODES = {}
        for name, instr in self.OPCODES.items():
            if instr.fmt == 'R':
                key = (instr.opcode, instr.funct)
            elif instr.fmt == 'I':
                key = (instr.opcode,)
            elif instr.fmt == 'J':
                key = (instr.opcode,)
            self.REV_OPCODES[key] = (name, instr.fmt)


        self.EXAMPLES = {
            "Basic Arithmetic": "addi $t0, $zero, 10\naddi $t1, $zero, 20\nadd $t2, $t0, $t1\nsub $t3, $t1, $t0\nsll $t4, $t0, 2\nsrl $t5, $t0, 1\nsra $t6, $t0, 1\nslt $t7, $t0, $t1\nand $t8, $t0, $t1\nor $t9, $t0, $t1",
            "Memory Access": "addi $t0, $zero, 42\nsw $t0, 0($zero)\nlw $t1, 0($zero)",
            "Branching": "addi $t0, $zero, 10\naddi $t1, $zero, 20\nloop:\naddi $t0, $t0, 1\nblt $t0, $t1, loop",
            "Function Call": "main:\naddi $a0, $zero, 5\njal factorial\nj end\n\nfactorial:\naddi $v0, $zero, 1\naddi $t0, $zero, 1\nfact_loop:\nblt $t0, $a0, fact_continue\nj fact_end\nfact_continue:\nmul $v0, $v0, $t0\naddi $t0, $t0, 1\nj fact_loop\n\nfact_end:\njr $ra\n\nend:"
        }

    def create_widgets(self):
        self.font_family = "Berlin Sans FB Demi"
        self.font_size = 12
        self.font = (self.font_family, self.font_size)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.background_color)
        style.configure('TLabel', background=self.background_color, foreground=self.header_color, font=self.font)
        style.configure('TButton', font=(self.font_family, 10), background=self.button_bg_color, foreground=self.button_fg_color, relief="flat")
        style.map('TButton',
                  background=[('active', '#21618C')],
                  foreground=[('active', self.button_fg_color)])

        # Style for Text widgets
        self.root.option_add('*Text*Background', self.text_area_bg)
        self.root.option_add('*Text*Foreground', self.text_area_fg)
        self.root.option_add('*Text*Font', self.font)
        self.root.option_add('*Text*Borderwidth', 1)
        self.root.option_add('*Text*Relief', 'solid')
        self.root.option_add('*Text*BorderColor', '#BDC3C7') # Light gray border

        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.pack(fill="both", expand=True)

        ttk.Label(self.frame, text="Instructions").pack(anchor="w")
        self.input_box = tk.Text(self.frame, height=8, width=70)
        self.input_box.pack(fill="x", pady=(0, 10))

        output_frame = ttk.Frame(self.frame)
        output_frame.pack(fill="both", expand=True)

        left_frame = ttk.Frame(output_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0,5))

        ttk.Label(left_frame, text="Assembled Output").pack(anchor="w")
        self.output_box = tk.Text(left_frame, height=15, width=40)
        self.output_box.pack(fill="both", expand=True)

        right_frame = ttk.Frame(output_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5,0))

        ttk.Label(right_frame, text="Register Values (Terminal)").pack(anchor="w")
        self.terminal_box = tk.Text(right_frame, height=15, width=30)
        self.terminal_box.pack(fill="both", expand=True)

        bottom_frame = ttk.Frame(self.frame)
        bottom_frame.pack(fill="x", pady=10)

        style.configure('Back.TButton', font=(self.font_family, 10),
                        background="#E74C3C", foreground=self.button_fg_color, relief="flat") # A red for 'Back'
        style.map('Back.TButton',
                  background=[('active', '#C0392B')])

        self.back_btn = ttk.Button(bottom_frame, text="← Back",
                                    style='Back.TButton', command=self.return_to_selection)
        self.back_btn.pack(side="left", padx=(0, 5))

        # Styling for OptionMenu
        style.configure('TMenubutton', font=(self.font_family, 10), background=self.button_bg_color, foreground=self.button_fg_color, relief="flat")
        style.map('TMenubutton',
                  background=[('active', '#21618C')],
                  foreground=[('active', self.button_fg_color)])

        self.selected_var = tk.StringVar(value="Select instruction")
        self.copy_menu = ttk.OptionMenu(bottom_frame, self.selected_var, "Select instruction")
        self.copy_menu.pack(side="left", padx=(0, 5))

        copy_btn = ttk.Button(bottom_frame, text="Copy Hex", command=self.copy_selected)
        copy_btn.pack(side="left", padx=(0, 5))

        self.assemble_btn = ttk.Button(bottom_frame, text="Assemble", command=self.assemble_all)
        self.assemble_btn.pack(side="right")

    def create_menu(self):
        self.menubar = tk.Menu(self.root, bg=self.button_bg_color, fg=self.button_fg_color)
        self.root.config(menu=self.menubar)

        # Style for Menu items
        menu_font = (self.font_family, 10)
        file_menu = tk.Menu(self.menubar, tearoff=0, bg=self.background_color, fg=self.header_color, font=menu_font)
        file_menu.add_command(label="Open Hex File", command=self.open_hex_file)
        file_menu.add_command(label="Documentation", command=self.show_docs)
        file_menu.add_command(label="Save Hex", command=self.save_hex_file)
        file_menu.add_command(label="Clear All", command=self.clear_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        examples_menu = tk.Menu(self.menubar, tearoff=0, bg=self.background_color, fg=self.header_color, font=menu_font)
        for example_name in self.EXAMPLES:
            examples_menu.add_command(
                label=example_name,
                command=lambda name=example_name: self.load_example(name)
            )
        self.menubar.add_cascade(label="Examples", menu=examples_menu)

        help_menu = tk.Menu(self.menubar, tearoff=0, bg=self.background_color, fg=self.header_color, font=menu_font)
        help_menu.add_command(label="Online Help", command=lambda: webbrowser.open("https://t.me/NimaGhafari007"))
        help_menu.add_command(label="Document", command=self.show_document)
        self.menubar.add_cascade(label="Help", menu=help_menu)

    def show_document(self):
        messagebox.showinfo("Document", f"Opening documentation for {self.architecture} architecture.")
        webbrowser.open(self.documentation_url)

    def open_hex_file(self):
        file_path = filedialog.askopenfilename(
              defaultextension=".hex",
            filetypes=[("Hex Files", "*.hex"), ("All Files", "*.*")],
            title="Open Hex File"
        )

        if file_path:
            self.clear_all()
            disassembled_instructions = []
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        hex_code = line.strip()
                        if hex_code:
                            try:
                                instruction_word = int(hex_code, 16)
                                disassembled_line = self.disassemble_instruction(instruction_word)
                                disassembled_instructions.append(f'0x{hex_code.upper()} => {disassembled_line}')
                                self.input_box.insert(tk.END, f"{hex_code}\n")
                            except ValueError:
                                disassembled_instructions.append(f'0x{hex_code} => INVALID HEX FORMAT')
                            except Exception as e:
                                disassembled_instructions.append(f'0x{hex_code} => DISASSEMBLY ERROR: {e}')

                self.output_box.insert(tk.END, "\n".join(disassembled_instructions))
                messagebox.showinfo("Success", "Hex file loaded and partially disassembled.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def disassemble_instruction(self, instruction_word):
        opcode = instruction_word & 0x7F

        if self.architecture == "RISC-V":
            funct3 = (instruction_word >> 12) & 0x7
            funct7 = (instruction_word >> 25) & 0x7F

            key_r = (opcode, funct3, funct7)
            if key_r in self.REV_OPCODES:
                instr_name, fmt = self.REV_OPCODES[key_r]
                rd = (instruction_word >> 7) & 0x1F
                rs1 = (instruction_word >> 15) & 0x1F
                rs2 = (instruction_word >> 20) & 0x1F
                return f"{instr_name} {self.REV_REGS.get(rd, f'x{rd}')}, {self.REV_REGS.get(rs1, f'x{rs1}')}, {self.REV_REGS.get(rs2, f'x{rs2}')}"

            key_i = (opcode, funct3)
            if key_i in self.REV_OPCODES:
                instr_name, fmt = self.REV_OPCODES[key_i]
                rd = (instruction_word >> 7) & 0x1F
                rs1 = (instruction_word >> 15) & 0x1F
                imm = (instruction_word >> 20) & 0xFFF
                imm = self.sign_extend(imm, 12)

                if instr_name == 'lw':
                    return f"{instr_name} {self.REV_REGS.get(rd, f'x{rd}')}, {imm}({self.REV_REGS.get(rs1, f'x{rs1}')})"
                elif instr_name == 'jalr':
                    return f"{instr_name} {self.REV_REGS.get(rd, f'x{rd}')}, {imm}({self.REV_REGS.get(rs1, f'x{rs1}')})"
                elif instr_name == 'addi':
                    return f"{instr_name} {self.REV_REGS.get(rd, f'x{rd}')}, {self.REV_REGS.get(rs1, f'x{rs1}')}, {imm}"

            if opcode == 0x23:
                instr_name = 'sw'
                funct3_s = (instruction_word >> 12) & 0x7
                if funct3_s == 0b010:
                    imm_11_5 = (instruction_word >> 25) & 0x7F
                    imm_4_0 = (instruction_word >> 7) & 0x1F
                    imm = (imm_11_5 << 5) | imm_4_0
                    imm = self.sign_extend(imm, 12)
                    rs1 = (instruction_word >> 15) & 0x1F
                    rs2 = (instruction_word >> 20) & 0x1F
                    return f"{instr_name} {self.REV_REGS.get(rs2, f'x{rs2}')}, {imm}({self.REV_REGS.get(rs1, f'x{rs1}')})"

            if opcode == 0x63:
                funct3_sb = (instruction_word >> 12) & 0x7
                instr_name = ""
                if funct3_sb == 0b000: instr_name = 'beq'
                elif funct3_sb == 0b100: instr_name = 'blt'

                if instr_name:
                    imm_12 = (instruction_word >> 31) & 0x1
                    imm_10_5 = (instruction_word >> 25) & 0x3F
                    imm_4_1 = (instruction_word >> 8) & 0xF
                    imm_11 = (instruction_word >> 7) & 0x1

                    offset = (imm_12 << 12) | (imm_11 << 11) | (imm_10_5 << 5) | (imm_4_1 << 1)
                    offset = self.sign_extend(offset, 13)

                    rs1 = (instruction_word >> 15) & 0x1F
                    rs2 = (instruction_word >> 20) & 0x1F
                    return f"{instr_name} {self.REV_REGS.get(rs1, f'x{rs1}')}, {self.REV_REGS.get(rs2, f'x{rs2}')}, {offset}"

            if opcode == 0x6F:
                instr_name = 'jal'
                rd = (instruction_word >> 7) & 0x1F

                imm_20 = (instruction_word >> 31) & 0x1
                imm_10_1 = (instruction_word >> 21) & 0x3FF
                imm_11 = (instruction_word >> 20) & 0x1
                imm_19_12 = (instruction_word >> 12) & 0xFF

                offset = (imm_20 << 20) | (imm_19_12 << 12) | (imm_11 << 11) | (imm_10_1 << 1)
                offset = self.sign_extend(offset, 21)

                if rd == 0:
                    return f"j {offset}"
                return f"{instr_name} {self.REV_REGS.get(rd, f'x{rd}')}, {offset}"

        elif self.architecture == "MIPS":
            if opcode == 0x00:
                funct = instruction_word & 0x3F
                shamt = (instruction_word >> 6) & 0x1F
                key_r = (opcode, funct)
                if key_r in self.REV_OPCODES:
                    instr_name, fmt = self.REV_OPCODES[key_r]
                    if instr_name == 'jr':
                        rs = (instruction_word >> 21) & 0x1F
                        return f"{instr_name} {self.REV_REGS.get(rs, f'${rs}')}"
                    elif instr_name in ['sll', 'srl', 'sra']:
                        rd = (instruction_word >> 11) & 0x1F
                        rt = (instruction_word >> 16) & 0x1F
                        return f"{instr_name} {self.REV_REGS.get(rd, f'${rd}')}, {self.REV_REGS.get(rt, f'${rt}')}, {shamt}"
                    else:
                        rd = (instruction_word >> 11) & 0x1F
                        rs = (instruction_word >> 21) & 0x1F
                        rt = (instruction_word >> 16) & 0x1F
                        return f"{instr_name} {self.REV_REGS.get(rd, f'${rd}')}, {self.REV_REGS.get(rs, f'${rs}')}, {self.REV_REGS.get(rt, f'${rt}')}"

            opcode_i = (instruction_word >> 26) & 0x3F
            key_i = (opcode_i,)
            if key_i in self.REV_OPCODES:
                instr_name, fmt = self.REV_OPCODES[key_i]
                rs = (instruction_word >> 21) & 0x1F
                rt = (instruction_word >> 16) & 0x1F
                imm = instruction_word & 0xFFFF
                imm = self.sign_extend(imm, 16)

                if instr_name in ['lw', 'sw']:
                    return f"{instr_name} {self.REV_REGS.get(rt, f'${rt}')}, {imm}({self.REV_REGS.get(rs, f'${rs}')})"
                elif instr_name == 'addi':
                    return f"{instr_name} {self.REV_REGS.get(rt, f'${rt}')}, {self.REV_REGS.get(rs, f'${rs}')}, {imm}"
                elif instr_name == 'beq':
                    return f"{instr_name} {self.REV_REGS.get(rs, f'${rs}')}, {self.REV_REGS.get(rt, f'${rt}')}, {imm}"

            opcode_j = (instruction_word >> 26) & 0x3F
            key_j = (opcode_j,)
            if key_j in self.REV_OPCODES:
                instr_name, fmt = self.REV_OPCODES[key_j]
                target_addr = instruction_word & 0x3FFFFFF
                return f"{instr_name} 0x{target_addr << 2:08x}"

        return f"UNKNOWN_INSTRUCTION: 0x{instruction_word:08x}"


    def return_to_selection(self):
        if messagebox.askyesno("Confirmation", "Return to architecture selection? Current work will be lost."):
            self.root.destroy()
            show_arch_selection()

    def sign_extend(self, val, bits):
        if val & (1 << (bits - 1)):
            val = val - (1 << bits)
        return val & 0xFFFFFFFF

    def parse_inst(self, line):
        line = re.sub(r'#.*', '', line).strip()
        if not line:
            return None

        if ':' in line:
            label, rest = line.split(':', 1)
            label = label.strip()
            rest = rest.strip()
            if not rest:
                return None
            parts = self.parse_inst(rest)
            if parts:
                parts.append(label)
            return parts

        if self.architecture == "RISC-V":
            if line.split()[0] in ['lw', 'sw', 'jalr']:
                m = re.match(r'(\w+)\s+(\w+)\s*,\s*(-?\d+)\((\w+)\)', line)
                if m:
                    if m.group(1) == 'sw':
                        return [m.group(1), m.group(2), m.group(4), m.group(3)]
                    else:
                        return [m.group(1), m.group(2), m.group(4), m.group(3)]
            elif line.split()[0] == 'j':
                m = re.match(r'j\s+(\w+)', line)
                if m:
                    return ['jal', 'x0', m.group(1)]
        else:
            if line.split()[0] in ['lw', 'sw']:
                m = re.match(r'(\w+)\s+(\w+)\s*,\s*(-?\d+)\((\w+)\)', line)
                if m:
                    return [m.group(1), m.group(2), m.group(4), m.group(3)]
            elif line.split()[0] in ['sll', 'srl', 'sra']:
                m = re.match(r'(\w+)\s+(\S+)\s*,\s*(\S+)\s*,\s*(\S+)', line)
                if m:
                    return [m.group(1), m.group(2), m.group(3), m.group(4)]

        parts = line.replace(',', ' ').split()
        return parts

    def encode_inst(self, parts, labels, pc):
        _mem = parts[0]
        instr = self.OPCODES.get(_mem)
        if not instr:
            raise ValueError(f'Unknown instruction "{_mem}"')
        fmt = instr.fmt

        if self.architecture == "RISC-V":
            return self.encode_riscv(parts, labels, pc, _mem, instr, fmt)
        else:
            return self.encode_mips(parts, labels, pc, _mem, instr, fmt)

    def encode_riscv(self, parts, labels, pc, _mem, instr, fmt):
        if fmt == 'R':
            rd, rs1, rs2 = parts[1:4]
            funct7 = instr.funct7
            funct3 = instr.funct3
            return (funct7 << 25) | \
                   (self.REGS[rs2] << 20) | (self.REGS[rs1] << 15) | \
                   (funct3 << 12) | (self.REGS[rd] << 7) | instr.opcode

        elif fmt == 'I':
            if _mem == 'jalr':
                rd, rs1, imm = parts[1], parts[2], parts[3]
                imm_val = int(imm, 0)
            elif _mem == 'lw':
                rd, rs1, imm = parts[1], parts[2], parts[3]
                imm_val = int(imm, 0)
            else:
                rd, rs1, imm = parts[1], parts[2], parts[3]
                imm_val = int(imm, 0)
            imm_val = self.sign_extend(imm_val, 12)
            funct3 = instr.funct3
            return (imm_val << 20) | (self.REGS[rs1] << 15) | \
                   (funct3 << 12) | (self.REGS[rd] << 7) | instr.opcode

        elif fmt == 'S':
            rs2, rs1, imm = parts[1], parts[2], parts[3]
            imm_val = int(imm, 0)
            imm_val = self.sign_extend(imm_val, 12)
            imm_11_5 = (imm_val >> 5) & 0x7F
            imm_4_0 = imm_val & 0x1F
            funct3 = instr.funct3
            return (imm_11_5 << 25) | (self.REGS[rs2] << 20) | \
                   (self.REGS[rs1] << 15) | (funct3 << 12) | \
                   (imm_4_0 << 7) | instr.opcode

        elif fmt == 'SB':
            rs1, rs2, label = parts[1], parts[2], parts[3]
            if label not in labels:
                raise ValueError(f'Label "{label}" not found')
            offset = labels[label] - pc
            imm = self.sign_extend(offset, 13)
            funct3 = instr.funct3
            imm_12 = (imm >> 12) & 0x1
            imm_10_5 = (imm >> 5) & 0x3F
            imm_4_1 = (imm >> 1) & 0xF
            imm_11 = (imm >> 11) & 0x1

            return (imm_12 << 31) | (imm_10_5 << 25) | \
                   (self.REGS[rs2] << 20) | (self.REGS[rs1] << 15) | \
                   (funct3 << 12) | (imm_4_1 << 8) | \
                   (imm_11 << 7) | instr.opcode

        elif fmt == 'UJ':
            rd = parts[1]
            label = parts[2]

            if label not in labels:
                raise ValueError(f'Label "{label}" not found')
            offset = labels[label] - pc
            imm = self.sign_extend(offset, 21)

            imm_20 = (imm >> 20) & 0x1
            imm_10_1 = (imm >> 1) & 0x3FF
            imm_11 = (imm >> 11) & 0x1
            imm_19_12 = (imm >> 12) & 0xFF

            return (imm_20 << 31) | (imm_10_1 << 21) | (imm_11 << 20) | \
                   (imm_19_12 << 12) | (self.REGS[rd] << 7) | instr.opcode

        raise ValueError(f'Unsupported or incomplete format for "{_mem}"')

    def encode_mips(self, parts, labels, pc, _mem, instr, fmt):
        if fmt == 'R':
            if _mem == 'jr':
                rs = parts[1]
                return (instr.opcode << 26) | (self.REGS[rs] << 21) | (0 << 16) | \
                       (0 << 11) | (0 << 6) | instr.funct
            elif _mem in ['sll', 'srl', 'sra']:
                rd, rt, shamt = parts[1:4]
                return (instr.opcode << 26) | (0 << 21) | (self.REGS[rt] << 16) | \
                       (self.REGS[rd] << 11) | (int(shamt) << 6) | instr.funct
            else:
                rd, rs, rt = parts[1:4]
                return (instr.opcode << 26) | (self.REGS[rs] << 21) | (self.REGS[rt] << 16) | \
                       (self.REGS[rd] << 11) | (0 << 6) | instr.funct

        elif fmt == 'I':
            if _mem in ['lw', 'sw']:
                rt, offset, rs = parts[1], parts[2], parts[3]
                imm_val = self.sign_extend(int(offset, 0), 16)
                return (instr.opcode << 26) | (self.REGS[rs] << 21) | \
                       (self.REGS[rt] << 16) | (imm_val & 0xFFFF)
            elif _mem == 'beq':
                rs, rt, label = parts[1], parts[2], parts[3]
                if label not in labels:
                    raise ValueError(f'Label "{label}" not found')
                offset = (labels[label] - pc - 4) // 4
                imm_val = self.sign_extend(offset, 16)
                return (instr.opcode << 26) | (self.REGS[rs] << 21) | \
                       (self.REGS[rt] << 16) | (imm_val & 0xFFFF)
            elif _mem == 'blt':
                rs, rt, label = parts[1], parts[2], parts[3]
                if label not in labels:
                    raise ValueError(f'Label "{label}" not found')

                slt_code = (0x00 << 26) | (self.REGS[rs] << 21) | (self.REGS[rt] << 16) | \
                           (self.REGS['$at'] << 11) | (0x00 << 6) | 0x2A

                offset_bne = (labels[label] - (pc + 8)) // 4
                imm_val_bne = self.sign_extend(offset_bne, 16)
                bne_code = (0x05 << 26) | (self.REGS['$at'] << 21) | (self.REGS['$zero'] << 16) | (imm_val_bne & 0xFFFF)
                return (slt_code, bne_code)
            else:
                rt, rs, imm = parts[1], parts[2], parts[3]
                imm_val = self.sign_extend(int(imm, 0), 16)
                return (instr.opcode << 26) | (self.REGS[rs] << 21) | \
                       (self.REGS[rt] << 16) | (imm_val & 0xFFFF)

        elif fmt == 'J':
            label = parts[1]
            if label not in labels:
                raise ValueError(f'Label "{label}" not found')
            address = labels[label] // 4
            return (instr.opcode << 26) | (address & 0x3FFFFFF)

        raise ValueError(f'Unsupported or incomplete format for "{_mem}"')

    def show_docs(self):
        if self.architecture == "RISC-V":
            webbrowser.open("https://riscv.org/about/")
        else:
            webbrowser.open("https://www.mips.com/")

    def save_hex_file(self):
        if not self.assembled:
            messagebox.showwarning("Warning", "No assembled code to save")
            return

        file_path = filedialog.asksaveasfilename(
              defaultextension=".hex",
            filetypes=[("Hex Files", "*.hex"), ("All Files", "*.*")],
            title="Save Hex File"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    for line in self.assembled:
                        if '=>' in line:
                            hex_part = line.split('=>')[1].strip()
                            hex_to_write = hex_part.split(';')[0].strip()
                            if hex_to_write.startswith('0x'):
                                f.write(hex_to_write[2:] + '\n')
                messagebox.showinfo("Success", "Hex file saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def clear_all(self):
        self.input_box.delete("1.0", tk.END)
        self.output_box.delete("1.0", tk.END)
        self.terminal_box.delete("1.0", tk.END)
        self.assembled = []
        self.hex_map = {}
        self.copy_menu["menu"].delete(0, "end")
        self.selected_var.set("Select instruction")

    def on_exit(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.destroy()

    def load_example(self, example_name):
        self.clear_all()
        self.input_box.insert(tk.END, self.EXAMPLES[example_name])

    def copy_selected(self):
        sel = self.selected_var.get()
        if sel in self.hex_map:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.hex_map[sel])
            self.root.update()

    def assemble_all(self):
        asm = self.input_box.get("1.0", tk.END).strip().splitlines()
        self.output_box.delete("1.0", tk.END)
        self.terminal_box.delete("1.0", tk.END)
        self.copy_menu["menu"].delete(0, "end")
        self.assembled = []
        self.hex_map = {}

        labels = {}
        pc = 0

        for line_num, line in enumerate(asm):
            original_line = line.strip()
            line_clean = re.sub(r'#.*', '', original_line).strip()

            if not line_clean:
                continue

            if ':' in line_clean:
                label_part, rest = line_clean.split(':', 1)
                label_part = label_part.strip()
                labels[label_part] = pc
                line_clean = rest.strip()

            if not line_clean:
                continue

            parts = self.parse_inst(line_clean)
            if parts:
                _mem = parts[0]
                if self.architecture == "MIPS" and _mem == 'blt':
                    pc += 8
                else:
                    if self.architecture == "RISC-V" and _mem == 'jal' and parts[1] == 'x0':
                        pc += 4
                    else:
                        pc += 4

        pc = 0
        registers = {reg: 0 for reg in self.REGS}
        memory = {}

        for line_num, line in enumerate(asm):
            original_line_for_output = line.strip()
            line_clean = re.sub(r'#.*', '', line).strip()

            if not line_clean:
                continue

            if ':' in line_clean:
                line_clean = line_clean.split(':', 1)[1].strip()
                if not line_clean:
                    continue

            parts = self.parse_inst(line_clean)
            if not parts:
                continue

            try:
                current_pc_for_branch_target = pc

                code = self.encode_inst(parts, labels, current_pc_for_branch_target)

                if isinstance(code, tuple):
                    hex_codes = []
                    for c in code:
                        hex_codes.append(f'0x{c:08x}')
                    hex_code = '; '.join(hex_codes)
                    self.assembled.append(f'{original_line_for_output} => {hex_code}')
                    self.hex_map[original_line_for_output] = hex_code
                    pc += len(code) * 4
                else:
                    hex_code = f'0x{code:08x}'
                    self.assembled.append(f'{original_line_for_output} => {hex_code}')
                    self.hex_map[original_line_for_output] = hex_code
                    pc += 4

                self.copy_menu["menu"].add_command(
                    label=original_line_for_output,
                    command=lambda l=original_line_for_output: self.selected_var.set(l)
                )

                _mem = parts[0]
                if _mem == 'addi':
                    rd, rs1, imm = parts[1], parts[2], int(parts[3])
                    registers[rd] = self.sign_extend(registers.get(rs1, 0) + imm, 32)
                elif _mem == 'add':
                    rd, rs1, rs2 = parts[1], parts[2], parts[3]
                    registers[rd] = self.sign_extend(registers.get(rs1, 0) + registers.get(rs2, 0), 32)
                elif _mem == 'sub':
                    rd, rs1, rs2 = parts[1], parts[2], parts[3]
                    registers[rd] = self.sign_extend(registers.get(rs1, 0) - registers.get(rs2, 0), 32)
                elif _mem == 'mul':
                    rd, rs1, rs2 = parts[1], parts[2], parts[3]
                    registers[rd] = self.sign_extend(registers.get(rs1, 0) * registers.get(rs2, 0), 32)
                elif _mem == 'sll':
                    if self.architecture == "RISC-V":
                        rd, rs1, rs2 = parts[1], parts[2], parts[3]
                        shift_amount = registers.get(rs2, 0) % 32
                        registers[rd] = (registers.get(rs1, 0) << shift_amount) & 0xFFFFFFFF
                    elif self.architecture == "MIPS":
                        rd, rt, shamt = parts[1], parts[2], int(parts[3])
                        shift_amount = shamt % 32
                        registers[rd] = (registers.get(rt, 0) << shift_amount) & 0xFFFFFFFF
                elif _mem == 'srl':
                    if self.architecture == "RISC-V":
                        rd, rs1, rs2 = parts[1], parts[2], parts[3]
                        shift_amount = registers.get(rs2, 0) % 32
                        registers[rd] = (registers.get(rs1, 0) >> shift_amount) & 0xFFFFFFFF
                    elif self.architecture == "MIPS":
                        rd, rt, shamt = parts[1], parts[2], int(parts[3])
                        shift_amount = shamt % 32
                        registers[rd] = (registers.get(rt, 0) >> shift_amount) & 0xFFFFFFFF
                elif _mem == 'sra':
                    if self.architecture == "RISC-V":
                        rd, rs1, rs2 = parts[1], parts[2], parts[3]
                        shift_amount = registers.get(rs2, 0) % 32
                        val = self.sign_extend(registers.get(rs1, 0), 32)
                        registers[rd] = (val >> shift_amount)
                        registers[rd] &= 0xFFFFFFFF
                    elif self.architecture == "MIPS":
                        rd, rt, shamt = parts[1], parts[2], int(parts[3])
                        shift_amount = shamt % 32
                        val = self.sign_extend(registers.get(rt, 0), 32)
                        registers[rd] = (val >> shift_amount)
                        registers[rd] &= 0xFFFFFFFF
                elif _mem == 'slt':
                    if self.architecture == "RISC-V":
                        rd, rs1, rs2 = parts[1], parts[2], parts[3]
                        val1 = self.sign_extend(registers.get(rs1, 0), 32)
                        val2 = self.sign_extend(registers.get(rs2, 0), 32)
                        registers[rd] = 1 if val1 < val2 else 0
                    elif self.architecture == "MIPS":
                        rd, rs, rt = parts[1], parts[2], parts[3]
                        val1 = self.sign_extend(registers.get(rs, 0), 32)
                        val2 = self.sign_extend(registers.get(rt, 0), 32)
                        registers[rd] = 1 if val1 < val2 else 0
                elif _mem == 'sltu':
                    if self.architecture == "RISC-V":
                        rd, rs1, rs2 = parts[1], parts[2], parts[3]
                        val1 = registers.get(rs1, 0)
                        val2 = registers.get(rs2, 0)
                        registers[rd] = 1 if val1 < val2 else 0
                elif _mem == 'xor':
                    rd, rs1, rs2 = parts[1], parts[2], parts[3]
                    registers[rd] = (registers.get(rs1, 0) ^ registers.get(rs2, 0)) & 0xFFFFFFFF
                elif _mem == 'or':
                    rd, rs1, rs2 = parts[1], parts[2], parts[3]
                    registers[rd] = (registers.get(rs1, 0) | registers.get(rs2, 0)) & 0xFFFFFFFF
                elif _mem == 'and':
                    rd, rs1, rs2 = parts[1], parts[2], parts[3]
                    registers[rd] = (registers.get(rs1, 0) & registers.get(rs2, 0)) & 0xFFFFFFFF
                elif _mem == 'lw':
                    target_reg_name = parts[1]
                    base_reg_name = parts[2]
                    offset_val = int(parts[3])

                    addr = (registers.get(base_reg_name, 0) + offset_val)
                    if addr % 4 != 0:
                        raise ValueError(f"Unaligned memory access at address {addr}")
                    registers[target_reg_name] = memory.get(addr, 0)
                elif _mem == 'sw':
                    src_reg_name = parts[1]
                    base_reg_name = parts[2]
                    offset_val = int(parts[3])

                    addr = (registers.get(base_reg_name, 0) + offset_val)
                    if addr % 4 != 0:
                        raise ValueError(f"Unaligned memory access at address {addr}")
                    memory[addr] = registers.get(src_reg_name, 0)
                elif _mem == 'jal':
                    if self.architecture == "RISC-V":
                        rd = parts[1]
                        label = parts[2]
                        registers[rd] = pc
                        pc = labels[label]
                    else:
                        label = parts[1]
                        registers['$ra'] = pc
                        pc = labels[label]
                elif _mem == 'j':
                    if self.architecture == "RISC-V":
                        label = parts[2]
                        pc = labels[label]
                    else:
                        label = parts[1]
                        pc = labels[label]
                elif _mem == 'jalr':
                    if self.architecture == "RISC-V":
                        rd, rs1, imm = parts[1], parts[2], int(parts[3])
                        registers[rd] = pc
                        pc = (registers.get(rs1, 0) + imm)
                elif _mem == 'beq':
                    rs1, rs2, label = parts[1], parts[2], parts[3]
                    if registers.get(rs1, 0) == registers.get(rs2, 0):
                        pc = labels[label]
                elif _mem == 'blt':
                    if self.architecture == "RISC-V":
                        rs1, rs2, label = parts[1], parts[2], parts[3]
                        val1 = self.sign_extend(registers.get(rs1, 0), 32)
                        val2 = self.sign_extend(registers.get(rs2, 0), 32)
                        if val1 < val2:
                            pc = labels[label]
                    else:
                        rs1, rt, label = parts[1], parts[2], parts[3]
                        val1 = self.sign_extend(registers.get(rs1, 0), 32)
                        val2 = self.sign_extend(registers.get(rt, 0), 32) # Corrected from rs2 to rt
                        if val1 < val2:
                            pc = labels[label]
                elif _mem == 'jr':
                    rs = parts[1]
                    pc = registers.get(rs, 0)
            except Exception as e:
                self.assembled.append(f'{original_line_for_output} => ERROR: {e}')
                if self.architecture == "MIPS" and parts[0] == 'blt':
                    pc += 8
                else:
                    pc += 4

        if self.architecture == "RISC-V":
            sorted_regs = sorted(registers.keys(), key=lambda x: int(x[1:]))
        else:
            sorted_regs = sorted(self.REGS.keys(), key=lambda x: self.REGS[x])

        for r in sorted_regs:
            val = registers[r]
            self.terminal_box.insert(tk.END, f'{r} = {val}\n')

        if memory:
            self.terminal_box.insert(tk.END, '\nMemory:\n')
            for addr in sorted(memory):
                self.terminal_box.insert(tk.END, f'[{addr}] = 0x{memory[addr]:08x}\n')

        self.output_box.insert(tk.END, '\n'.join(self.assembled))

def show_arch_selection():
    root = tk.Tk()
    selection_window = ArchSelectionWindow(root)
    root.mainloop()

    if hasattr(selection_window, 'selected_arch') and selection_window.selected_arch:
        root = tk.Tk()
        app = AssemblerApp(root, selection_window.selected_arch)
        root.mainloop()

def main():
    show_arch_selection()

if __name__ == "__main__":
    main()