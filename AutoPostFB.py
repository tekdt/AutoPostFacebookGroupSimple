import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
                             QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QListWidget, QTextEdit,
                             QTabWidget, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from openai import OpenAI
from mistralai import Mistral
import groq
import google.generativeai as genai
import json
import os
import random
import time
import threading
import psutil
import sys
import pickle
import re
import csv
import glob
import hashlib

# Biến toàn cục để kiểm soát luồng và Selenium
stop_event = threading.Event()
driver = None
COOKIE_FILE = "facebook_cookies.pkl"
version = "2.0.0"
released_date = "11/04/2025"

# Định nghĩa các định dạng file cần kiểm tra
image_extensions = [
    '*.jpg', '*.jpeg',  # image/jpeg
    '*.png',           # image/png
    '*.gif',           # image/gif
    '*.bmp',          # image/bmp
    '*.webp',         # image/webp
    '*.tiff', '*.tif', # image/tiff
    '*.heif',         # image/heif
    '*.heic',         # image/heic
    '*.svg',          # image/svg+xml
    '*.ico',          # image/x-icon
    '*.psd',          # image/vnd.adobe.photoshop
    '*.raw',          # image/x-raw
    '*.cr2',          # Canon RAW
    '*.nef',          # Nikon RAW
    '*.dng',          # Digital Negative
    '*.ai',           # Adobe Illustrator
    '*.eps',          # image/eps
    '*.pcx',          # image/x-pcx
    '*.ppm',          # image/x-portable-pixmap
    '*.xcf'           # GIMP image file
]
audio_extensions = [
    '*.mp3',          # audio/mpeg
    '*.wav',          # audio/wav
    '*.aac',          # audio/aac
    '*.ogg',          # audio/ogg
    '*.flac',         # audio/flac
    '*.m4a',          # audio/mp4
    '*.wma',          # audio/x-ms-wma
    '*.opus',         # audio/opus
    '*.amr',          # audio/amr
    '*.aiff', '*.aif', # audio/aiff
    '*.mid', '*.midi', # audio/midi
    '*.ac3',          # audio/ac3
    '*.ra', '*.rm',    # audio/x-pn-realaudio
    '*.ape',          # audio/ape
    '*.au',           # audio/basic
    '*.voc',          # audio/x-voc
    '*.weba',         # audio/webm
    '*.dsd',          # audio/dsd
    '*.mka',          # audio/x-matroska
    '*.qcp'           # audio/qcelp
]
video_extensions = [
    '*.mp4',          # video/mp4
    '*.avi',          # video/x-msvideo
    '*.mov',          # video/quicktime
    '*.mkv',          # video/x-matroska
    '*.flv',          # video/x-flv
    '*.wmv',          # video/x-ms-wmv
    '*.webm',         # video/webm
    '*.m4v',          # video/x-m4v
    '*.3gp',          # video/3gpp
    '*.vob',          # video/dvd
    '*.ogv',          # video/ogg
    '*.ts',           # video/mp2t
    '*.mpeg', '*.mpg', # video/mpeg
    '*.rm', '*.rmvb',  # video/vnd.rn-realvideo
    '*.asf',          # video/x-ms-asf
    '*.divx',         # video/divx
    '*.m2ts',         # video/m2ts
    '*.f4v',          # video/x-f4v
    '*.mxf',          # video/mxf
    '*.swf'           # application/x-shockwave-flash
]

