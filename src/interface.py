"""Presentation layer for the planar measurement application."""
from pathlib import Path
import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

NAVY = '#183353'
TEAL = '#108b91'
BG = '#f3f6fa'
WHITE = '#ffffff'
MUTED = '#52657b'


def build_interface(app):
    root = app.root
    root.title('TranKhoaAn_22021579')
    root.geometry('1440x920')
    root.minsize(1160, 790)
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=('Segoe UI', 10), foreground=NAVY)
    style.configure('TFrame', background=WHITE)
    style.configure('TLabel', background=WHITE, foreground=NAVY)
    style.configure('TButton', padding=(8, 4), background='#e8eef4', borderwidth=0)
    style.map('TButton', background=[('active', '#d9e4ed')])
    style.configure('Primary.TButton', background=TEAL, foreground=WHITE)
    style.map('Primary.TButton', background=[('active', '#07777d')])
    style.configure('TLabelframe', background=WHITE, bordercolor='#d7e0e9', relief='solid')
    style.configure('TLabelframe.Label', background=WHITE, font=('Segoe UI', 12, 'bold'))
    style.configure('TEntry', padding=5)
    style.configure('TCombobox', padding=5)

    header = tk.Frame(root, bg=WHITE, padx=18, pady=6)
    header.pack(fill='x', padx=12, pady=(10, 7))
    logo_path = Path(__file__).resolve().parents[1] / 'assets/uet_logo.png'
    if logo_path.exists():
        logo = Image.open(logo_path).convert('RGBA')
        logo.thumbnail((235, 62), Image.Resampling.LANCZOS)
        app.logo_photo = ImageTk.PhotoImage(logo)
        tk.Label(header, image=app.logo_photo, bg=WHITE).pack(side='left', padx=(0, 22))
    identity = tk.Frame(header, bg=WHITE)
    identity.pack(side='left', fill='x', expand=True)
    tk.Label(identity, text='ĐỒ ÁN TỐT NGHIỆP', font=('Segoe UI', 9, 'bold'), fg=TEAL, bg=WHITE).pack(anchor='w')
    title = tk.Label(identity, text='ƯỚC LƯỢNG KÍCH THƯỚC VẬT THỂ BẰNG THỊ GIÁC MÁY', font=('Segoe UI', 16, 'bold'), fg=NAVY, bg=WHITE, anchor='w', justify='left', wraplength=1030)
    title.pack(anchor='w', fill='x')
    identity.bind('<Configure>', lambda e: title.configure(wraplength=max(500, e.width-10)))
    tk.Label(identity, text='Trần Khoa An   •   MSV: 22021579   •   Lớp: K67-M-AT', font=('Segoe UI', 11), bg=WHITE, fg=NAVY).pack(anchor='w', pady=(3, 0))
    tk.Label(identity, text='Giảng viên hướng dẫn: Đinh Trần Hiệp', font=('Segoe UI', 10), bg=WHITE, fg=MUTED).pack(anchor='w')

    main = tk.Frame(root, bg=BG)
    main.pack(fill='both', expand=True, padx=12)
    main.columnconfigure(0, weight=1)
    main.columnconfigure(1, weight=0, minsize=405)
    main.rowconfigure(0, weight=1)
    left = tk.Frame(main, bg=BG)
    left.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
    left.rowconfigure(0, weight=1)
    left.columnconfigure(0, weight=1)
    view = tk.Frame(left, bg=WHITE, highlightthickness=1, highlightbackground='#d7e0e9')
    view.grid(row=0, column=0, sticky='nsew')
    view.rowconfigure(1, weight=1)
    view.columnconfigure(0, weight=1)
    top = tk.Frame(view, bg=WHITE)
    top.grid(row=0, column=0, sticky='ew', padx=10, pady=9)
    tk.Label(top, text='Hình ảnh camera', bg=WHITE, fg=NAVY, font=('Segoe UI', 12, 'bold')).pack(side='left')
    app.camera_state_var = tk.StringVar(value='Chưa kết nối')
    tk.Label(top, textvariable=app.camera_state_var, bg=WHITE, fg=TEAL).pack(side='right')
    video_area = tk.Frame(view, bg='#e7edf3', width=760, height=440)
    video_area.grid(row=1, column=0, sticky='nsew', padx=9, pady=(0, 9))
    video_area.grid_propagate(False)
    video_area.rowconfigure(0, weight=1)
    video_area.columnconfigure(0, weight=1)
    app.video_label = tk.Label(video_area, text='CAMERA CHƯA KHỞI ĐỘNG\n\nBấm Bắt đầu để mở hình ảnh', bg='#e7edf3', fg=MUTED, anchor='center', font=('Segoe UI', 13))
    app.video_label.grid(row=0, column=0, sticky='nsew')
    app.video_label.bind('<Button-1>', app._on_video_click)

    result = tk.Frame(left, bg=WHITE, padx=14, pady=10, highlightthickness=1, highlightbackground='#d7e0e9')
    result.grid(row=1, column=0, sticky='ew', pady=(10, 0))
    tk.Label(result, text='KẾT QUẢ ĐO', bg=WHITE, fg=NAVY, font=('Segoe UI', 11, 'bold')).pack(anchor='w')
    nums = tk.Frame(result, bg=WHITE)
    nums.pack(fill='x', pady=(7, 3))
    app.length_display = tk.StringVar(value='— mm')
    app.width_display = tk.StringVar(value='— mm')
    app.quality_display = tk.StringVar(value='Ổn định: —\nHình học: —')
    for label, var in [('Chiều dài', app.length_display), ('Chiều rộng', app.width_display)]:
        col = tk.Frame(nums, bg=WHITE)
        col.pack(side='left', expand=True, fill='x')
        tk.Label(col, text=label, bg=WHITE, fg=MUTED).pack(anchor='w')
        tk.Label(col, textvariable=var, bg=WHITE, fg=TEAL, font=('Segoe UI', 24, 'bold')).pack(anchor='w')
    tk.Label(nums, textvariable=app.quality_display, bg=WHITE, fg=NAVY, justify='left').pack(side='right', padx=8)
    tk.Label(result, textvariable=app.result_var, bg=WHITE, fg='#9a4c16', wraplength=740, justify='left', anchor='w').pack(fill='x')

    side = ttk.Frame(main, width=405)
    side.grid(row=0, column=1, sticky='nsew')
    side.grid_propagate(False)
    scroller = tk.Canvas(side, width=405, highlightthickness=0, bg=WHITE)
    scroll = ttk.Scrollbar(side, orient='vertical', command=scroller.yview)
    scroller.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right', fill='y')
    scroller.pack(side='left', fill='both', expand=True)
    right = ttk.Frame(scroller)
    window = scroller.create_window((0,0), window=right, anchor='nw')
    scroller.bind('<Configure>', lambda e: scroller.itemconfigure(window, width=e.width))
    right.bind('<Configure>', lambda e: scroller.configure(scrollregion=scroller.bbox('all')))
    def wheel(event):
        if right.winfo_reqheight() > scroller.winfo_height():
            scroller.yview_scroll(int(-event.delta/120), 'units')
    def bind_wheel(widget):
        widget.bind('<MouseWheel>', wheel, add='+')
        for child in widget.winfo_children(): bind_wheel(child)
    right.columnconfigure(0, weight=1)
    def group(name):
        f = ttk.LabelFrame(right, text=name, padding=8)
        f.pack(fill='x', pady=(0, 9))
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)
        return f
    def row(parent, label, var, r):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky='w', pady=2)
        ttk.Entry(parent, textvariable=var, width=10).grid(row=r, column=1, sticky='ew', padx=(8,0), pady=2)
    def pair(parent, a, b, r):
        f=ttk.Frame(parent);f.grid(row=r,column=0,columnspan=2,sticky='ew',pady=4)
        ttk.Entry(f,textvariable=a,width=10).pack(side='left',expand=True,fill='x')
        ttk.Label(f,text=' × ').pack(side='left')
        ttk.Entry(f,textvariable=b,width=10).pack(side='left',expand=True,fill='x')
    def buttons(parent, items, r):
        f=ttk.Frame(parent);f.grid(row=r,column=0,columnspan=2,sticky='ew',pady=(5,2))
        for i,(name,cmd,primary) in enumerate(items):
            ttk.Button(f,text=name,command=cmd,style='Primary.TButton' if primary else 'TButton').pack(side='left',expand=True,fill='x',padx=(0,5 if i<len(items)-1 else 0))
    f=group('1   Camera và nhận dạng')
    ttk.Label(f,text='Camera').grid(row=0,column=0,sticky='w')
    ttk.Spinbox(f,from_=0,to=10,textvariable=app.camera_var,width=8).grid(row=0,column=1,sticky='ew',padx=(8,0))
    ttk.Label(f,text='Chế độ nhận dạng').grid(row=1,column=0,columnspan=2,sticky='w',pady=(6,2))
    ttk.Combobox(f,textvariable=app.detector_var,state='readonly',values=('Nền trống (khuyên dùng)','Contour (nhanh)','YOLO11-seg','Kết hợp')).grid(row=2,column=0,columnspan=2,sticky='ew')
    row(f,'Ngưỡng tin cậy',app.conf_var,3)
    buttons(f,[('Bắt đầu',app.start,True),('Dừng',app.stop,False)],4)
    f=group('2   Hiệu chuẩn mặt phẳng')
    ttk.Label(f,textvariable=app.calibration_var,foreground=TEAL,wraplength=350).grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,4))
    ttk.Label(f,text='Mẫu chữ nhật R × C (mm)').grid(row=1,column=0,columnspan=2,sticky='w')
    pair(f,app.reference_width_var,app.reference_height_var,2)
    buttons(f,[('Chọn 4 góc',app.begin_manual_calibration,True),('Xóa hiệu chuẩn',app.clear_plane,False)],3)
    row(f,'Cạnh ArUco (mm)',app.marker_size_var,4)
    buttons(f,[('Khóa theo ArUco',app.lock_aruco_plane,False)],5)
    row(f,'Camera–mặt phẳng (cm)',app.distance_cm_var,6)
    buttons(f,[('Ghi nền trống',app.capture_empty_background,False)],7)
    f=group('3   Lưu mẫu đo')
    ttk.Label(f,text='Kích thước đối chiếu D × R (mm)').grid(row=0,column=0,columnspan=2,sticky='w')
    pair(f,app.true_length_var,app.true_width_var,1)
    buttons(f,[('LƯU MẪU (ẢNH + CSV)',app.save_sample,True)],2)
    ttk.Label(f,text='Một lần bấm lưu đồng thời ảnh và số liệu.',foreground=MUTED,wraplength=350).grid(row=3,column=0,columnspan=2,sticky='w',pady=(4,0))
    footer=tk.Frame(root,bg=WHITE,padx=12,pady=5)
    footer.pack(side='bottom',fill='x',pady=(8,0),before=main)
    tk.Label(footer,textvariable=app.status_var,bg=WHITE,fg=MUTED,anchor='w',wraplength=970).pack(side='left',fill='x',expand=True)
    ttk.Button(footer,text='Mở thư mục ảnh',command=lambda: open_images(app)).pack(side='right')
    app.result_var.trace_add('write',lambda *_: refresh_result(app))
    bind_wheel(right)


def refresh_result(app):
    result=app.last_result
    if result:
        app.length_display.set(f"{result['length_mm']:.1f} mm")
        app.width_display.set(f"{result['width_mm']:.1f} mm")
        app.quality_display.set(f"Ổn định: {max(0.,1.-result['stability_cv']):.1%}\nHình học: {result['rectangularity']:.0%}")
    else:
        app.length_display.set('— mm');app.width_display.set('— mm')
        app.quality_display.set('Ổn định: —\nHình học: —')


def open_images(app):
    folder=Path(__file__).resolve().parents[1]/'measurement_images'
    folder.mkdir(exist_ok=True)
    os.startfile(str(folder))
