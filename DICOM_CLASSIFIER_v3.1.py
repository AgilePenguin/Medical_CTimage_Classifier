import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
import pandas as pd
import pydicom
from pathlib import Path

def select_source():
    path = filedialog.askdirectory(title="Dicom 원본 폴더 선택")
    if path:
        entry_source.delete(0, tk.END)
        entry_source.insert(0, path)

def select_target():
    path = filedialog.askdirectory(title="Dicom 도착지 폴더 선택")
    if path:
        entry_target.delete(0, tk.END)
        entry_target.insert(0, path)

def select_excel():
    path = filedialog.askopenfilename(title="엑셀 매칭 테이블 선택", filetypes=[("Excel files", "*.xlsx *.xls")])
    if path:
        entry_excel.delete(0, tk.END)
        entry_excel.insert(0, path)

def select_verify():
    path = filedialog.askdirectory(title="Verify 검증 대상 폴더 선택")
    if path:
        entry_verify.delete(0, tk.END)
        entry_verify.insert(0, path)

# ==========================================
# 1. 고도화된 자동 분류 로직 (Sorter)
# ==========================================
def run_sorting():
    source_path = entry_source.get()
    target_path = entry_target.get()
    excel_path = entry_excel.get()
    delete_original = delete_var.get()

    if not source_path or not target_path or not excel_path:
        messagebox.showwarning("경고", "분류(Sorting)를 위한 경로 3가지를 모두 지정해주세요.")
        return

    source_dir = Path(source_path)
    target_dir = Path(target_path)

    try:
        df = pd.read_excel(excel_path)
        col_patient = df.columns[0]
        col_pno = df.columns[1]
        
        df[col_patient] = df[col_patient].astype(str)
        mapping_dict = dict(zip(df[col_patient], df[col_pno]))

        success_count = 0
        skip_count = 0

        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                try:
                    ds = pydicom.dcmread(file_path, stop_before_pixels=True)
                    patient_num = str(getattr(ds, 'PatientID', 'Unknown'))
                    study_date = str(getattr(ds, 'StudyDate', 'UnknownDate'))
                    
                    p_no = mapping_dict.get(patient_num)
                    if not p_no:
                        skip_count += 1
                        continue

                    series_desc = str(getattr(ds, 'SeriesDescription', '')).upper()
                    study_desc = str(getattr(ds, 'StudyDescription', '')).upper()
                    view = None
                    
                    if "AX" in series_desc: view = "ax"
                    elif "CO" in series_desc: view = "co"
                    elif "SA" in series_desc: view = "sa"
                    
                    if not view:
                        if "AX" in study_desc: view = "ax"
                        elif "CO" in study_desc: view = "co"
                        elif "SA" in study_desc: view = "sa"

                    if not view:
                        skip_count += 1
                        continue
                    
                    instance_num = getattr(ds, 'InstanceNumber', None)
                    inst_str = str(int(instance_num)) if instance_num is not None else "0"

                    out_folder = target_dir / str(p_no) / study_date / view
                    out_folder.mkdir(parents=True, exist_ok=True)
                    
                    new_filename = f"{patient_num}{inst_str}.dcm"
                    new_file_path = out_folder / new_filename

                    if new_file_path.exists():
                         existing_files = len(list(out_folder.glob(f"{patient_num}*.dcm")))
                         new_filename = f"{patient_num}{existing_files + 1}.dcm"
                         new_file_path = out_folder / new_filename

                    shutil.copy2(file_path, new_file_path)
                    success_count += 1
                    
                    if delete_original:
                        file_path.unlink()

                except Exception:
                    pass

        messagebox.showinfo("1단계 완료", f"정렬 완료!\n- 성공: {success_count}개\n- 스킵(조건불일치): {skip_count}개")

    except Exception as e:
        messagebox.showerror("오류", f"정렬 중 문제 발생:\n{e}")

