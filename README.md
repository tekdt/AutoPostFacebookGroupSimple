
# Auto Post Facebook Group Simple

- Tác giả: TekDT
- Email: dinhtrungtek@gmail.com
- Mô tả: Phần mềm tự động đăng bài lên Facebook với nội dung tạo tự động bằng AI, hỗ trợ chuyển đổi tài khoản facebook phụ và hỗ trợ tải lên hình ảnh.
- Phiên bản: 1.2.0
- Ngày phát hành: 11/4/2023

# Hướng dẫn cài đặt
* Chạy trực tiếp từ script python
- Cài đặt Python3: https://www.python.org/downloads/
- Cài đặt thư viện cần thiết: webdriver, EC, BeautifulSoup, Groq, psutil bằng câu lệnh python py -m pip install <tên thư viện>
- Cài đặt Chrome: https://www.google.com/intl/vi_vn/chrome/
Các phần mềm cũng có thể cài đặt tự động theo phần mềm TekDT Tool 4 Auto Install Soft: https://github.com/tekdt/TekDTTool4AutoInstallSoft_Release

* Chạy trực tiếp từ file EXE đã biên dịch (khuyến khích).
- Chỉ cần cài đặt Chrome: https://www.google.com/intl/vi_vn/chrome/

# Hướng dẫn sử dụng
Ở giao diện chương trình sẽ có tổng cộng 5 tab, bao gồm: Facebook, Groq AI, Hình ảnh, Thông tin phần mềm và Thiết lập.
- Tab Facebook: Thiết lập cơ bản về facebook
+ Email: Hãy nhập user facebook bạn ở đây, có thể là số điện thoại hoặc Email.
+ Mật khẩu: Nhập mật khẩu facebook.
+ Sử dụng profile Chrome hiện tại: Nếu bạn đã đăng nhập facebook trên Chrome và muốn sử dụng trực tiếp profile này mà không cần đăng nhập lại thì hay tick chọn tuỳ chọn này.
+ Nhập liên kết nhóm: Nếu bạn chỉ nhập link nhóm facebook đơn lẻ, thì nhập vào ô này rồi nhấn nút Thêm. Link nhóm facebook phải đầy đủ, chẳng hạn như: https://www.facebook.com/groups/abcdefghiklmn/
+ Nhập từ file: Nếu bạn muốn nhập hàng loạt các link nhóm facebook, hãy dùng Nút bấm này. Mỗi link nhóm facebook trong file là một dòng. Hỗ trợ tập tin .csv và .txt

- Tab Groq AI: Tạo nội dung đăng bài tự động bằng AI
+ Groq API Key: Đây là API Key được tạo từ trang Groq (miễn phí), hãy tạo một key tại trang https://console.groq.com/keys
+ Các mô hình AI: Hiện tại, có sẵn 3 mô hình AI qwen-2.5-32b, llama-3.3-70b-versatile, gemma2-9b-it. Mặc định chương trình sẽ tự động tạo nội dung ngẫu nhiên từ 3 mô hình AI này để tạo nội dung bài đăng. Nếu bạn muốn sử dụng một mô hình duy nhất, hãy xoá bớt hoặc điền tên mô hình nhiều lần. Nhớ là ngăn cách chúng bằng dấu chấm phẩy ";" và không có khoảng cách giữa chúng.
+ Promt cho bài đăng: Hãy nhập yêu cầu của bạn vào đây để mô hình AI tự động tạo bài đăng theo ý muốn. Ví dụ: Tạo bài đăng facebook khoảng 200 từ, để giới thiệu phần mềm Auto Post Facebook Group Simple, có chức năng tự động đăng bài lên Facebook với nội dung tạo tự động bằng AI, hỗ trợ chuyển đổi tài khoản facebook phụ và hỗ trợ tải lên hình ảnh.

