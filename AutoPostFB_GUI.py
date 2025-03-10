import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from groq import Groq
import json
import os
import random
import time
import re
import threading
import psutil

def save_settings():
	settings = {
		"email": email_entry.get(),
		"password": password_entry.get(),
		"use_profile": profile_var.get(),
		"api_key": api_key_entry.get(),
		"models": models_entry.get(),
		"groups": groups_listbox.get(0, tk.END),
		"prompt": prompt_entry.get("1.0", tk.END).strip(),
		"image_folder": image_folder_entry.get().strip(),
		"chrome_profile_path": chrome_profile_entry.get().strip(),
		"xpath_login_success": xpath_login_success_entry.get().strip(),
		"xpath_avatar": xpath_avatar_entry.get().strip(),
		"xpath_second_account": xpath_second_account_entry.get().strip(),
		"xpath_image_button": xpath_image_button_entry.get().strip(),
		"xpath_upload_image": xpath_upload_image_entry.get().strip(),
		"xpath_post_box_pre": xpath_post_box_pre_entry.get().strip(),
		"xpath_post_box_xpaths": xpath_post_box_xpaths_entry.get("1.0", tk.END).strip(),
		"xpath_post_button": xpath_post_button_entry.get().strip(),
		"xpath_switch_account_confirmation": xpath_switch_account_confirmation_entry.get().strip(),
		"xpath_post_confirmation": xpath_post_confirmation_entry.get().strip(),
	}
	with open("settings.json", "w", encoding="utf-8") as file:
		json.dump(settings, file, indent=4)

def load_settings():
	if os.path.exists("settings.json"):
		with open("settings.json", "r", encoding="utf-8") as file:
			settings = json.load(file)
			email_entry.insert(0, settings.get("email", ""))
			password_entry.insert(0, settings.get("password", ""))
			profile_var.set(settings.get("use_profile", False))
			api_key_entry.insert(0, settings.get("api_key", ""))
			models_entry.delete(0, tk.END)
			models_entry.insert(0, settings.get("models", ""))
			prompt_entry.delete("1.0", tk.END)
			prompt_entry.insert("1.0", settings.get("prompt", ""))
			image_folder_entry.delete(0, tk.END)
			image_folder_entry.insert(0, settings.get("image_folder", ""))
			for group in settings.get("groups", []):
				groups_listbox.insert(tk.END, group)
			chrome_profile_entry.delete(0, tk.END)
			chrome_profile_entry.insert(0, settings.get("chrome_profile_path", ""))
			xpath_login_success_entry.delete(0, tk.END)
			xpath_login_success_entry.insert(0, settings.get("xpath_login_success", ""))
			xpath_avatar_entry.delete(0, tk.END)
			xpath_avatar_entry.insert(0, settings.get("xpath_avatar", ""))
			xpath_second_account_entry.delete(0, tk.END)
			xpath_second_account_entry.insert(0, settings.get("xpath_second_account", ""))
			xpath_image_button_entry.delete(0, tk.END)
			xpath_image_button_entry.insert(0, settings.get("xpath_image_button", ""))
			xpath_upload_image_entry.delete(0, tk.END)
			xpath_upload_image_entry.insert(0, settings.get("xpath_upload_image", ""))
			xpath_post_box_pre_entry.delete(0, tk.END)
			xpath_post_box_pre_entry.insert(0, settings.get("xpath_post_box_pre", ""))
			xpath_post_box_xpaths_entry.delete("1.0", tk.END)
			xpath_post_box_xpaths_entry.insert("1.0", settings.get("xpath_post_box_xpaths", ""))
			xpath_post_button_entry.delete(0, tk.END)
			xpath_post_button_entry.insert(0, settings.get("xpath_post_button", ""))
			xpath_switch_account_confirmation_entry.delete(0, tk.END)
			xpath_switch_account_confirmation_entry.insert(0, settings.get("xpath_switch_account_confirmation", ""))
			xpath_post_confirmation_entry.delete(0, tk.END)
			xpath_post_confirmation_entry.insert(0, settings.get("xpath_post_confirmation", ""))
	else:
		print("Tệp settings.json không tồn tại.")