# ==========================================
# 2. 직관적인 Actionable Verify 로직 (Y/N/need to check)
# ==========================================
def run_verify():
    verify_path = entry_verify.get()
    excel_path = entry_excel.get()

    if not verify_path or not excel_path:
        messagebox.showwarning("경고", "Verify 검증 대상 폴더와 엑셀 파일을 지정해주세요.")
        return

    verify_dir = Path(verify_path)

    try:
        # Step 5: 엑셀 파일 비고 'N'인 경우 _no CT 빈 폴더 생성 유지
        df = pd.read_excel(excel_path)
        col_pno = df.columns[1]
        has_remark = len(df.columns) >= 4

        if has_remark:
            for idx, row in df.iterrows():
                p_no = str(row[col_pno]).strip()
                remark_val = str(row.iloc[3]).strip().upper()
                if remark_val == 'N':
                    no_ct_path = verify_dir / f"{p_no}_no CT"
                    no_ct_path.mkdir(exist_ok=True)
        
        verify_data = []

        # 각 타겟 폴더 (P name) 순회
        for target_folder in verify_dir.iterdir():
            if target_folder.is_dir():
                folder_name = target_folder.name
                
                # 1차 하위 폴더 개수 (Drill down 없이 바로 아래 폴더 개수만)
                sub_folders = [d for d in target_folder.iterdir() if d.is_dir()]
                sub_folder_count = len(sub_folders)
                
                has_ax = False
                has_co = False
                has_sa = False
                
                # 층화 상관없이 하위 구조 탐색하여 ax, co, sa 존재 및 내부 파일 유무 확인
                for root, dirs, files in os.walk(target_folder):
                    dir_name = Path(root).name.lower()
                    
                    # 숨김 파일 제외하고 실제 파일이 있는지 판별
                    valid_files = [f for f in files if not f.startswith('.')]
                    
                    if len(valid_files) > 0:
                        if 'ax' in dir_name or 'axial' in dir_name:
                            has_ax = True
                        if 'co' in dir_name or 'coronal' in dir_name or 'cor' in dir_name:
                            has_co = True
                        if 'sa' in dir_name or 'sagittal' in dir_name or 'sag' in dir_name:
                            has_sa = True
                            
                # 플래그 Y / N 할당
                ax_val = 'Y' if has_ax else 'N'
                co_val = 'Y' if has_co else 'N'
                sa_val = 'Y' if has_sa else 'N'
                
                # no CT? 판단 로직
                is_no_ct = False
                if not has_ax and not has_co and not has_sa:
                    if 'no ct' not in folder_name.lower():
                        is_no_ct = True
                        
                no_ct_val = 'Y' if is_no_ct else '-'
                
                # need to check? 판단 로직
                is_all_y = has_ax and has_co and has_sa
                if is_all_y or is_no_ct:
                    need_check_val = ''
                else:
                    need_check_val = 'Y'
                    
                verify_data.append([
                    folder_name, 
                    sub_folder_count, 
                    ax_val, 
                    co_val, 
                    sa_val, 
                    no_ct_val, 
                    need_check_val
                ])

        show_verify_window(verify_data, verify_dir)

    except Exception as e:
        messagebox.showerror("오류", f"Verify 실행 중 문제가 발생했습니다:\n{e}")

