
#  Free AI IELTS Speaking Scorer (with Gemini API)

Một hệ thống chấm điểm kỹ năng Nói trong kỳ thi IELTS hoàn chỉnh, miễn phí và có thể tự host. Dự án này sử dụng các công cụ AI tiên tiến để cung cấp điểm số chi tiết cho bài nói của người dùng, bao gồm cả nhận xét chuyên sâu về Ngữ pháp và Từ vựng

## ✨ Tính năng chính

-   **Chấm điểm bởi AI:** Đánh giá bài nói dựa trên 4 tiêu chí: Fluency, Pronunciation, Grammar, và Vocabulary.
-   **Nhận xét chuyên sâu:** Tận dụng sức mạnh của Gemini API để cung cấp phản hồi chi tiết, mang tính xây dựng cho phần Ngữ pháp và Từ vựng.
-   **Xử lý bất đồng bộ:** Sử dụng Celery và Redis để xử lý các file âm thanh trong nền, giúp hệ thống không bị treo và có khả năng mở rộng.
-   **Triển khai dễ dàng:** Đóng gói toàn bộ ứng dụng bằng Docker, cho phép khởi chạy toàn bộ hệ thống chỉ bằng một lệnh duy nhất.
-   **Hoàn toàn riêng tư:** Dữ liệu âm thanh của bạn được xử lý trên server của bạn, chỉ có phần transcript được gửi ẩn danh đến Google để chấm điểm.

## 🏛️ Kiến trúc & Công nghệ

Hệ thống được xây dựng dựa trên một kiến trúc microservice đơn giản, dễ hiểu.

```
Client → FastAPI → Redis → Celery Worker → [Whisper, Librosa] → Gemini API → SQLite
```

| Thành phần | Công cụ | Mục đích |
| :--- | :--- | :--- |
| **Web Framework** | FastAPI | Xây dựng các API endpoint hiệu năng cao. |
| **Speech-to-Text** | OpenAI Whisper | Chuyển đổi giọng nói thành văn bản với độ chính xác cao. |
| **Fluency/Pronunciation** | Librosa & Pydub | Phân tích các đặc trưng âm thanh như khoảng lặng, cao độ. |
| **Grammar/Vocabulary** | Google Gemini Pro | Đánh giá văn bản và cung cấp điểm số, nhận xét chi tiết. |
| **Hàng đợi tác vụ** | Celery & Redis | Quản lý và xử lý các tác vụ nặng (như phân tích audio) một cách bất đồng bộ. |
| **Cơ sở dữ liệu** | SQLite | Lưu trữ kết quả chấm điểm một cách gọn nhẹ. |
| **Triển khai** | Docker & Docker Compose | Đóng gói và chạy toàn bộ ứng dụng một cách nhất quán. |

## 🚀 Bắt đầu