key_map = {
    "Nhóm": "groups",
    "Gửi tin nhắn tới thành viên nhóm": "members",
    "Trang": "pages",
    "Marketplace": "marketplace",
    "Groups": "groups",
    "Send message to group members": "members",
    "Pages": "pages"
}

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cả khi chạy từ EXE và script """
    if getattr(sys, 'frozen', False):
        # Trường hợp chạy từ EXE: PyInstaller tạo thư mục tạm '_MEIXXXXXX'
        base_path = sys._MEIPASS
    else:
        # Trường hợp chạy từ script: Lấy đường dẫn thư mục hiện tại
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ChromeDriverThread(QThread):
    driver_ready = pyqtSignal(object)  # Tín hiệu phát ra khi driver sẵn sàng

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window  # Tham chiếu đến MainWindow để truy cập các thuộc tính như profile_check

    def run(self):
        # Cấu hình ChromeOptions
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        desktop_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        options.add_argument(f"user-agent={desktop_user_agent}")

        # Kiểm tra checkbox headless
        if self.window.headless_check.isChecked():
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")  # Cần thiết cho headless trên một số hệ thống
        
        # Sử dụng profile Chrome nếu được chọn
        if self.window.profile_check.isChecked():
            profile_path = self.window.profile_path if hasattr(self.window, 'profile_path') else None
            if profile_path:
                options.add_argument(f"user-data-dir={profile_path}")
                options.add_argument("--profile-directory=Default")

        # Khởi tạo driver
        driver = webdriver.Chrome(options=options)
        options.add_experimental_option("detach", True)

        # Phát tín hiệu rằng driver đã sẵn sàng
        self.driver_ready.emit(driver)

class ChromeMonitorThread(QThread):
    chrome_closed = pyqtSignal()

    def run(self):
        while True:
            if not self.is_chrome_running():
                self.chrome_closed.emit()
                break
            time.sleep(5)

    @staticmethod
    def is_chrome_running():
        for process in psutil.process_iter(attrs=['name']):
            if "chrome" in process.info['name'].lower():
                return True
        return False

class LoginThread(QThread):
    login_success = pyqtSignal()
    status_updated = pyqtSignal(str)

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.email = window.email_entry.text()
        self.password = window.password_entry.text()
        self.driver = self.window.driver

    def run(self):
        if self.driver is None:
            self.status_updated.emit(self.window.translate("LoginThread_driver_is_not_initialized"))
            return
        self.driver.get("https://facebook.com")
        time.sleep(2)

        # Thử tải cookie trước
        if self.load_cookies(self.driver):
            self.driver.get("https://facebook.com")
            time.sleep(2)
            if self.is_logged_in(self.driver):
                self.status_updated.emit(self.window.translate("LoginThread_logged_in_by_cookie"))
                if self.window.sub_account_check.isChecked():
                    self.switch_to_sub_account(self.driver)
                self.login_success.emit()
                return

        # Đăng nhập thủ công
        try:
            email_input = self.driver.find_element(By.ID, "m_login_email")
            email_input.send_keys(self.email)
            password_input = self.driver.find_element(By.ID, "m_login_password")
            password_input.send_keys(self.password)
            self.driver.find_element(By.XPATH, "//div[@data-anchor-id='replay' and @role='button']").click()
            time.sleep(5)
        except NoSuchElementException:
            self.status_updated.emit(self.window.translate("LoginThread_not_found_login_input"))

        self.status_updated.emit(self.window.translate("LoginThread_waitting_for_login"))
        while not self.is_logged_in(self.driver) and not stop_event.is_set():
            time.sleep(5)

        if stop_event.is_set():
            return
        self.status_updated.emit(self.window.translate("LoginThread_logged_in_successful"))
        self.save_cookies(self.driver)
        if self.window.sub_account_check.isChecked():
            self.switch_to_sub_account(self.driver)
        self.login_success.emit()

    def is_logged_in(self, driver):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//form[starts-with(@action, '/logout.php') and contains(@action, 'logout')]"))
            )
            return True
        except Exception:
            return False

    def save_cookies(self, driver):
        cookies = driver.get_cookies()
        with open(COOKIE_FILE, "wb") as file:
            pickle.dump(cookies, file)
        self.status_updated.emit(self.window.translate("LoginThread_saved_cookie_to_file"))

    def load_cookies(self, driver):
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, "rb") as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            self.status_updated.emit(self.window.translate("LoginThread_loaded_cookie_from_file"))
            return True
        return False

    def switch_to_sub_account(self, driver):
        sub_account_name = self.window.sub_account_entry.text().strip()
        try:
            account_menu = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@aria-expanded and contains(@class, 'x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w') and @role='button' and @tabindex='0']"))
            )
            account_menu.click()
            time.sleep(2)
            try:
                # Kiểm tra account đã active chưa (nếu có thì không cần click)
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '/me/') and contains(@class, 'x1i10hfl xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20') and @role='link' and @tabindex='0']//span[text()='{sub_account_name}' and @dir='auto']"))
                )
            except TimeoutException:
                # Nếu không tìm thấy account active -> click switch
                switch_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[@role='button' and @tabindex='0' and contains(@aria-label, '{sub_account_name}')]"))
                )
                switch_btn.click()
                time.sleep(5)
            self.status_updated.emit(self.window.translate("LoginThread_switched_to_sub_account",sub_account_name=sub_account_name))
            self.save_cookies(driver)  # Lưu lại cookie sau khi chuyển tài khoản
        except TimeoutException as e:
            self.status_updated.emit(self.window.translate("LoginThread_could_not_switch_to_sub_account", sub_account_name=sub_account_name, e="Timeout waiting for element"))
        except NoSuchElementException as e:
            self.status_updated.emit(self.window.translate("LoginThread_could_not_switch_to_sub_account", sub_account_name=sub_account_name, e="Element not found"))
        except Exception as e:
            self.status_updated.emit(self.window.translate("LoginThread_could_not_switch_to_sub_account", sub_account_name=sub_account_name, e=str(e)))

class FetchDataThread(QThread):
    fetch_completed = pyqtSignal()
    fetch_failed = pyqtSignal(str)
    status_updated = pyqtSignal(str)

    def __init__(self, window, data_type, url=None, parent=None):
        super().__init__(parent)
        self.window = window
        self.data_type = data_type
        self.url = url
        self.driver = self.window.driver
        self.items = []

    def run(self):
        if self.driver is None:
            self.status_updated.emit(self.window.translate("LoginThread_driver_is_not_initialized"))
            return
        try:
            self.items = self.fetch_data(self.driver, self.data_type, self.url)
            if stop_event.is_set():
                self.status_updated.emit(self.window.translate("FetchDataThread_stopped_to_get_data_by_request"))
                return
            if self.items:  # Chỉ tiếp tục nếu có dữ liệu
                self.window.url_items_list.clear()
                for item in self.items:
                    self.window.url_items_list.addItem(item)
                self.window.save_settings()
                self.fetch_completed.emit()
            else:
                tmp_data_type = self.data_type
                self.status_updated.emit(self.window.translate("FetchDataThread_could_not_get_data"))
        except Exception as e:
            self.status_updated.emit(self.window.translate("FetchDataThread_error_during_fetching_data", e=str(e)))

    def fetch_data(self, driver, data_type, url=None):
        if driver is None:
            self.status_updated.emit(self.window.translate("LoginThread_driver_is_not_initialized"))
            return []
        self.status_updated.emit(self.window.translate("FetchDataThread_start_fetching_data", data_type=data_type, url=url))
        """Lấy danh sách nhóm hoặc danh sách thành viên tùy thuộc vào data_type."""
        if data_type == "groups":
            driver.get("https://www.facebook.com/groups/joins/?nav_source=tab")
        elif data_type == "members":
            if not url:
                self.status_updated.emit(self.window.translate("FetchDataThread_provide_group_url"))
                return []
            driver.get(url.rstrip('/') + "/members")
        time.sleep(5)
        items = set()
        last_count = 0
        no_new_items_count = 0
        max_no_new_items = 10  # Số lần cuộn không có nhóm mới trước khi dừng
        scroll_attempts = 0
        save_interval = 10  # Lưu sau mỗi 10 liên kết mới
        new_items_count = 0
        
        while no_new_items_count < max_no_new_items and not stop_event.is_set():
            # Lấy vị trí hiện tại trước khi cuộn
            current_position = driver.execute_script("return window.pageYOffset;")
            window_height = driver.execute_script("return window.innerHeight;")
            
            # Cuộn xuống dưới cùng
            self.smooth_scroll_to_position(driver, current_position + window_height)
            for _ in range(20):
                if stop_event.is_set():
                    break
                time.sleep(0.1)
            
            # Kiểm tra xem có cuộn được không
            new_position = driver.execute_script("return window.pageYOffset;")
            if new_position == current_position:
                # Nếu không cuộn được xuống nữa, thử cuộn lên đầu rồi xuống lại
                self.smooth_scroll_to_position(driver, 0)
                for _ in range(20):
                    if stop_event.is_set():
                        break
                    time.sleep(0.1)
                self.smooth_scroll_to_position(driver, new_position)
                for _ in range(20):
                    if stop_event.is_set():
                        break
                    time.sleep(0.1)
                scroll_attempts += 1
                if scroll_attempts > 3:  # Nếu đã thử nhiều lần mà không cuộn được
                    break
            
            # Lấy danh sách nhóm mới
            try:
                if data_type == "groups":
                    elements = driver.find_elements(
                        By.XPATH, "//div[@role='listitem' and @style]//div[@class='x1lq5wgf xgqcy7u x30kzoy x9jhf4c x9f619 xktsk01 xl1xv1r']//a[contains(@href, '/groups/') and not(contains(@href, 'category')) and @role='link' and @tabindex='0']"
                    )
                elif data_type == "members":
                    elements = driver.find_elements(
                        By.XPATH, "//a[contains(@href, '/groups/') and contains(@href, '/user/') and @tabindex='0' and @role='link']"  # XPath cho liên kết tin nhắn của thành viên
                    )
                
                current_items_count = len(items)
                
                for element in elements:
                    if stop_event.is_set():  # Kiểm tra lại trước khi thêm item
                        break
                    item_url = element.get_attribute("href")
                    if item_url:
                        clean_url = item_url.split("?")[0]
                        if data_type == "members":
                            user_id = clean_url.rstrip("/").split("/")[-1]  # Lấy phần cuối của URL
                            clean_url = f"https://www.facebook.com/messages/t/{user_id}"  # Tạo URL mới
                            
                        if clean_url not in items:
                            items.add(clean_url)
                            new_items_count += 1
                            current_urls = [self.window.url_items_list.item(i).text() for i in range(self.window.url_items_list.count())]
                            if clean_url not in current_urls:
                                self.window.url_items_list.addItem(clean_url)
                            # Lưu mỗi 10 item cho cả "groups" và "members"
                            if new_items_count >= save_interval:
                                if data_type == "groups":
                                    self.window.settings["groups"] = list(items)
                                elif data_type == "members":
                                    self.window.settings["members"] = list(items)
                                self.window.save_settings()
                                count_items = len(items)
                                self.status_updated.emit(self.window.translate("FetchDataThread_saved_items_to_settings", count_items=count_items, data_type=data_type))
                                new_items_count = 0
                
                # Kiểm tra dữ liệu mới
                if len(items) == current_items_count:
                    no_new_items_count += 1
                else:
                    no_new_items_count = 0
                    
                count_items = len(items)
                self.status_updated.emit(self.window.translate("FetchDataThread_fetched_items", count_items=count_items, data_type=data_type))
                
            except Exception as e:
                self.status_updated.emit(self.window.translate("FetchDataThread_fetching_failed", data_type=data_type, e=str(e)))
                break  # Thoát nếu có lỗi
        
        # Cập nhật giao diện hoặc lưu dữ liệu
        if data_type == "groups":
            self.window.settings["groups"] = list(items)
        elif data_type == "members":
            self.window.settings["members"] = list(items)

        self.window.save_settings()
        count_items = len(items)
        self.status_updated.emit(self.window.translate("FetchDataThread_fetch_completed", data_type=data_type, count_items=count_items))
        
        self.items = list(items)
        return list(items)

    def smooth_scroll_to_position(self, driver, target_y, duration=2):
        # Giữ nguyên hàm smooth_scroll_to_position từ PostingThread
        current_y = driver.execute_script("return window.pageYOffset;")
        distance = target_y - current_y
        if distance == 0 or stop_event.is_set():
            return
        step = 100 if distance > 0 else -100
        steps_count = abs(distance) // abs(step)
        if steps_count == 0:
            steps_count = 1
        sleep_time = duration / steps_count
        while (distance > 0 and current_y < target_y) or (distance < 0 and current_y > target_y):
            if stop_event.is_set():
                break
            current_y += step
            if (distance > 0 and current_y > target_y) or (distance < 0 and current_y < target_y):
                current_y = target_y
            driver.execute_script(f"window.scrollTo(0, {current_y});")
            time.sleep(sleep_time)
        driver.execute_script(f"window.scrollTo(0, {target_y});")

class PostingThread(QThread):
    status_updated = pyqtSignal(str)
    content_updated = pyqtSignal(str)
    stop_requested = pyqtSignal()
    
    def __init__(self, window, location, valid_urls, parent=None):
        super().__init__(parent)
        self.window = window
        self.location = location
        self.valid_urls = valid_urls
        self.driver = self.window.driver
    
    def run(self):
        if self.driver is None:
            self.status_updated.emit(self.window.translate("LoginThread_driver_is_not_initialized"))
            return

        self.post_to_location(self.driver, self.location, self.valid_urls)

    # Hàm đọc danh sách ID đã gửi từ file CSV
    def is_id_sent(self, user_id):
        """Kiểm tra xem user_id đã được gửi tin nhắn chưa"""
        if os.path.exists("sent_ids.csv"):
            with open("sent_ids.csv", "r", encoding="utf-8") as file:
                sent_ids = {line.strip() for line in file}
                return user_id in sent_ids
        return False

    # Hàm lưu ID đã gửi vào file CSV
    def save_sent_id(self, user_id):
        """Lưu user_id vào tệp sent_ids.csv"""
        with open("sent_ids.csv", "a", encoding="utf-8") as file:
            file.write(f"{user_id}\n")

    def upload_images(self, driver, image_folder):
        if stop_event.is_set():
            return
        image_paths = [os.path.join(image_folder, filename) for filename in os.listdir(image_folder)
                       if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        if self.window.random_image_check.isChecked():
            # Chọn ngẫu nhiên từ 1 đến số lượng hình ảnh có sẵn
            num_images = random.randint(1, len(image_paths))
            image_paths = random.sample(image_paths, num_images)
        for image_path in image_paths:
            upload_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w')]//input[contains(@accept, 'image/*,image/heif,image/heic,video') and @class='x1s85apg' and @multiple and @type='file']"))
            )
            upload_input.send_keys(image_path)
            time.sleep(1)

    def post_to_location(self, driver, location, urls):
        failed_urls = []
        image_folder = self.window.image_folder_entry.text().strip()
        encrypt_code = self.window.encrypt_message_code_input.text().strip()
        prompt = self.window.prompt_entry.toPlainText().strip()
        content = None  # Khởi tạo content
        failed_times = 0
        
        # Kiểm tra từng loại file
        has_images = any(glob.glob(os.path.join(image_folder, ext)) for ext in image_extensions)
        has_audio = any(glob.glob(os.path.join(image_folder, ext)) for ext in audio_extensions)
        has_video = any(glob.glob(os.path.join(image_folder, ext)) for ext in video_extensions)

        for url in urls:
            if stop_event.is_set():
                self.status_updated.emit(self.window.translate("PostingThread_stopping"))
                return
            driver.get(url)
            time.sleep(5)

            # Tạo nội dung mới nếu bật tự động
            if self.window.auto_generate_check.isChecked():
                try:
                    content = self.window.generate_content_ai(self.window.server_combo.currentText(), 
                                                           self.window.model_combo.currentText(), 
                                                           prompt)
                    # Kiểm tra nội dung có hợp lệ hay không
                    if any(err in content.lower() for err in ["balance", "error", "api key is not set", "máy chủ không hỗ trợ"]):
                        raise ValueError(self.status_updated.emit(self.window.translate("PostingThread_generated_content_error")))
                    # Cập nhật ô xem trước với nội dung hợp lệ
                    self.content_updated.emit(content)
                except Exception as e:
                    self.status_updated.emit(self.window.translate("PostingThread_error_during_generate_content", e=str(e)))
                    content = self.window.get_random_content_from_json()
                    if not content:
                        self.status_updated.emit(self.window.translate("PostingThread_not_found_backup_content"))
                        # self.window.stop_posting()
                        self.stop_requested.emit()
                        return
                    self.content_updated.emit(content)
            else:
                # Nếu không tự động tạo, lấy nội dung từ ô nhập tay (nếu có)
                content = self.window.content_preview.toPlainText().strip()
                if not content:  # Kiểm tra nếu nội dung rỗng
                    content = self.window.get_random_content_from_json()
                    if not content:
                        self.status_updated.emit(self.window.translate("PostingThread_content_is_empty"))
                        # self.window.stop_posting()
                        self.stop_requested.emit()
                        return
                    self.content_updated.emit(content)

            try:
                if location == self.window.translate("group_location_position_option"):
                    group_id = url.rstrip("/").split("/")[-1]
                    #Tìm tên nhóm
                    try:
                        group_title_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@class='x1e56ztr x1xmf6yo']//h1[@dir='auto' and contains(@class, 'html-h1 xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu')]//a[contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee') and @tabindex='0' and @role='link' and contains(@href, 'https://')]"))
                        )
                        group_title = group_title_element.text
                    except:
                        group_title = url

                    try:
                        # Nhấn vào nút đăng bài
                        post_box_button = WebDriverWait(driver, 10).until(
                           EC.element_to_be_clickable((By.XPATH, r"//div[contains(@class, 'x1i10hfl x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l') and @role='button' and @tabindex='0']//div[@class='xi81zsa x1lkfr7t xkjl1po x1mzt3pk xh8yej3 x13faqbe']//span[@class='x1lliihq x6ikm8r x10wlt62 x1n2onr6' and @style]")) # Tìm ô đăng bài để nhấp vào ngay trên trang chủ của nhóm
                        )
                    except TimeoutException:
                        self.status_updated.emit(self.window.translate("PostingThread_posting_dialog_button_not_found", group_title=group_title, group_id=group_id))
                        failed_urls.append(url)
                        continue

                    post_box_button.click()
                    
                    try:
                        # Xác định ô đăng bài
                        post_box = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, r"//div[contains(@class, 'xzsf02u x1a2a7pz x1n2onr6 x14wi4xw x9f619 x1lliihq x5yr21d') and @contenteditable='true' and @role='textbox' and @spellcheck='true' and @tabindex='0' and @data-lexical-editor='true' and @aria-placeholder]"))
                        )
                    except TimeoutException:
                        self.status_updated.emit(self.window.translate("PostingThread_posting_dialog_not_found", group_title=group_title, group_id=group_id))
                        failed_urls.append(url)
                        continue
                    
                    post_box.send_keys(content)
                    
                    # Chờ đến khi toàn bộ nội dung được nhập
                    timeout = 10  # Giới hạn thời gian chờ (10 giây)
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        entered_text = post_box.get_attribute("innerText")  # Lấy nội dung đã nhập
                        if entered_text.strip() == content.strip():  # So sánh nội dung đã nhập với nội dung gốc
                            break
                        time.sleep(0.5)  # Đợi thêm một chút rồi kiểm tra lại
                    
                    if (has_images or has_audio or has_video) and not stop_event.is_set():
                        # Xác định nút đính kèm hình ảnh và click vào đó
                        immages_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, r"//span[contains(@class, 'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5')]//div[contains(@aria-label, '/video') and contains(@class, 'x1i10hfl x1qjc9v5 xjqpnuy xa49m3k xqeqjp1 x2hbi6w') and @role='button' and @tabindex='0']//div[@class='xc9qbxq x1n2onr6 x14qfxbe x14yjl9h xudhj91 x18nykt9 xww2gxu']//div[@class='x6s0dn4 x78zum5 xl56j7k x1n2onr6 x5yr21d xh8yej3']//img[@class='x1b0d499 xl1xv1r' and contains(@src, '.png') and @alt and @style]"))
                        )
                        immages_button.click()
                        
                        if image_folder:
                            self.upload_images(driver, image_folder)
                    
                    try:
                        # Nút đăng
                        post_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'x9f619 x1ja2u2z x78zum5 x2lah0s x1n2onr6 x1qughib x1qjc9v5')]//div[@role='button' and @tabindex='0' and contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf')]//div[@role='none' and contains(@class, 'x9f619 x1n2onr6 x1ja2u2z x193iq5w xeuugli x6s0dn4 x78zum5')]//span[contains(@class, 'x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv') and @dir='auto']"))
                        )
                    except TimeoutException:
                        self.status_updated.emit(self.window.translate("PostingThread_posting_button_not_found", group_title=group_title, group_id=group_id))
                        failed_urls.append(url)
                        continue
                    post_button.click()
                    
                    # Facebook không cho phép đăng bài
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((
                                By.XPATH,
                                "//div[@data-visualcompletion='ignore-dynamic' and @style]//div[@aria-disabled='false' and @class='x1lq5wgf xgqcy7u x30kzoy x9jhf4c x1lliihq']//span[@dir='auto' and contains(@class, 'x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq') and @id]//div[contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf') and @role='button' and @tabindex='0']"
                            ))
                        )
                        self.status_updated.emit(self.window.translate("PostingThread_failed_to_post", group_title=group_title, group_id=group_id))
                        failed_urls.append(url)
                        continue
                    except TimeoutException:
                        pass
                        
                    try:
                        #Chờ đăng bài thành công và ô đăng bài biến mất
                        WebDriverWait(driver, 60).until(
                            EC.invisibility_of_element_located((By.XPATH, r"//div[@class='x78zum5 x92rtbv x10l6tqk x1tk7jg1']//div[contains(@class, 'x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3') and @aria-label and @role='button' and @tabindex='0']//i[contains(@style, '.png') and @data-visualcompletion='css-img' and @class='x1b0d499 x1d69dk1' and @aria-hidden='true']"))
                        )
                    except TimeoutException:
                        self.status_updated.emit(self.window.translate("PostingThread_posting_dialog_not_disappear", group_title=group_title, group_id=group_id))
                        failed_urls.append(url)
                        continue
                    self.status_updated.emit(self.window.translate("PostingThread_post_successful", group_title=group_title, group_id=group_id))
                    
                    # Xóa URL khỏi url_items_list và lưu settings
                    self.window.remove_url_from_list(url)
                    self.window.save_settings()
                elif location == "Marketplace":
                    listing_type = self.window.listing_type_combo.currentText()
                    for _ in range(self.window.marketplace_post_count):  # Dự phòng cho số lần đăng
                        self.post_marketplace_item(driver, f"https://facebook.com/marketplace/create/{listing_type}")
                elif location == self.window.translate("pages_location_position_option") or location == "Pages":
                    post_box = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
                    )
                    post_box.click()
                    post_box.send_keys(content)
                    if image_folder:
                        self.upload_images(driver, image_folder)
                    post_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                    post_button.click()

                elif location == self.window.translate("members_location_position_option") or location == "Send message to group members":
                    if failed_times >= 3:
                        self.status_updated.emit(self.window.translate("PostingThread_blocked_posting"))
                        break
                    # Kiểm tra xem ID đã gửi chưa
                    user_id = url.split("/")[-1]  # Lấy user_id từ url (ví dụ: 132013598798057)
                    if self.is_id_sent(user_id):
                        self.status_updated.emit(self.window.translate("PostingThread_skip_member", url=url))
                        continue  # Bỏ qua nếu đã gửi
                    
                    #Tìm tên người dùng
                    try:
                        user_name_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x193iq5w')]//h2[@dir='auto' and contains(@class, 'html-h2 xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu')]//span[contains(@class, 'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5')]"))
                        )
                        user_name = user_name_element.text
                    except:
                        user_name = url
                    
                    #Kiểm tra xem có xuất hiện yêu cầu nhập mã hóa tin nhắn đầu cuối hay không
                    try:
                        encrypt_dialog_input = driver.find_element(By.XPATH, r"//div[@class='x1n2onr6']//input[contains(@class, 'x1i10hfl x9f619 xggy1nq xtpw4lu x1tutvks x1s3xk63 x1s07b3s') and @dir='ltr' and @autocomplete='one-time-code' and @id='mw-numeric-code-input-prevent-composer-focus-steal' and @maxlength='6' and @type='text' and @value and @tabindex='0']")
                        if encrypt_dialog_input:
                            encrypt_dialog_input.send_keys(encrypt_code)
                            WebDriverWait(driver, 30).until_not(
                                EC.presence_of_element_located((By.XPATH, r"//div[@class='x1n2onr6']//input[contains(@class, 'x1i10hfl x9f619 xggy1nq xtpw4lu x1tutvks x1s3xk63 x1s07b3s') and @dir='ltr' and @autocomplete='one-time-code' and @id='mw-numeric-code-input-prevent-composer-focus-steal' and @maxlength='6' and @type='text' and @value and @tabindex='0']"))
                            )
                    except:
                        pass
                    
                    # Nút tiếp tục mã hoá tin nhắn đầu cuối
                    try:
                        continue_encrypt_button = driver.find_element(By.XPATH, r"//div[contains(@class, 'x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w')]//div[@aria-label and contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf') and @role='button' and @tabindex='0']//span[contains(@class, 'x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft')]")
                        if continue_encrypt_button:
                            continue_encrypt_button.click()
                    except:
                        pass
                    
                    try:
                        # Xác định ô tin nhắn
                        message_box = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, r"//div[@aria-placeholder and @role='textbox' and @spellcheck='true' and @contenteditable='true' and @aria-label and @aria-describedby and @data-lexical-editor='true']"))
                        )
                        message_box.send_keys(content)
                    except:
                        self.status_updated.emit(self.window.translate("PostingThread_not_found_input_message_box", user_name=user_name, user_id=user_id))
                        failed_urls.append(url)
                        continue
                    
                    # Chờ đến khi toàn bộ nội dung được nhập
                    timeout = 30  # Giới hạn thời gian chờ (30 giây)
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        entered_text = message_box.get_attribute("innerText")  # Lấy nội dung đã nhập
                        if entered_text.strip() == content.strip():  # So sánh nội dung đã nhập với nội dung gốc
                            break
                        time.sleep(0.5)  # Đợi thêm một chút rồi kiểm tra lại
                    
                    try:
                        # Xác định nút gửi tin nhắn và click vào đó
                        send_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, r"//span[contains(@class, 'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5')]//div[@role='button' and @tabindex='0' and contains(@aria-label, 'Enter') and contains(@class, 'x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1')]"))
                        )
                    except:
                        self.status_updated.emit(self.window.translate("PostingThread_not_found_send_button", user_name=user_name, user_id=user_id))
                        failed_urls.append(url)
                        continue
                    send_button.click()
                    
                    # Chờ đến khi toàn bộ nội dung được nhập
                    timeout = 30  # Giới hạn thời gian chờ (30 giây)
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        entered_text = message_box.get_attribute("innerText")  # Lấy nội dung đã nhập
                        if entered_text.strip() == "":  # Kiểm tra xem nội dung đã được gửi hết chưa
                            break
                        time.sleep(2)  # Đợi thêm một chút rồi kiểm tra lại

                    # Facebook không cho gửi tin nhắn
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((
                            By.XPATH,
                            "//div[contains(@class, 'html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu')]//span[@role='presentation' and contains(@class, 'html-span x1mh8g0r x1hl2dhg x16tdsg8 x1vvkbs x1eb86dx')]//span[contains(@class, 'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu')]"
                        ))
                    )
                    sending_status_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu')]//span[@role='presentation' and contains(@class, 'html-span x1mh8g0r x1hl2dhg x16tdsg8 x1vvkbs x1eb86dx')]//span[contains(@class, 'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu')]")
                    last_sending_status = sending_status_elements[-1]                    
                    if last_sending_status.text in ["không thể", "unable", "can not", "can't"]:
                        self.status_updated.emit(self.window.translate("PostingThread_failed_to_send_message", user_name=user_name, user_id=user_id))
                        failed_urls.append(url)
                        failed_times += 1
                        continue
                        
                    # Chờ cho nút gửi biến mất
                    WebDriverWait(driver, 60).until(
                        EC.invisibility_of_element_located((By.XPATH, r"//span[contains(@class, 'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5')]//div[@role='button' and @tabindex='0' and contains(@aria-label, 'Enter') and contains(@class, 'x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1')]"))
                    )
                    
                    try:
                        #Chờ gửi tin nhắn thành công và nút gửi tin nhắn biến mất
                        WebDriverWait(driver, 60).until(
                            EC.invisibility_of_element_located((By.XPATH, r"//span[contains(@class, 'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5')]//div[@role='button' and @tabindex='0' and contains(@aria-label, 'Enter') and contains(@class, 'x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1')]"))
                        )
                    except TimeoutException:
                        self.status_updated.emit(self.window.translate("PostingThread_send_button_not_disappear", user_name=user_name, user_id=user_id))
                        failed_urls.append(url)
                        continue
                        
                    time.sleep(3)
                    self.status_updated.emit(self.window.translate("PostingThread_send_successful", user_name=user_name, user_id=user_id))

                    # Xóa URL khỏi url_items_list và lưu settings
                    self.window.remove_url_from_list(url)
                    self.window.save_settings()

                    # Lưu user_id vào tệp CSV
                    self.save_sent_id(user_id)
                    self.status_updated.emit(self.window.translate("PostingThread_saved_id_to_file", user_id=user_id))

                time.sleep(5)
            except Exception as e:
                self.status_updated.emit(self.window.translate("PostingThread_failed_to_post_location", url=url, e=str(e)))
                failed_urls.append(url)

        # self.window.stop_posting()  # Dừng đăng bài
        self.stop_requested.emit()
        
        if failed_urls:
            self.status_updated.emit(self.window.translate("PostingThread_all_locations_posted_fail"))
            for failed_url in failed_urls:
                self.status_updated.emit(f"- {failed_url}")
        else:
            self.status_updated.emit(self.window.translate("PostingThread_all_locations_posted_successful"))
        return

    def post_marketplace_item(self, driver, url):
        driver.get(url)
        time.sleep(5)
        if 'additional_profile/dialog/marketplace_mitigation' in driver.current_url():
            try:
                switch_primary_account_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@aria-label and @role='button' and @tabindex='0']//div[@role='none' and contains(@class, 'x9f619 x1n2onr6 x1ja2u2z x193iq5w xeuugli x6s0dn4 x78zum5')]//span[contains(@class, 'x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv') and @dir='auto']"))
                )
                switch_primary_account_button.click()
                self.status_updated.emit(self.window.translate("PostingThread_switched_to_primary_account"))
                time.sleep(5)
                driver.get(url)
            except Exception as e:
                self.status_updated.emit(self.window.translate("PostingThread_error_while_pressing_button",e=str(e)))
        title_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='What are you selling?']"))
        )
        title_box.send_keys(content[:50])
        price_box = driver.find_element(By.XPATH, "//input[@placeholder='Price']")
        price_box.send_keys("0")
        if image_folder:
            self.upload_images(driver, image_folder)
        publish_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Publish')]"))
        )
        publish_button.click()
        # Thêm logic đăng bài Marketplace ở đây
        # Hiện tại chỉ đăng 1 bài nhưng có thể mở rộng bằng vòng lặp

class UpdateChecker(QThread):
    update_status = pyqtSignal(str)

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.current_version = version

    def run(self):
        try:
            response = requests.get("https://api.github.com/repos/tekdt/AutoPostFacebookGroupSimple/releases/latest")
            latest_version = response.json()["name"].lstrip("v")
            if latest_version > self.current_version:
                self.update_status.emit(self.window.translate("UpdateChecker_new_version", latest_version=latest_version))
            else:
                self.update_status.emit(self.window.translate("UpdateChecker_last_version"))
        except Exception as e:
            self.update_status.emit(self.window.translate("UpdateChecker_error_checking", e=str(e)))

class MainWindow(QMainWindow):
    ai_servers = {
        "Groq": ["distil-whisper-large-v3-en", "gemma2-9b-it", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-70b-8192", "llama3-8b-8192", "whisper-large-v3", "whisper-large-v3-turbo", "playai-tts", "playai-tts-arabic", "qwen-qwq-32b", "mistral-saba-24b", "qwen-2.5-coder-32b", "qwen-2.5-32b", "deepseek-r1-distill-qwen-32b", "deepseek-r1-distill-llama-70b", "llama-3.3-70b-specdec", "llama-3.2-1b-preview", "llama-3.2-3b-preview", "llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview"],
        "ChatGPT": ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4", "gpt-4o-mini", "gpt-4o", "o3-mini"],
        "Gemini": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"],
        "Mistral": ["mistral-large-latest", "pixtral-large-latest", "mistral-moderation-latest", "ministral-3b-latest", "ministral-8b-latest", "open-mistral-nemo", "mistral-small-latest", "mistral-saba-latest", "codestral-latest"],
        "DeepSeek": ["deepseek-chat", "deepseek-reasoner"]
    }
    
    def __init__(self):
        super().__init__()
        self.driver = None
        self.setWindowTitle("Auto Post Facebook Simple")
        self.setGeometry(100, 100, 600, 800)

        self.settings = {}
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab Facebook
        self.facebook_tab = QWidget()
        self.tabs.addTab(self.facebook_tab, "Facebook")
        self.setup_facebook_tab()
        self.location_combo.currentTextChanged.connect(self.update_url_list)

        # Tab Tạo nội dung tự động
        self.ai_tab = QWidget()
        self.tabs.addTab(self.ai_tab, "Tạo nội dung tự động")
        self.setup_ai_tab()

        # Tab Cài đặt
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Cài đặt")
        self.setup_settings_tab()

        # Tab Thông tin phần mềm
        self.info_tab = QWidget()
        self.tabs.addTab(self.info_tab, "Thông tin phần mềm")
        self.setup_info_tab()

        self.is_initializing = True
        self.load_settings()
        # self.toggle_auto_fetch_groups(self.location_combo.currentText())
        self.is_initializing = False
        self.driver_ready = False
    
    def init_driver(self):
        self.chrome_driver_thread = ChromeDriverThread(self)
        self.chrome_driver_thread.driver_ready.connect(self.set_driver)
        self.chrome_driver_thread.start()

    def set_driver(self, driver):
        self.driver = driver
        self.driver_ready = True
        # Khởi động ChromeMonitorThread
        self.chrome_monitor = ChromeMonitorThread()
        self.chrome_monitor.chrome_closed.connect(self.handle_chrome_closed)
        self.chrome_monitor.start()
        # Sau khi driver sẵn sàng, bắt đầu đăng nhập
        self.start_login()

    def handle_chrome_closed(self):
        QMessageBox.warning(self, self.translate("waning_title"), self.translate("MainWindow_chrome_has_stopped"))
        self.update_status(self.translate("MainWindow_chrome_has_stopped"))
        self.stop_posting()
        # self.driver = None
        # self.init_driver()

    def start_login(self):
        self.login_thread = LoginThread(self)
        self.login_thread.login_success.connect(self.on_login_success)
        self.login_thread.status_updated.connect(self.update_status)
        self.login_thread.start()

    def on_login_success(self):
        if self.driver is None:
            self.update_status(self.translate("LoginThread_driver_is_not_initialized"))
            return
        location = self.location_combo.currentText()
        if location == self.translate("group_location_position_option") and self.auto_fetch_check.isChecked():
            self.start_fetching_data('groups')
        elif (location == self.translate("members_location_position_option")) and self.url_items_list.count() == 0:
            group_url = self.url_entry.text().strip()
            if group_url:
                self.start_fetching_data('members', group_url)
        else:
            self.start_posting_process()
        
    def update_content_preview(self, content):
        self.content_preview.setPlainText(content)

    def setup_facebook_tab(self):
        layout = QVBoxLayout()

        # Login frame
        login_frame = QWidget()
        login_layout = QGridLayout()
        login_frame.setLayout(login_layout)

        email_label = QLabel("Email:")
        email_label.setObjectName("email_label")  # Đặt tên cho QLabel
        self.email_entry = QLineEdit()
        login_layout.addWidget(email_label, 0, 0)
        login_layout.addWidget(self.email_entry, 0, 1)

        password_label = QLabel("Mật khẩu:")
        password_label.setObjectName("password_label")  # Đặt tên cho QLabel
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        login_layout.addWidget(password_label, 1, 0)
        login_layout.addWidget(self.password_entry, 1, 1)

        self.profile_check = QCheckBox("Sử dụng profile Chrome hiện tại")
        self.profile_check.setObjectName("profile_check")  # Đặt tên cho QCheckBox
        login_layout.addWidget(self.profile_check, 2, 0, 1, 2)

        self.sub_account_check = QCheckBox("Sử dụng Facebook phụ")
        self.sub_account_check.setObjectName("sub_account_check")  # Đặt tên cho QCheckBox
        self.sub_account_entry = QLineEdit()
        self.sub_account_entry.setEnabled(False)
        self.sub_account_check.stateChanged.connect(self.toggle_sub_account_entry)
        login_layout.addWidget(self.sub_account_check, 3, 0)
        login_layout.addWidget(self.sub_account_entry, 3, 1)
        
        self.headless_check = QCheckBox("Chạy Chrome ở chế độ ẩn (headless)")
        self.headless_check.setObjectName("headless_check")  # Đặt tên cho QCheckBox
        login_layout.addWidget(self.headless_check, 4, 0, 1, 2)

        layout.addWidget(login_frame)

        # Location frame
        location_frame = QWidget()
        location_layout = QVBoxLayout()
        location_frame.setLayout(location_layout)

        location_label = QLabel("Đăng lên:")
        location_label.setObjectName("location_label")  # Đặt tên cho QLabel
        self.location_combo = QComboBox()
        self.location_combo.addItems(["Nhóm", "Marketplace", "Trang", "Gửi tin nhắn tới thành viên nhóm"])
        self.location_combo.currentTextChanged.connect(self.toggle_auto_fetch_groups)
        location_layout.addWidget(location_label)
        location_layout.addWidget(self.location_combo)

        layout.addWidget(location_frame)

        # Thêm phần loại bài niêm yết và mã hóa tin nhắn
        self.additional_location_frame = QWidget()
        self.additional_location_layout = QVBoxLayout()
        self.additional_location_frame.setLayout(self.additional_location_layout)
        
        self.listing_type_label = QLabel("Loại bài niêm yết:")
        self.listing_type_label.setObjectName("listing_type_label")  # Đặt tên cho QLabel
        self.listing_type_combo = QComboBox()
        self.listing_type_combo.addItems(["Item", "Vehicle", "Rental"])
        self.additional_location_layout.addWidget(self.listing_type_label)
        self.additional_location_layout.addWidget(self.listing_type_combo)
        
        self.encrypt_message_code_label = QLabel("Mã 6 số mã hoá tin nhắn đầu cuối:")
        self.encrypt_message_code_label.setObjectName("encrypt_code_label")  # Đặt tên cho QLabel
        self.encrypt_message_code_input = QLineEdit()
        self.additional_location_layout.addWidget(self.encrypt_message_code_label)
        self.additional_location_layout.addWidget(self.encrypt_message_code_input)
        
        layout.addWidget(self.additional_location_frame)

        # Image frame
        self.image_frame = QWidget()
        self.image_layout = QVBoxLayout()
        self.image_frame.setLayout(self.image_layout)

        self.image_folder_label = QLabel("Chọn thư mục chứa hình ảnh:")
        self.image_folder_label.setObjectName("image_folder_label")  # Đặt tên cho QLabel
        self.image_folder_entry = QLineEdit()
        self.image_layout.addWidget(self.image_folder_label)
        self.image_layout.addWidget(self.image_folder_entry)

        self.select_image_button = QPushButton("Chọn thư mục")
        self.select_image_button.setObjectName("select_image_button")  # Đặt tên cho QPushButton
        self.select_image_button.clicked.connect(self.select_image_folder)
        self.image_layout.addWidget(self.select_image_button)
        
        self.random_image_check = QCheckBox("Lấy hình ảnh ngẫu nhiên")
        self.random_image_check.setObjectName("random_image_check")  # Đặt tên cho QCheckBox
        self.image_layout.addWidget(self.random_image_check)
        
        self.auto_fetch_check = QCheckBox("Tự động lấy danh sách nhóm")
        self.auto_fetch_check.setObjectName("auto_fetch_check")  # Đặt tên cho QCheckBox
        self.auto_fetch_check.setVisible(False)
        self.auto_fetch_check.stateChanged.connect(self.toggle_url_frame)
        self.image_layout.addWidget(self.auto_fetch_check)

        layout.addWidget(self.image_frame)

        # URL frame
        self.url_frame = QWidget()
        url_layout = QVBoxLayout()
        self.url_frame.setLayout(url_layout)

        url_label = QLabel("Nhập URL:")
        url_label.setObjectName("url_label")  # Đặt tên cho QLabel
        self.url_entry = QLineEdit()
        self.add_button = QPushButton("Thêm")
        self.add_button.setObjectName("add_button")  # Đặt tên cho QPushButton
        self.add_button.clicked.connect(self.add_url)
        url_input_layout = QHBoxLayout()
        url_input_layout.addWidget(url_label)
        url_input_layout.addWidget(self.url_entry)
        url_input_layout.addWidget(self.add_button)
        url_layout.addLayout(url_input_layout)

        self.import_button = QPushButton("Nhập từ file")
        self.import_button.setObjectName("import_button")  # Đặt tên cho QPushButton
        self.import_button.clicked.connect(self.import_urls_from_file)
        self.remove_button = QPushButton("Xóa URL đã chọn")
        self.remove_button.setObjectName("remove_button")  # Đặt tên cho QPushButton
        self.remove_button.clicked.connect(self.delete_selected_url)
        url_buttons_layout = QHBoxLayout()
        url_buttons_layout.addWidget(self.import_button)
        url_buttons_layout.addWidget(self.remove_button)
        url_layout.addLayout(url_buttons_layout)

        self.url_items_list = QListWidget()
        url_layout.addWidget(self.url_items_list)

        layout.addWidget(self.url_frame)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Bắt đầu đăng")
        self.start_button.setObjectName("start_button")  # Đặt tên cho QPushButton
        self.start_button.clicked.connect(self.start_posting)
        self.stop_button = QPushButton("Dừng đăng bài")
        self.stop_button.setObjectName("stop_button")  # Đặt tên cho QPushButton
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_posting)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        layout.addLayout(buttons_layout)

        # Status
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        self.facebook_tab.setLayout(layout)

    def setup_ai_tab(self):
        layout = QVBoxLayout()

        api_key_label = QLabel("API Key:")
        api_key_label.setObjectName("api_key_label")  # Đặt tên cho QLabel
        self.api_key_entry = QLineEdit()
        self.api_key_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_entry)
        
        server_label = QLabel("Máy chủ AI:")
        server_label.setObjectName("server_label")  # Đặt tên cho QLabel
        self.server_combo = QComboBox()
        self.server_combo.addItems(self.ai_servers.keys())
        self.server_combo.currentTextChanged.connect(self.update_model_combo)
        layout.addWidget(server_label)
        layout.addWidget(self.server_combo)
        
        model_label = QLabel("Mô hình AI:")
        model_label.setObjectName("model_label")  # Đặt tên cho QLabel
        self.model_combo = QComboBox()
        layout.addWidget(model_label)
        layout.addWidget(self.model_combo)

        prompt_label = QLabel("Nhập prompt cho bài đăng:")
        prompt_label.setObjectName("prompt_label")  # Đặt tên cho QLabel
        self.prompt_entry = QTextEdit()
        layout.addWidget(prompt_label)
        layout.addWidget(self.prompt_entry)
        
        self.generate_button = QPushButton("Tạo nội dung")
        self.generate_button.setObjectName("generate_button")  # Đặt tên cho QPushButton
        self.generate_button.clicked.connect(self.generate_content_preview)
        layout.addWidget(self.generate_button)
        
        self.auto_generate_check = QCheckBox("Tự động tạo nội dung cho mỗi bài đăng")
        self.auto_generate_check.setObjectName("auto_generate_check")  # Đặt tên cho QCheckBox
        layout.addWidget(self.auto_generate_check)

        self.content_preview = QTextEdit()
        self.content_preview.setReadOnly(True)
        layout.addWidget(self.content_preview)

        self.ai_tab.setLayout(layout)
        self.update_model_combo(self.server_combo.currentText())

    def setup_settings_tab(self):
        layout = QVBoxLayout()

        # Group Ngôn ngữ
        self.language_group = QGroupBox("Ngôn ngữ")
        language_layout = QHBoxLayout()
        language_label = QLabel("Chọn ngôn ngữ:")
        language_label.setObjectName("language_label")  # Đặt tên cho QLabel
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Tiếng Việt", "English"])
        self.language_combo.currentTextChanged.connect(self.change_language)
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        self.language_group.setLayout(language_layout)
        layout.addWidget(self.language_group)

        # Group Cập nhật
        self.update_group = QGroupBox("Cập nhật")
        update_layout = QVBoxLayout()
        self.update_button = QPushButton("Kiểm tra cập nhật")
        self.update_button.setObjectName("update_button")  # Đặt tên cho QPushButton
        self.update_button.clicked.connect(self.check_for_updates)
        self.update_status_label = QLabel("Chưa kiểm tra cập nhật.")
        self.update_status_label.setObjectName("update_status_label")  # Đặt tên cho QLabel
        update_layout.addWidget(self.update_button)
        update_layout.addWidget(self.update_status_label)
        self.update_group.setLayout(update_layout)
        layout.addWidget(self.update_group)

        self.settings_tab.setLayout(layout)
    
    def setup_image_tab(self):
        layout = QVBoxLayout()

        image_folder_label = QLabel("Chọn thư mục chứa hình ảnh:")
        self.image_folder_entry = QLineEdit()
        layout.addWidget(image_folder_label)
        layout.addWidget(self.image_folder_entry)

        select_image_button = QPushButton("Chọn thư mục")
        select_image_button.clicked.connect(self.select_image_folder)
        layout.addWidget(select_image_button)

        self.image_tab.setLayout(layout)

    def setup_info_tab(self):
        layout = QVBoxLayout()

        info_label = QLabel("Thông tin phần mềm")
        info_label.setObjectName("info_label")  # Đặt tên cho QLabel
        info_label.setStyleSheet("font-size: 16pt;")
        layout.addWidget(info_label)

        software_info = f"""