def show_verify_window(data, verify_dir):
    verify_win = tk.Toplevel(root)
    verify_win.title("Actionable Verified Table")
    verify_win.geometry("750x400")

    columns = ("P name", "sub folder", "ax", "co", "sa", "no CT?", "need to check?")
    tree = ttk.Treeview(verify_win, columns=columns, show='headings')

    col_widths = [120, 100, 80, 80, 80, 100, 120]
    for col, w in zip(columns, col_widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor='center')

    for row in data:
        tree.insert("", tk.END, values=row)

    scrollbar = ttk.Scrollbar(verify_win, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    try:
        out_df = pd.DataFrame(data, columns=columns)
        out_path = verify_dir / "Verified_Table_Result.xlsx"
        out_df.to_excel(out_path, index=False)
        tk.Label(verify_win, text=f"결과가 다음 경로에 저장되었습니다:\n{out_path.name}", fg="blue").pack(pady=5)
    except:
        pass

# ==========================================
# UI 셋업
# ==========================================
root = tk.Tk()
root.title("IMAT 파이프라인 (Actionable Verify 적용)")
root.geometry("620x550")
root.configure(padx=20, pady=20)

font_title = ("Malgun Gothic", 12, "bold")
font_label = ("Malgun Gothic", 11)
font_entry = ("Malgun Gothic", 10)
btn_color = "#ED7D31"
btn_fg = "white"

tk.Label(root, text="[공통] 환자번호 매칭 엑셀 파일 (4번째 열='비고' 권장)", font=font_title, fg="#2F5597").pack(anchor="w", pady=(0,5))
frame3 = tk.Frame(root)
frame3.pack(fill="x", pady=(0, 15))
entry_excel = tk.Entry(frame3, font=font_entry, relief="solid")
entry_excel.pack(side="left", fill="x", expand=True, ipady=4)
tk.Button(frame3, text="찾아보기", bg=btn_color, fg=btn_fg, command=select_excel).pack(side="right", padx=(10, 0), ipadx=10)

tk.Frame(root, height=1, bg="gray").pack(fill="x", pady=10)

tk.Label(root, text="[Step 1] Dicom 자동 정렬 (Sorter)", font=font_title, fg="#2F5597").pack(anchor="w", pady=(0,5))
tk.Label(root, text="Dicom 원본 폴더 경로:", font=font_label).pack(anchor="w")
frame1 = tk.Frame(root)
frame1.pack(fill="x", pady=(0, 5))
entry_source = tk.Entry(frame1, font=font_entry, relief="solid")
entry_source.pack(side="left", fill="x", expand=True, ipady=4)
tk.Button(frame1, text="찾아보기", bg=btn_color, fg=btn_fg, command=select_source).pack(side="right", padx=(10, 0), ipadx=10)

tk.Label(root, text="Dicom 저장 및 정렬될 도착지 폴더:", font=font_label).pack(anchor="w")
frame2 = tk.Frame(root)
frame2.pack(fill="x", pady=(0, 5))
entry_target = tk.Entry(frame2, font=font_entry, relief="solid")
entry_target.pack(side="left", fill="x", expand=True, ipady=4)
tk.Button(frame2, text="찾아보기", bg=btn_color, fg=btn_fg, command=select_target).pack(side="right", padx=(10, 0), ipadx=10)

delete_var = tk.BooleanVar(value=False)
tk.Checkbutton(root, text="분류 완료된 원본 파일 삭제하기", variable=delete_var, font=font_label).pack(anchor="w", pady=(0, 5))
tk.Button(root, text="▶ 1. 고도화 정렬 실행", bg="#4472C4", fg="white", font=("Malgun Gothic", 11, "bold"), command=run_sorting).pack(fill="x", ipady=6)

tk.Frame(root, height=1, bg="gray").pack(fill="x", pady=15)

tk.Label(root, text="[Step 2] Actionable 검증 (Verify)", font=font_title, fg="#2F5597").pack(anchor="w", pady=(0,5))
tk.Label(root, text="Verify 검증 대상 폴더 경로 (P100~P200 상위 폴더):", font=font_label).pack(anchor="w")
frame_verify = tk.Frame(root)
frame_verify.pack(fill="x", pady=(0, 10))
entry_verify = tk.Entry(frame_verify, font=font_entry, relief="solid")
entry_verify.pack(side="left", fill="x", expand=True, ipady=4)
tk.Button(frame_verify, text="찾아보기", bg=btn_color, fg=btn_fg, command=select_verify).pack(side="right", padx=(10, 0), ipadx=10)

tk.Button(root, text="✔ 2. Verify(검증) 실행", bg="#70AD47", fg="white", font=("Malgun Gothic", 11, "bold"), command=run_verify).pack(fill="x", ipady=6)

root.mainloop()