### Yêu cầu
-   [Git](https://git-scm.com/)
-   [Docker](https://www.docker.com/products/docker-desktop/)
-   [Docker Compose](https://docs.docker.com/compose/install/) (thường đi kèm với Docker Desktop)

### Hướng dẫn cài đặt

**1. Clone Repository**
```bash
git clone https://github.com/your-username/ielts-scorer.git
cd ielts-scorer
```

**2. Cấu hình Gemini API Key**

Hệ thống cần một API key từ Google AI Studio để chấm điểm Ngữ pháp và Từ vựng.

-   Truy cập [Google AI Studio](https://aistudio.google.com/) và tạo một API Key mới.
-   Tạo một file tên là `.env` trong thư mục gốc của dự án.
-   Sao chép nội dung dưới đây vào file `.env` và thay thế `YOUR_API_KEY_HERE` bằng key của bạn.

```ini
# File: .env
# Tuyệt đối không đưa file này lên Git.

GEMINI_API_KEY="YOUR_API_KEY_HERE"
PYTHONUNBUFFERED=1
```
> ⚠️ **Cảnh báo bảo mật:** File `.env` chứa thông tin nhạy cảm. Nó đã được thêm vào file `.gitignore` để tránh bị đưa lên Git một cách vô tình. **Không bao giờ chia sẻ API key của bạn một cách công khai.**

**3. Chạy ứng dụng bằng Docker Compose**

Đây là cách được khuyến khích nhất. Mở terminal tại thư mục gốc của dự án và chạy lệnh:

```bash
docker-compose up --build
```

-   `--build`: Lệnh này sẽ build các Docker image lần đầu tiên.
-   Docker sẽ tự động tải Redis image, build image cho ứng dụng của bạn, và khởi chạy 3 container: `redis`, `api`, và `worker`.
-   Để dừng ứng dụng, nhấn `Ctrl + C`.

## 🛠️ Cách sử dụng

Sau khi hệ thống đã khởi động, bạn có thể tương tác với nó thông qua các API endpoint.

### 1. Gửi bài nói để chấm điểm

Gửi một yêu cầu `POST` đến `/api/v1/submit` với `user_id` và file âm thanh (`audio`).

Sử dụng `curl`:
```bash
curl -X POST "http://localhost:8000/api/v1/submit" \
  -F "user_id=test_user_01" \
  -F "audio=@/path/to/your/audio.mp3"
```
-   Thay thế `/path/to/your/audio.mp3` bằng đường dẫn thực tế đến file âm thanh của bạn.
-   Bạn sẽ nhận được một phản hồi chứa `submission_id`.

```json
{
  "submission_id": "Abc123Xyz789",
  "status": "PENDING",
  "topic_prompt":""
}
```
```json
{
    "submission_id": "GyrCkqnqntmnJVitatmZD3",
    "user_id": "user123",
    "status": "COMPLETED",
    "topic_prompt": "wedding",
    "transcript": "I'm a wedding planner. My job brings me a lot of pleasure. Today is an amazing day. I am planning my sister's wedding. She will wear a beautiful white dress. I also get to wear a lovely dress. After the wedding, all the guests will have a nice dinner and will dance for hours. In the evening, my sister and her new husband will cut a cake that I designed. I hope they like it a lot.",
    "scores": {
        "fluency": 8.0,
        "pronunciation": 5.0,
        "task_response": 6.0,
        "grammar": 6.0,
        "vocabulary": 5.5,
        "overall": 6.1
    },
    "feedback": {
        "task_response": "The candidate addresses the topic directly and maintains relevance throughout. The ideas are logically connected, providing a clear narrative flow (job description → current task → specific wedding events). The response is coherent, with clear sequencing (e.g., 'After the wedding,' 'In the evening'). However, the response is brief, limiting the opportunity to fully develop complex points or demonstrate sustained discourse. For higher scores, the candidate would need to extend the response, perhaps by elaborating on the challenges of planning or the emotional significance of the event, rather than just listing activities.",
        "grammar": "Grammatical accuracy is very high; there are virtually no errors in this sample. The candidate controls simple tenses (simple present: 'brings,' 'am planning') and the simple future ('will wear,' 'will dance') effectively. However, the range is limited. The response consists primarily of simple, short sentences connected by basic coordination. There is a lack of complex grammatical structures, such as subordinate clauses, passive voice, or varied relative clauses, which is necessary to achieve scores of 7.0 and above. The candidate needs to practice embedding ideas using complex structures to demonstrate flexibility.",
        "vocabulary": "The candidate uses adequate vocabulary for the topic, including 'wedding planner' and specific terms like 'designed' (the cake). However, the vocabulary tends to be basic and common, relying heavily on simple adjectives such as 'amazing,' 'beautiful,' 'lovely,' and 'nice.' There is no evidence of sophisticated or low-frequency vocabulary, precise collocations, or idiomatic language (e.g., 'tying the knot,' 'a momentous occasion'). To improve, the candidate should aim to replace vague adjectives (like 'nice') with more precise descriptive language and incorporate a wider range of academic or specialized terminology.",
        "overall": "The candidate delivers a clear, accurate, and relevant response. The main strength is the high level of accuracy in basic grammar. The primary limitation is the lack of complexity and extension across all criteria. To reach a higher band, the candidate must actively practice extending their answers using a variety of complex sentence structures and demonstrating a broader, more nuanced vocabulary repertoire. The response is currently too short and structurally simple for advanced levels."
    }
}
```

*(Lưu ý: Bạn có thể mở rộng API và cơ sở dữ liệu để lưu và trả về cả phần nhận xét chi tiết từ Gemini.)*

## 📁 Cấu trúc thư mục

```
ielts-scorer/
├── app/
│   ├── main.py             # FastAPI server, định nghĩa API endpoints
│   ├── celery_app.py       # Cấu hình Celery và định nghĩa tác vụ nền
│   ├── database.py         # Thiết lập cơ sở dữ liệu SQLAlchemy
│   ├── models/
│   │   └── submission.py   # Mô hình dữ liệu cho bảng submissions
│   └── services/
│       ├── audio_analysis.py # Hàm chấm điểm Fluency & Pronunciation
│       ├── scoring.py        # Logic tổng hợp điểm, gọi Gemini API
│       └── speech_to_text.py # Wrapper cho OpenAI Whisper
├── uploads/                # Nơi lưu trữ các file audio được tải lên
├── .env                    # (Bạn tự tạo) Chứa API key và biến môi trường
├── docker-compose.yml      # Định nghĩa các service cho Docker
├── Dockerfile              # Công thức để build image cho ứng dụng
└── requirements.txt        # Danh sách các thư viện Python
```

## 🤝 Đóng góp

Chào mừng mọi sự đóng góp! Vui lòng tạo một Pull Request hoặc mở một Issue để thảo luận về các thay đổi bạn muốn thực hiện.

## 📄 Giấy phép

Dự án này được cấp phép dưới Giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.