def on_closing():
	save_settings()
	root.destroy()

def init_driver():
	if not is_chrome_running():
		update_status("Chrome chưa được mở. Đang khởi chạy trình duyệt...")
	else:
		update_status("Bắt đầu...")

	options = webdriver.ChromeOptions()
	options.add_argument("--disable-notifications")
	
	if profile_var.get():
		profile_path = chrome_profile_entry.get().strip()
		options.add_argument(f"user-data-dir={profile_path}")
		options.add_argument("--profile-directory=Default")
	
	driver = webdriver.Chrome(options=options)
	options.add_experimental_option("detach", True)
	start_chrome_monitoring()  # Bắt đầu theo dõi Chrome
	return driver
	
def is_logged_in(driver):
	try:
		login_success = driver.find_element(By.XPATH, xpath_login_success_entry.get().strip())
		if login_success.is_displayed():
			return True
	except Exception:
		return False

def facebook_login(driver, email, password):
	driver.get("https://www.facebook.com")
	time.sleep(2)
	if is_logged_in(driver):
		avatar_xpath = xpath_avatar_entry.get().strip()
		if avatar_xpath:
			avatar = WebDriverWait(driver, 30).until(
				EC.presence_of_element_located((By.XPATH, xpath_avatar_entry.get().strip()))
			)
			avatar.click()
			time.sleep(2)
			update_status("Chuyển sang Facebook phụ")
			second_account = WebDriverWait(driver, 30).until(
				EC.presence_of_element_located((By.XPATH, xpath_second_account_entry.get().strip()))
			)
			second_account.click()
			time.sleep(2)
			WebDriverWait(driver, 30).until(
				EC.presence_of_element_located((By.XPATH, xpath_switch_account_confirmation_entry.get().strip()))
			)
			update_status("Chuyển sang Facebook phụ thành công")
		return True
	email_input = driver.find_element(By.ID, "email")
	email_input.send_keys(email)
	password_input = driver.find_element(By.ID, "pass")
	password_input.send_keys(password)
	password_input.send_keys(Keys.RETURN)
	time.sleep(5)

	update_status("Đang chờ xác thực nếu có...")
	while not is_logged_in(driver):  # Lặp cho đến khi đăng nhập thành công
		time.sleep(5)

	update_status("Đăng nhập Facebook thành công")
	return True
	
def generate_content(prompt):
	# Thiết lập biến môi trường
	os.environ['GROQ_API_KEY'] = api_key_entry.get().strip()
	
	# Kiểm tra xem API key đã được thiết lập chưa
	api_key = os.environ.get("GROQ_API_KEY")
	if not api_key:
		raise ValueError("API key is not set. Please set the GROQ_API_KEY environment variable.")
	models = models_entry.get().strip().split(';')
	# Chọn ngẫu nhiên một model từ danh sách
	selected_model = random.choice(models).strip()

	client = Groq(api_key=api_key)
	chat_completion = client.chat.completions.create(
		messages=[
			{
				"role": "user",
				"content": prompt,
			}
		],
		# model="llama-3.3-70b-versatile",
		model=selected_model,
		temperature=0.8,  # Giá trị cao hơn sẽ tạo ra kết quả đa dạng hơn
		top_p=0.9
	)
	return chat_completion.choices[0].message.content