Tên phần mềm: Auto Post Facebook Simple
Tác giả: TekDT
Email: dinhtrungtek@gmail.com
Telegram: @tekdt1152
Zalo: 0944.095.092
Mô tả: Phần mềm tự động đăng bài lên Facebook với nội dung tạo tự động bằng AI
Phiên bản: {version}
Ngày phát hành: {released_date}

Software: Auto Post Facebook Simple
Author: TekDT
Email: dinhtrungtek@gmail.com
Telegram: @tekdt1152
Zalo: 0944.095.092
Description: Software to automatically post to Facebook with content automatically generated by AI
Version: {version}
Released date: {released_date}
"""
        info_text = QTextEdit()
        info_text.setPlainText(software_info)
        info_text.setReadOnly(True)
        layout.addWidget(info_text)

        self.info_tab.setLayout(layout)

    def save_settings(self):
        settings = {
            "email": self.email_entry.text(),
            "password": self.password_entry.text(),
            "use_profile": self.profile_check.isChecked(),
            "api_key": self.api_key_entry.text(),
            "url_entry": self.url_entry.text(),
            "listing_type": self.listing_type_combo.currentText(),
            "groups": [self.url_items_list.item(i).text() for i in range(self.url_items_list.count())] if self.location_combo.currentText() == self.translate("group_location_position_option") else self.settings.get("groups", []),
            "members": [self.url_items_list.item(i).text() for i in range(self.url_items_list.count())] if self.location_combo.currentText() == self.translate("members_location_position_option") else self.settings.get("members", []),
            "pages": [self.url_items_list.item(i).text() for i in range(self.url_items_list.count())] if self.location_combo.currentText() == self.translate("pages_location_position_option") else self.settings.get("pages", []),
            "prompt": self.prompt_entry.toPlainText().strip(),
            "image_folder": self.image_folder_entry.text().strip(),
            "post_location": self.location_combo.currentText(),
            "message_code": self.encrypt_message_code_input.text(),
            "auto_fetch_groups": self.auto_fetch_check.isChecked(),
            "use_sub_account": self.sub_account_check.isChecked(),
            "headless_mode": self.headless_check.isChecked(),
            "sub_account_name": self.sub_account_entry.text(),
            "random_image": self.random_image_check.isChecked(),
            "ai_server": self.server_combo.currentText(),
            "ai_model": self.model_combo.currentText(),
            "auto_generate_content": self.auto_generate_check.isChecked(),
            "selected_language": self.language_combo.currentText()
        }
        with open("settings.json", "w", encoding="utf-8") as file:
            json.dump(settings, file, indent=4)

    def remove_url_from_list(self, url):
        """Xóa URL khỏi danh sách url_items_list."""
        for i in range(self.url_items_list.count()):
            if self.url_items_list.item(i).text() == url:
                self.url_items_list.takeItem(i)
                break
    
    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r", encoding="utf-8") as file:
                settings = json.load(file)
                self.email_entry.setText(settings.get("email", ""))
                self.password_entry.setText(settings.get("password", ""))
                self.profile_check.setChecked(settings.get("use_profile", False))
                self.headless_check.setChecked(settings.get("headless_mode", False))
                self.api_key_entry.setText(settings.get("api_key", ""))
                self.url_entry.setText(settings.get("url_entry", ""))
                self.listing_type_combo.setCurrentText(settings.get("listing_type", "Item"))
                self.prompt_entry.setPlainText(settings.get("prompt", ""))
                self.image_folder_entry.setText(settings.get("image_folder", ""))
                self.location_combo.setCurrentText(settings.get("post_location", "Nhóm"))
                self.encrypt_message_code_input.setText(settings.get("message_code", ""))
                self.settings["groups"] = settings.get("groups", [])
                self.settings["members"] = settings.get("members", [])
                self.settings["pages"] = settings.get("pages", [])
                self.language_combo.setCurrentText(settings.get("selected_language", "Tiếng Việt"))  # Tải ngôn ngữ đã chọn
                self.change_language(self.language_combo.currentText())
                
                location = self.location_combo.currentText()
                self.toggle_auto_fetch_groups(location)
                self.update_url_list(location)
                if self.url_items_list.count() > 0:
                    self.auto_fetch_check.setChecked(False)
                    self.toggle_url_frame(Qt.CheckState.Unchecked.value)
                else:
                    self.auto_fetch_check.setChecked(settings.get("auto_fetch_groups", False))

                
                self.headless_check.setChecked(settings.get("headless_check", False))
                self.sub_account_check.setChecked(settings.get("use_sub_account", False))
                self.sub_account_entry.setText(settings.get("sub_account_name", ""))
                self.random_image_check.setChecked(settings.get("random_image", False))
                self.server_combo.setCurrentText(settings.get("ai_server", "Groq"))
                self.model_combo.setCurrentText(settings.get("ai_model", "default_model"))
                self.auto_generate_check.setChecked(settings.get("auto_generate_content", False))
                self.language_combo.setCurrentText(settings.get("selected_language", "Tiếng Việt"))

    def closeEvent(self, event):
        self.stop_posting()  # Dừng Selenium nếu có
        # Chờ các luồng dừng từ luồng chính
        threads = ['login_thread', 'fetch_data_thread', 'posting_thread', 'chrome_monitor']
        for thread in threads:
            if hasattr(self, thread):
                thread_obj = getattr(self, thread)
                if thread_obj.isRunning():
                    thread_obj.quit()
                    # if not thread_obj.wait(2000):  # Chờ tối đa 2 giây
                        # thread_obj.terminate()  # Buộc dừng nếu không phản hồi
                        # self.update_status(self.translate("MainWindow_forced_close", thread=thread))
                    
        
        # Đóng Chrome Driver nếu tồn tại
        if self.driver is not None:
            try:
                self.driver.quit()
                self.update_status(self.translate("MainWindow_closed_chrome_driver"))
            except Exception as e:
                self.update_status(self.translate("MainWindow_error_closing_chrome_driver", e=str(e)))
            self.driver = None
            self.driver_ready = False
        
        self.kill_chrome_processes()
        self.save_settings()  # Lưu dữ liệu nếu cần
        event.accept()

    def kill_chrome_processes(self):
        """Giết các quy trình Chrome và chromedriver còn sót lại."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower() or 'chromedriver' in proc.info['name'].lower():
                    proc.kill()
                    process_name = proc.info['name']
                    process_pid = proc.info['pid']
                    self.update_status(self.translate("MainWindow_kill_chrome_processes", process_name=process_name, process_pid=process_pid))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    def start_posting(self):
        location = self.location_combo.currentText()
        
        # Kiểm tra "Trang" và "Marketplace"
        if location in [self.translate("pages_location_position_option"), "Marketplace"]:
            QMessageBox.warning(self, self.translate("error_title"), self.translate("MainWindow_not_supported_location", location=location))
            return
            
        sub_account_name = self.sub_account_entry.text().strip()
        if not sub_account_name and self.sub_account_check.isChecked():
            self.update_status(self.translate("MainWindow_not_allow_empty_sub_account"))
            return
        
        # Kiểm tra "Nhóm"
        if location == self.translate("group_location_position_option"):
            if not self.auto_fetch_check.isChecked():
                if self.url_items_list.count() == 0:
                    QMessageBox.warning(self, self.translate("error_title"), self.translate("MainWindow_url_list_is_empty"))
                    return
        
        # Kiểm tra "Gửi tin nhắn tới thành viên nhóm"
        elif location == self.translate("members_location_position_option"):
            if self.url_items_list.count() == 0:
                group_url = self.url_entry.text().strip()
                if not group_url or not self.is_valid_url_for_location(group_url, self.translate("group_location_position_option")):
                    QMessageBox.warning(self, self.translate("error_title"), self.translate("MainWindow_url_is_invalid"))
                    return
        
        stop_event.clear()
        # Vô hiệu hóa tất cả control và kích hoạt nút "Dừng"
        self.disable_all_controls()
        
        # Nếu tất cả kiểm tra đều qua, khởi động driver
        if self.driver is None:
            self.init_driver()
        else:
            self.start_login()
        
    def start_fetching_data(self, data_type, url=None):
        if not self.driver_ready or self.driver is None:
            self.update_status(self.translate("LoginThread_driver_is_not_initialized"))
            return
        stop_event.clear()
        self.fetch_data_thread = FetchDataThread(self, data_type, url)
        self.fetch_data_thread.fetch_completed.connect(self.start_posting_process)
        self.fetch_data_thread.fetch_failed.connect(self.show_fetch_error)
        self.fetch_data_thread.status_updated.connect(self.update_status)
        self.fetch_data_thread.start()
    
    def show_fetch_error(self, message):
        QMessageBox.warning(self, self.translate("error_title"), message)
    
    def start_posting_process(self):
        location = self.location_combo.currentText()
        urls = [self.url_items_list.item(i).text() for i in range(self.url_items_list.count())]
        valid_urls = [url for url in urls if self.is_valid_url_for_location(url, location)]

        if not valid_urls:
            self.update_status(self.translate("MainWindow_url_list_is_empty"))
            return

        stop_event.clear()
        self.posting_thread = PostingThread(self, location, valid_urls)
        self.posting_thread.status_updated.connect(self.update_status)
        self.posting_thread.content_updated.connect(self.update_content_preview)
        self.posting_thread.stop_requested.connect(self.stop_posting)
        self.posting_thread.finished.connect(self.reset_buttons)
        self.posting_thread.start()
    
    def reset_buttons(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def stop_posting(self):
        stop_event.set()
        threads = ['login_thread', 'fetch_data_thread', 'posting_thread', 'chrome_monitor']
    
        # Chờ các luồng dừng với timeout
        for thread in threads:
            if hasattr(self, thread):
                thread_obj = getattr(self, thread)
                if thread_obj.isRunning():
                    thread_obj.quit()  # Yêu cầu dừng luồng
                    # if not thread_obj.wait(2000):  # Chờ tối đa 2 giây
                        # thread_obj.terminate()
        
        # Lưu dữ liệu nếu đang fetch
        if hasattr(self, 'fetch_data_thread') and self.fetch_data_thread.isRunning():
            items = self.fetch_data_thread.items
            if items:
                self.url_items_list.clear()
                for item in items:
                    self.url_items_list.addItem(item)
                if self.location_combo.currentText() == self.translate("group_location_position_option"):
                    self.settings["groups"] = items
                elif self.location_combo.currentText() == self.translate("members_location_position_option"):
                    self.settings["members"] = items
                count_items = len(items)
                self.save_settings()
                self.update_status(self.translate("MainWindow_saved_to_settings"))
        
        if self.driver is not None:
            try:
                self.driver.quit()
                self.update_status(self.translate("MainWindow_stop_selenium_and_browser"))
            except Exception as e:
                self.update_status(self.translate("MainWindow_error_while_closing_driver", e=str(e)))
            self.driver = None
            self.driver_ready = False
            
        # Kích hoạt lại tất cả control và vô hiệu hóa nút "Dừng"
        self.enable_all_controls()
        
        # Thêm điều kiện để bỏ tick "Tự động lấy danh sách nhóm" nếu url_items_list có link và checkbox được tick
        if self.url_items_list.count() > 0:
            self.auto_fetch_check.setChecked(False)
            self.toggle_url_frame(Qt.CheckState.Unchecked.value)  # Hiển thị khung danh sách URL
        
        self.update_status(self.translate("MainWindow_stop_posting"))

    def add_url(self):
        url = self.url_entry.text().strip()
        location = self.location_combo.currentText()
        
        # Kiểm tra URL theo từng loại địa điểm
        validation_patterns = {
            "Nhóm": r'^https?://(www\.|m\.)?facebook\.com/groups/[\w-]+',
            "Trang": r'^https?://(www\.|m\.)?facebook\.com/[\w.]+',
            "Gửi tin nhắn tới thành viên nhóm": r'^https?://(www\.|m\.)?facebook\.com/(messages/t/|groups/)'
        }
        
        if location in validation_patterns and not re.match(validation_patterns[location], url):
            QMessageBox.warning(self, self.translate("error_title"), self.translate("MainWindow_invalid_url_for_location", location=location))
            return
            
        self.url_items_list.addItem(url)
        self.url_entry.clear()
        self.save_settings()
        
        
    def is_valid_url_for_location(self, url, location):
        if location == self.translate("group_location_position_option") or location == "groups":
            return re.match(r'^https?://(www\.|m\.)?facebook\.com/groups/[\w-]+', url)
        elif location == self.translate("pages_location_position_option") or location == "pages":
            return re.match(r'^https?://(www\.|m\.)?facebook\.com/[\w.]+', url)
        elif location == self.translate("members_location_position_option") or location == "members":
            return re.match(r'^https?://(www\.|m\.)?facebook\.com/(groups/[\w.-]+|messages/t/[\w.-]+)', url)
        elif location == "Marketplace":
            return True
        return False

    def delete_selected_url(self):
        selected_items = self.url_items_list.selectedItems()
        for item in selected_items:
            self.url_items_list.takeItem(self.url_items_list.row(item))
        self.save_settings()

    def import_urls_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.translate("MainWindow_choose_file"), "", "CSV Files (*.csv);;Text Files (*.txt)")
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.url_items_list.clear()
                for line in file:
                    url = line.strip()
                    if url and is_valid_facebook_url(url):
                        self.url_items_list.addItem(url)
                    else:
                        self.update_status(self.translate("MainWindow_skipped_invalid_url", url=url))
        self.save_settings()

    def select_image_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.translate("MainWindow_choose_image_folder"))
        if folder_path:
            self.image_folder_entry.setText(folder_path)

    def update_status(self, message):
        self.status_text.append(message)

    def toggle_sub_account_entry(self, state):
        self.sub_account_entry.setEnabled(state == Qt.CheckState.Checked.value)

    def toggle_auto_fetch_groups(self, text):
        if text == "Marketplace":
            self.auto_fetch_check.setVisible(False)
            self.url_frame.setVisible(False)
            self.listing_type_label.setVisible(True)
            self.listing_type_combo.setVisible(True)
            self.encrypt_message_code_label.setVisible(False)
            self.encrypt_message_code_input.setVisible(False)
        elif text == self.translate("group_location_position_option"):
            self.additional_location_frame.hide()
            self.auto_fetch_check.setVisible(True)
            self.url_frame.setVisible(not self.auto_fetch_check.isChecked())
            # Reset danh sách nhóm khi chuyển chế độ
            if not self.auto_fetch_check.isChecked() and not self.is_initializing:
                self.url_frame.setVisible(True)
            else:
                self.url_frame.setVisible(False)
        elif text in [self.translate("pages_location_position_option"), self.translate("members_location_position_option")]:
            self.auto_fetch_check.setVisible(False)
            self.auto_fetch_check.setChecked(False)
            if text == self.translate("members_location_position_option"):
                self.additional_location_frame.show()
                self.listing_type_label.setVisible(False)
                self.listing_type_combo.setVisible(False)
                self.encrypt_message_code_label.setVisible(True)
                self.encrypt_message_code_input.setVisible(True)
            else:                
                self.additional_location_frame.hide()
            self.url_entry.setVisible(True)
            self.url_frame.setVisible(True)
            if not self.is_initializing:
                self.url_items_list.clear()

        # Điều chỉnh các thành phần con
        show_add_buttons = text == self.translate("group_location_position_option") and not self.auto_fetch_check.isChecked()
        for btn in [self.translate("add_button"), self.translate("import_button"), self.translate("remove_button")]:
            widget = self.findChild(QPushButton, btn)
            if widget:
                widget.setVisible(show_add_buttons)

        # Ẩn toàn bộ danh sách URL cho Trang và Tin nhắn
        self.url_items_list.setVisible(text in [self.translate("group_location_position_option"), "Marketplace"])
    
    def toggle_url_frame(self, state):
        visible = state != Qt.CheckState.Checked.value
        self.url_frame.setVisible(visible)
        
        # Ẩn/hiện các thành phần con trong url_frame
        for widget in [
            self.url_entry, 
            self.url_items_list, 
            self.findChild(QPushButton, self.translate("add_button")),
            self.findChild(QPushButton, self.translate("import_button")),
            self.findChild(QPushButton, self.translate("remove_button"))
        ]:
            if widget:
                widget.setVisible(visible)
        
    def update_model_combo(self, server):
        self.model_combo.clear()
        self.model_combo.addItems(self.ai_servers.get(server, []))
        
    def generate_content_preview(self):
        server = self.server_combo.currentText()
        model = self.model_combo.currentText()
        prompt = self.prompt_entry.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, self.translate("error_title"), self.translate("MainWindow_please_input_prompt"))
            return
        self.generate_button.setText(self.translate("MainWindow_generating_content"))
        self.generate_button.setEnabled(False)
        try:
            content = self.generate_content_ai(server, model, prompt)
            self.content_preview.setText(content)
        except Exception as e:
            QMessageBox.warning(self, self.translate("error_title"), self.translate("MainWindow_can_not_generate_content", e=str(e)))
        self.generate_button.setText(self.translate("generate_button"))
        self.generate_button.setEnabled(True)
            
    def generate_content_ai(self, server, model, prompt):
        api_key = self.api_key_entry.text().strip()
        if not api_key:
            raise ValueError(self.translate("MainWindow_api_is_empty"))

        try:
            if server == "Groq":
                os.environ['GROQ_API_KEY'] = api_key
                client = groq.Client(api_key=api_key)
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    temperature=0.8,
                    top_p=0.9
                )
                content = chat_completion.choices[0].message.content

            elif server == "Gemini":
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model)
                response = model.generate_content(prompt)
                content = response.text

            elif server == "DeepSeek":
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=False
                )
                content = response.choices[0].message.content

            elif server == "Mistral":
                client = Mistral(api_key=api_key)
                response = client.chat.complete(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.choices[0].message.content

            elif server == "ChatGPT":
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.choices[0].message.content

            else:
                raise ValueError(self.translate("MainWindow_server_is_not_supported", server=server))

        except Exception as e:
            raise ValueError(self.translate("MainWindow_error_while_calling_api", server=server, e=str(e)))

        md5_hash = self.calculate_md5(content)
        if not self.is_content_exists(md5_hash):
            self.save_content_to_json(content, md5_hash)

        return content
    
    def update_url_list(self, location):
        self.url_items_list.clear()  # Xóa danh sách hiện tại
        if location in key_map:
            items = self.settings.get(key_map[location], [])  # Lấy danh sách từ settings
            for item in items:
                self.url_items_list.addItem(item)  # Thêm từng mục vào url_items_list
            if self.url_items_list.count() > 0:
                self.auto_fetch_check.setChecked(False)
                self.toggle_url_frame(Qt.CheckState.Unchecked.value)
            else:
                self.auto_fetch_check.setChecked(self.settings.get("auto_fetch_groups", False))
                
            count_items = len(items)
            self.update_status(self.translate("update_status_load_items_from_settings", count_items = count_items, location=location))
  
    def calculate_md5(self, content):
        return hashlib.md5(content.encode('utf-8')).hexdigest()
        
    def is_content_exists(self, md5_hash):
        """Kiểm tra xem mã MD5 đã tồn tại trong file JSON chưa."""
        if os.path.exists("posted_contents.json"):
            with open("posted_contents.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                return any(item["md5"] == md5_hash for item in data)
        return False

    def save_content_to_json(self, content, md5_hash):
        """Lưu nội dung và mã MD5 vào file JSON."""
        data = []
        if os.path.exists("posted_contents.json"):
            with open("posted_contents.json", "r", encoding="utf-8") as file:
                data = json.load(file)
        data.append({"content": content, "md5": md5_hash})
        with open("posted_contents.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
            
    def get_random_content_from_json(self):
        """Lấy một nội dung ngẫu nhiên từ file JSON, với điều kiện cho tin nhắn."""
        if os.path.exists("posted_contents.json"):
            with open("posted_contents.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                if data:
                    location = self.location_combo.currentText()
                    if location == self.translate("members_location_position_option"):
                        # Lọc các nội dung không chứa ký tự xuống dòng
                        filtered_data = [item for item in data if '\n' not in item["content"]]
                        if filtered_data:
                            return random.choice(filtered_data)["content"]
                        else:
                            return None  # Hoặc trả về một giá trị mặc định
                    else:
                        # Trường hợp không phải gửi tin nhắn, lấy ngẫu nhiên từ toàn bộ dữ liệu
                        return random.choice(data)["content"]
        return None  # Trả về None nếu file không tồn tại hoặc không có dữ liệu

    def get_all_controls(self):
        controls = []
        # Tab Facebook
        controls.extend([
            self.email_entry,
            self.password_entry,
            self.profile_check,
            self.sub_account_check,
            self.sub_account_entry,
            self.headless_check,
            self.location_combo,
            self.listing_type_combo,
            self.image_folder_entry,
            self.random_image_check,
            self.auto_fetch_check,
            self.url_entry,
            self.url_items_list,
            self.start_button,
            self.stop_button,
            self.import_button,
            self.add_button,
            self.remove_button,
            self.select_image_button,
            # self.findChild(QPushButton, self.translate("add_button")),
            # self.findChild(QPushButton, self.translate("import_button")),
            # self.findChild(QPushButton, self.translate("remove_button")),
        ])
        # Tab Tạo nội dung tự động
        controls.extend([
            self.api_key_entry,
            self.server_combo,
            self.model_combo,
            self.prompt_entry,
            self.generate_button,
            self.auto_generate_check,
            self.content_preview,
        ])
        # Tab Cài đặt
        controls.extend([
            self.language_combo,
            self.update_button,
        ])
        # Tab Thông tin phần mềm không có control cần quản lý
        return [control for control in controls if control is not None]  # Loại bỏ None nếu có
    
    def disable_all_controls(self):
        for control in self.get_all_controls():
            if control != self.stop_button:  # Không vô hiệu hóa nút "Dừng"
                control.setEnabled(False)
        self.stop_button.setEnabled(True)  # Kích hoạt nút "Dừng"

    def enable_all_controls(self):
        for control in self.get_all_controls():
            if control != self.stop_button:  # Không kích hoạt lại nút "Dừng"
                control.setEnabled(True)
        self.stop_button.setEnabled(False)  # Vô hiệu hóa nút "Dừng"
        
    def change_language(self, language):
        if language == "Tiếng Việt" or language == "Vietnamese":
            lang_code = "vi"
        elif language == "Tiếng Anh" or language == "English":
            lang_code = "en"
        else:
            return

        if os.path.exists(resource_path("language.json")):
            with open(resource_path("language.json"), "r", encoding="utf-8") as file:
                content = file.read().strip()
                if not content:
                    QMessageBox.warning(self, self.translate("error_title"), self.translate("language_json_file_is_empty"))
                    return
                try:
                    lang_data = json.loads(content)  # Sử dụng loads để kiểm soát
                    if lang_code in lang_data:
                        self.translate_ui(lang_data[lang_code])
                    else:
                        QMessageBox.warning(self, self.translate("error_title"), self.translate("language_not_supported"))
                except json.JSONDecodeError as e:
                    QMessageBox.warning(self, self.translate("error_title"), self.translate("change_language_error_for_language_json_contruct", e=str(e)))
                except RecursionError as e:
                    QMessageBox.warning(self, self.translate("error_title"), self.translate("change_language_error_for_recursion_depth_exceeded", e=str(e)))
        else:
            QMessageBox.warning(self, self.translate("error_title"), self.translate("language_json_file_is_not_found"))
            
    def translate_ui(self, lang_dict):
        # Cập nhật tiêu đề cửa sổ và các tab
        self.setWindowTitle(lang_dict.get("window_title", "Auto Post Facebook Simple"))
        self.tabs.setTabText(0, lang_dict.get("tab_facebook", "Facebook"))
        self.tabs.setTabText(1, lang_dict.get("tab_ai", "Tạo nội dung tự động"))
        self.tabs.setTabText(2, lang_dict.get("tab_settings", "Cài đặt"))
        self.tabs.setTabText(3, lang_dict.get("tab_info", "Thông tin phần mềm"))

        # Tab Facebook
        self.findChild(QLabel, "email_label").setText(lang_dict.get("email_label", "Email:"))
        self.findChild(QLabel, "password_label").setText(lang_dict.get("password_label", "Mật khẩu:"))
        self.findChild(QCheckBox, "profile_check").setText(lang_dict.get("profile_check", "Sử dụng profile Chrome hiện tại"))
        self.findChild(QCheckBox, "sub_account_check").setText(lang_dict.get("sub_account_check", "Sử dụng Facebook phụ"))
        self.findChild(QCheckBox, "headless_check").setText(lang_dict.get("headless_check", "Chạy Chrome ở chế độ ẩn (headless)"))
        self.findChild(QLabel, "location_label").setText(lang_dict.get("location_label", "Đăng lên:"))
        
        self.location_keys = [
            "group_location_position_option",
            "marketplace_location_position_option",
            "pages_location_position_option",
            "members_location_position_option"
        ]
        self.default_labels = ["Group", "Marketplace", "Page", "Send message to group members"]
        self.location_key_list = []
        self.location_combo.clear()
        for i, location_key in enumerate(self.location_keys):
            translation = lang_dict.get(location_key)
            if translation is not None:
                self.location_key_list.append(translation)
            else:
                if i < len(self.default_labels):
                    self.location_key_list.append(self.default_labels[i])
                else:
                    self.location_key_list.append(location_key)
        self.location_combo.addItems(self.location_key_list)
        
        self.findChild(QLabel, "listing_type_label").setText(lang_dict.get("listing_type_label", "Loại bài niêm yết:"))
        self.findChild(QLabel, "encrypt_code_label").setText(lang_dict.get("encrypt_code_label", "Mã 6 số mã hoá tin nhắn đầu cuối:"))
        self.findChild(QLabel, "image_folder_label").setText(lang_dict.get("image_folder_label", "Chọn thư mục chứa hình ảnh:"))
        self.findChild(QPushButton, "select_image_button").setText(lang_dict.get("select_image_button", "Chọn thư mục"))
        self.findChild(QCheckBox, "random_image_check").setText(lang_dict.get("random_image_check", "Lấy hình ảnh ngẫu nhiên"))
        self.findChild(QCheckBox, "auto_fetch_check").setText(lang_dict.get("auto_fetch_check", "Tự động lấy danh sách nhóm"))
        self.findChild(QLabel, "url_label").setText(lang_dict.get("url_label", "Nhập URL:"))
        self.findChild(QPushButton, "add_button").setText(lang_dict.get("add_button", "Thêm"))
        self.findChild(QPushButton, "import_button").setText(lang_dict.get("import_button", "Nhập từ file"))
        self.findChild(QPushButton, "remove_button").setText(lang_dict.get("remove_button", "Xóa URL đã chọn"))
        self.start_button.setText(lang_dict.get("start_button", "Bắt đầu đăng"))
        self.stop_button.setText(lang_dict.get("stop_button", "Dừng đăng bài"))

        # Tab Tạo nội dung tự động
        self.findChild(QLabel, "api_key_label").setText(lang_dict.get("api_key_label", "API Key:"))
        self.findChild(QLabel, "server_label").setText(lang_dict.get("server_label", "Máy chủ AI:"))
        self.findChild(QLabel, "model_label").setText(lang_dict.get("model_label", "Mô hình AI:"))
        self.findChild(QLabel, "prompt_label").setText(lang_dict.get("prompt_label", "Nhập prompt cho bài đăng:"))
        self.generate_button.setText(lang_dict.get("generate_button", "Tạo nội dung"))
        self.auto_generate_check.setText(lang_dict.get("auto_generate_check", "Tự động tạo nội dung cho mỗi bài đăng"))

        # Tab Cài đặt
        self.language_group.setTitle(lang_dict.get("language_group_label", "Ngôn ngữ"))
        self.update_group.setTitle(lang_dict.get("update_group_label", "Cập nhật"))
        self.findChild(QLabel, "language_label").setText(lang_dict.get("language_label", "Chọn ngôn ngữ:"))
        self.update_button.setText(lang_dict.get("update_button", "Kiểm tra cập nhật"))
        self.update_status_label.setText(lang_dict.get("update_status_label", "Chưa kiểm tra cập nhật."))

        # Tab Thông tin phần mềm
        self.findChild(QLabel, "info_label").setText(lang_dict.get("info_label", "Thông tin phần mềm"))
        
    def check_for_updates(self):
        self.update_button.setEnabled(False)
        self.update_status_label.setText(self.translate("MainWindow_checking_update"))
        self.update_checker = UpdateChecker(self)
        self.update_checker.update_status.connect(self.update_status_label.setText)
        self.update_checker.finished.connect(lambda: self.update_button.setEnabled(True))
        self.update_checker.start()
        
    def translate(self, key, **kwargs):
        lang_code = "vi" if self.language_combo.currentText() == "Tiếng Việt" else "en"
        if os.path.exists(resource_path("language.json")):
            with open(resource_path("language.json"), "r", encoding="utf-8") as file:
                lang_data = json.load(file)
                if lang_code in lang_data:
                    message_template = lang_data[lang_code].get(key, key)
                    try:
                        # Thay thế placeholder bằng giá trị từ kwargs
                        return message_template.format(**kwargs)
                    except KeyError as ke:
                        # Nếu placeholder không khớp với kwargs, trả về thông báo lỗi chi tiết
                        return f"Error in translation: Missing placeholder {ke} for key '{key}'"
                    except ValueError as ve:
                        # Nếu chuỗi mẫu không hợp lệ
                        return f"Error in translation: Invalid format for key '{key}' - {ve}"
        # Nếu không tìm thấy file hoặc ngôn ngữ, trả về key gốc
        return key

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