- Tab Hình ảnh: Lựa chọn hình ảnh đăng bài đính kèm với bài đăng
+ Chọn thư mục chứa hình ảnh: Nhấn chọn thư mục và chọn thư mục chứa các hình ảnh đăng bài đính kèm với bài đăng. Phần mềm sẽ đính kèm toàn bộ các hình ảnh trong thư mục, gồm các loại tập tin như .png, .jpg, .jpeg, .gif, .bmp

- Tab Thiết lập: Cấu hình các XPath để chương trình hoạt động đúng. Hãy thay các cụm từ (chẳng hạn như tên facebook hoặc ngôn ngữ của facebook) cho phù hợp với tài khoản của bạn. Bên dưới là các giá trị tham khảo (có thể hoạt động với tài khoản của bạn)
+ Đường dẫn Chrome: C:\Users\TekDT\AppData\Local\Google\Chrome\User Data
+ XPath login success: //div[@aria-label='Trang cá nhân của bạn' and @role='button' and @aria-expanded='false' and @tabindex='0']
+ XPath avatar: //div[@aria-label='Trang cá nhân của bạn' and @role='button' and @aria-expanded='false' and @tabindex='0']
+ XPath xác nhận đã chuyển sang trang cá nhân khác: //span[contains(@class, 'x193iq5w') and normalize-space(text())='Đã chuyển sang TekDT']
+ XPath second_account: //div[@aria-label='Chuyển sang TekDT' and @role='button' and @tabindex='0']
+ XPath image_button: //div[@class='x4k7w5x x1h91t0o x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1jfb8zj x1beo9mf x3igimt xarpa2k x1n2onr6 x1qrby5j']//img[contains(@class, 'x1b0d499') and contains(@src, 'rsrc.php/v4/yD/r/4lAYcqypgif.png')]
+ XPath: upload_image: //div[contains(@class, 'x9f619') and contains(@class, 'x1ja2u2z')]//*[text()='Thêm ảnh/video']/preceding::input[@type='file'][1]
+ XPath post_box_pre: //span[contains(text(), 'Bạn viết gì đi...')]
+ XPath post_box_xpaths: //div[@aria-label='Tạo bài viết công khai...' and @role='textbox']
//div[@aria-label='Bạn viết gì đi...' and @role='textbox']
+ XPath post_button: //span[contains(@class, 'x1lliihq') and text()='Đăng']
+ XPath xác nhận đã đăng: //span[contains(@class, 'x1lliihq') and text()='Đăng']

# Trách nhiệm
TekDT không chịu trách nhiệm cho tài khoản của bạn khi bạn tải ở các nguồn khác được tuỳ biến, sửa đổi dựa trên script này. Bạn có thể sử dụng chương trình này miễn phí thì hãy tin nó. TekDT sẽ không thu thập tài khoản tài khoản hay làm bất cứ điều gì với tài khoản của bạn.
Nếu không tin TekDT hoặc sợ mất tài khoản, vui lòng thoát khỏi trang này, hãy xoá phần mềm/script đã tải.

# Hỗ trợ:
Mọi liên lạc của bạn với TekDT sẽ rất hoan nghênh và đón nhận để TekDT có thể cải tiến phần mềm/script này tốt hơn. Hãy thử liên hệ với TekDT bằng những cách sau:
- Telegram: @tekdt1152
- Zalo: 0944.095.092
- Email: dinhtrungtek@gmail.com
- Facebook: @tekdtcom

# Đóng góp:
Để phần mềm/script ngày càng hoàn thiện và nhiều tính năng hơn. TekDT cũng cần có động lực để duy trì. Nếu phần mềm/script này có ích với công việc của bạn, hãy đóng góp một chút. TekDT rất cảm kích việc làm chân thành này của bạn.
- MOMO: https://me.momo.vn/TekDT1152
- Biance ID: 877691831
- USDT (BEP20): 0x53a4f3c22de1caf465ee7b5b6ef26aed9749c721