def upload_images(driver, image_folder):
	image_paths = [os.path.join(image_folder, filename) for filename in os.listdir(image_folder)
				   if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
	
	for image_path in image_paths:
		image_button = WebDriverWait(driver, 30).until(
			EC.presence_of_element_located((By.XPATH, xpath_image_button_entry.get().strip()))
		)
		image_button.click()
		time.sleep(5)

		upload_image = WebDriverWait(driver, 30).until(
			EC.presence_of_element_located((By.XPATH, xpath_upload_image_entry.get().strip()))
		)
		upload_image.send_keys(image_path)
		time.sleep(1)
		
def post_to_groups(driver, groups):
	failed_groups = []
	image_folder = image_folder_entry.get().strip()

	for group_url in groups:
		update_status(f"Đang truy cập liên kết {group_url}...")
		driver.get(group_url)
		time.sleep(5)  # Tăng thời gian chờ

		try:
			post_box_pre = WebDriverWait(driver, 30).until(
				EC.presence_of_element_located((By.XPATH, xpath_post_box_pre_entry.get().strip()))
			)
			post_box_pre.click()
			time.sleep(2)

			prompt = prompt_entry.get("1.0", tk.END).strip()
			content = generate_content(prompt)

			# post_box_xpaths = [
				# xpath_post_box_xpaths_entry.get().strip()
			# ]

			post_box_xpaths = [xpath.strip() for xpath in xpath_post_box_xpaths_entry.get("1.0", tk.END).splitlines() if xpath.strip()]
			print("Danh sách XPath được load:", post_box_xpaths)
			post_box = None
			for xpath in post_box_xpaths:
				try:
					post_box = WebDriverWait(driver, 30).until(
						EC.presence_of_element_located((By.XPATH, xpath))
					)
					post_box = driver.find_element(By.XPATH, xpath)
					break
				except Exception as e:
					continue  # Thử với XPath tiếp theo

			if post_box:
				time.sleep(2)
				post_box.send_keys(content)
				time.sleep(2)

				if image_folder:
					upload_images(driver, image_folder)

				post_button = driver.find_element(By.XPATH, xpath_post_button_entry.get().strip())
				post_button.click()
				time.sleep(5)

				WebDriverWait(driver, 30).until(
					EC.invisibility_of_element_located((By.XPATH, xpath_post_confirmation_entry.get().strip()))
				)

				update_status(f"Đã đăng vào {group_url} thành công!")
			else:
				update_status(f"Không tìm thấy hộp thoại để đăng bài trong {group_url}")
				failed_groups.append(group_url)

		except Exception as e:
			update_status(f"Đăng bài không thành công: {group_url}: {e}")
			failed_groups.append(group_url)

	if failed_groups:
		update_status("Các nhóm đăng không thành công:")
		for failed_group in failed_groups:
			update_status(f"- {failed_group}")
	else:
		update_status("Tất cả các nhóm đều đã đăng thành công!")

def start_posting():
	thread = threading.Thread(target=run_posting, daemon=True)
	thread.start()

def run_posting():
	driver = init_driver()
	email = email_entry.get()
	password = password_entry.get()
	groups = list(groups_listbox.get(0, tk.END))

	if facebook_login(driver, email, password):
		post_to_groups(driver, groups)

def delete_selected_group():
	selected_indices = groups_listbox.curselection()
	if selected_indices:
		for index in reversed(selected_indices):
			groups_listbox.delete(index)

def import_groups_from_file():
	file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")])
	if file_path:
		with open(file_path, 'r', encoding='utf-8') as file:
			groups_listbox.delete(0, tk.END)
			for line in file:
				group_url = line.strip()
				if group_url:
					groups_listbox.insert(tk.END, group_url)

def select_image_folder():
	folder_path = filedialog.askdirectory()
	if folder_path:
		image_folder_entry.delete(0, tk.END)
		image_folder_entry.insert(0, folder_path)
		
def update_status(message):
	status_text.insert(tk.END, message + "\n")
	status_text.update_idletasks()
	
def is_chrome_running():
	"""Kiểm tra xem Chrome có đang chạy không"""
	for process in psutil.process_iter(attrs=['name']):
		if "chrome" in process.info['name'].lower():  # Kiểm tra tên tiến trình
			return True
	return False
	
def monitor_chrome():
	"""Theo dõi Chrome liên tục, nếu bị tắt thì thông báo"""
	while True:
		if not is_chrome_running():
			messagebox.showwarning("Cảnh báo", "Trình duyệt Chrome đã bị tắt!")
			update_status("Trình duyệt Chrome đã bị tắt!")
			break  # Ngừng theo dõi khi Chrome tắt
		time.sleep(5)  # Kiểm tra mỗi 5 giây

def start_chrome_monitoring():
	"""Chạy theo dõi Chrome trên một luồng riêng"""
	thread = threading.Thread(target=monitor_chrome, daemon=True)
	thread.start()

# Tạo giao diện
root = tk.Tk()
root.title("Auto Post Facebook Group Simple")
root.geometry("600x600")
root.protocol("WM_DELETE_WINDOW", on_closing)

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

facebook_tab = ttk.Frame(notebook)
notebook.add(facebook_tab, text="Facebook")

login_frame = ttk.LabelFrame(facebook_tab, text="Đăng nhập Facebook")
login_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(login_frame, text="Email:").grid(row=0, column=0, padx=5, pady=5)
email_entry = ttk.Entry(login_frame, width=40)
email_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(login_frame, text="Mật khẩu:").grid(row=1, column=0, padx=5, pady=5)
password_entry = ttk.Entry(login_frame, width=40, show="*")
password_entry.grid(row=1, column=1, padx=5, pady=5)

profile_var = tk.BooleanVar()
profile_check = ttk.Checkbutton(login_frame, text="Sử dụng profile Chrome hiện tại", variable=profile_var)
profile_check.grid(row=2, columnspan=2, padx=5, pady=5)

group_frame = ttk.LabelFrame(facebook_tab, text="Quản lý nhóm Facebook")
group_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(group_frame, text="Nhập liên kết nhóm:").grid(row=0, column=0, padx=5, pady=5)
group_entry = ttk.Entry(group_frame, width=40)
group_entry.grid(row=0, column=1, padx=5, pady=5)

add_group_button = ttk.Button(group_frame, text="Thêm", command=lambda: groups_listbox.insert(tk.END, group_entry.get()))
add_group_button.grid(row=0, column=2, padx=5, pady=5)

import_button = ttk.Button(group_frame, text="Nhập từ file", command=import_groups_from_file)
import_button.grid(row=1, column=0, padx=5, pady=5)

remove_group_button = ttk.Button(group_frame, text="Xóa nhóm đã chọn", command=delete_selected_group)
remove_group_button.grid(row=1, column=1, padx=5, pady=5)

groups_listbox = tk.Listbox(facebook_tab, width=60, height=6, selectmode=tk.MULTIPLE)
groups_listbox.pack()

start_post_button = ttk.Button(facebook_tab, text="Bắt đầu đăng", command=start_posting)
start_post_button.pack(pady=10)

# Khung hiển thị trạng thái
status_frame = ttk.LabelFrame(facebook_tab, text="Trạng thái")
status_frame.pack(fill="both", padx=10, pady=5)

status_text = tk.Text(status_frame, height=15, width=70)
status_text.pack(padx=5, pady=5)
status_text.config(state=tk.NORMAL)

# Tab Groq AI
groq_tab = ttk.Frame(notebook)
notebook.add(groq_tab, text="Groq AI")

ttk.Label(groq_tab, text="Groq API Key:").pack(pady=(10, 0))
api_key_entry = ttk.Entry(groq_tab, width=50, show="*")
api_key_entry.pack(padx=5, pady=5)

ttk.Label(groq_tab, text="Nhập tên các mô hình AI (ngăn cách bằng dấu chấm phẩy):").pack(pady=(10, 0))
models_entry = ttk.Entry(groq_tab, width=50)
models_entry.pack(padx=5, pady=5)

ttk.Label(groq_tab, text="Nhập prompt cho bài đăng:").pack(pady=(10, 0))
prompt_entry = tk.Text(groq_tab, height=15, width=50)
prompt_entry.pack(padx=5, pady=5)

# Tab Hình ảnh
image_tab = ttk.Frame(notebook)
notebook.add(image_tab, text="Hình ảnh")

ttk.Label(image_tab, text="Chọn thư mục chứa hình ảnh:").pack(pady=(10, 0))
image_folder_entry = ttk.Entry(image_tab, width=50)
image_folder_entry.pack(padx=5, pady=5)

select_image_button = ttk.Button(image_tab, text="Chọn thư mục", command=select_image_folder)
select_image_button.pack(pady=(5, 10))

# Thêm tab Thông tin phần mềm
info_tab = ttk.Frame(notebook)
notebook.add(info_tab, text="Thông tin phần mềm")

# Thêm nội dung cho tab Thông tin phần mềm
info_label = ttk.Label(info_tab, text="Thông tin phần mềm", font=("Arial", 16))
info_label.pack(pady=(10, 0))
software_info = """
Tên phần mềm: Auto Post Facebook Group Simple
Tác giả: TekDT
Email: dinhtrungtek@gmail.com
Telegram: @tekdt1152
Zalo: 0944.095.092
Mô tả: Phần mềm tự động đăng bài lên Facebook với nội dung tạo tự động bằng AI, hỗ trợ chuyển đổi tài khoản facebook phụ và hỗ trợ tải lên hình ảnh
Phiên bản: 1.0
Ngày phát hành: 3/3/2023
"""
info_text = tk.Text(info_tab, height=10, width=70)
info_text.insert(tk.END, software_info)
info_text.config(state=tk.DISABLED)  # Không cho phép chỉnh sửa
info_text.pack(padx=5, pady=5)

# Tab Thiết lập
settings_tab = ttk.Frame(notebook)
notebook.add(settings_tab, text="Thiết lập")

ttk.Label(settings_tab, text="Đường dẫn profile Chrome:").grid(row=0, column=0, padx=5, pady=5)
chrome_profile_entry = ttk.Entry(settings_tab, width=40)
chrome_profile_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath login success:").grid(row=1, column=0, padx=5, pady=5)
xpath_login_success_entry = ttk.Entry(settings_tab, width=40)
xpath_login_success_entry.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath avatar:").grid(row=2, column=0, padx=5, pady=5)
xpath_avatar_entry = ttk.Entry(settings_tab, width=40)
xpath_avatar_entry.grid(row=2, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath xác nhận đã chuyển trang cá nhân khác:").grid(row=3, column=0, padx=5, pady=5)
xpath_switch_account_confirmation_entry = ttk.Entry(settings_tab, width=40)
xpath_switch_account_confirmation_entry.grid(row=3, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath second_account:").grid(row=4, column=0, padx=5, pady=5)
xpath_second_account_entry = ttk.Entry(settings_tab, width=40)
xpath_second_account_entry.grid(row=4, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath image_button:").grid(row=5, column=0, padx=5, pady=5)
xpath_image_button_entry = ttk.Entry(settings_tab, width=40)
xpath_image_button_entry.grid(row=5, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath upload_image:").grid(row=6, column=0, padx=5, pady=5)
xpath_upload_image_entry = ttk.Entry(settings_tab, width=40)
xpath_upload_image_entry.grid(row=6, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath post_box_pre:").grid(row=7, column=0, padx=5, pady=5)
xpath_post_box_pre_entry = ttk.Entry(settings_tab, width=40)
xpath_post_box_pre_entry.grid(row=7, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath post_box_xpaths:").grid(row=8, column=0, padx=5, pady=5)
xpath_post_box_xpaths_entry = tk.Text(settings_tab, height=5, width=40)
xpath_post_box_xpaths_entry.grid(row=8, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath post_button:").grid(row=9, column=0, padx=5, pady=5)
xpath_post_button_entry = ttk.Entry(settings_tab, width=40)
xpath_post_button_entry.grid(row=9, column=1, padx=5, pady=5)

ttk.Label(settings_tab, text="XPath xác nhận đã đăng:").grid(row=10, column=0, padx=5, pady=5)
xpath_post_confirmation_entry = ttk.Entry(settings_tab, width=40)
xpath_post_confirmation_entry.grid(row=10, column=1, padx=5, pady=5)

load_settings()
root.mainloop()