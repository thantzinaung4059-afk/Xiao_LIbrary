import os
import base64
from flask import Flask, render_template_string, request, send_from_directory
import fitz  # PyMuPDF

# Local books directory (VS Code ထဲက books ဖိုဒါကို ညွှန်ထားပါတယ်)
BOOK_DIR = os.path.join(os.path.dirname(__file__), 'books')

app = Flask("XiaoLibraryApp")

@app.route('/')
def index():
    query = request.args.get('q', '').lower()
    books = []

    if os.path.exists(BOOK_DIR):
        for filename in sorted(os.listdir(BOOK_DIR)):
            if filename.lower().endswith('.pdf'):
                title = os.path.splitext(filename)[0]

                file_path = os.path.join(BOOK_DIR, filename)
                preview_img = ""
                try:
                    doc = fitz.open(file_path)
                    if len(doc) > 0:
                        page = doc.load_page(0)
                        pix = page.get_pixmap(dpi=100)
                        img_bytes = pix.tobytes("png")
                        preview_img = base64.b64encode(img_bytes).decode('utf-8')
                except:
                    pass

                if not query or query in title.lower():
                    books.append({"title": title, "filename": filename, "preview": preview_img})

    return render_template_string(HTML_TEMPLATE, books=books, query=query)

@app.route('/download/<path:filename>')
def download_book(filename):
    return send_from_directory(BOOK_DIR, filename, as_attachment=True)

@app.route('/read/<path:filename>')
def read_book(filename):
    file_path = os.path.join(BOOK_DIR, filename)
    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)

        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        encoded_img = base64.b64encode(img_bytes).decode('utf-8')

        return render_template_string(READER_TEMPLATE, filename=filename, current_page=1, total_pages=total_pages, image_data=encoded_img)
    except Exception as e:
        return f"<h3 style='color:white; background:#121212; padding:20px;'>ဖိုင်ဖွင့်၍ မရပါ။<br><br>Error: {e}</h3>"

@app.route('/page/<path:filename>', methods=['POST', 'GET'])
def view_page_redirect(filename):
    if request.method == 'POST':
        try:
            page_num = int(request.form.get('page_num', 1))
        except:
            page_num = 1
        return view_page_render(filename, page_num)
    return view_page_render(filename, 1)

@app.route('/page/<path:filename>/<int:page_num>')
def view_page_get(filename, page_num):
    return view_page_render(filename, page_num)

def view_page_render(filename, page_num):
    file_path = os.path.join(BOOK_DIR, filename)
    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)

        if page_num < 1: page_num = 1
        if page_num > total_pages: page_num = total_pages

        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        encoded_img = base64.b64encode(img_bytes).decode('utf-8')

        return render_template_string(READER_TEMPLATE, filename=filename, current_page=page_num, total_pages=total_pages, image_data=encoded_img)
    except Exception as e:
        return f"Error loading page: {e}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <title>Xiao Library</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #121212 !important; color: #e0e0e0 !important; }
        .form-control { background-color: #1e1e1e !important; color: #ffffff !important; border-color: #333333 !important; }
        .form-control::placeholder { color: #aaaaaa !important; }
        .card { background-color: #1e1e1e !important; border-color: #333333 !important; }
        .card-title { color: #ffffff !important; }
        .quote-banner {
            background: linear-gradient(135deg, #1e1e1e, #2a2a2a);
            border-left: 4px solid #ffc107;
            border-radius: 8px; padding: 15px 20px; margin-bottom: 25px;
        }
        .quote-text { font-style: italic; color: #f1f1f1; font-size: 0.95rem; margin-bottom: 0; }
        .zoom-img { transition: transform 0.3s ease; cursor: zoom-in; }
        .live-clock {
            font-family: monospace;
            font-size: 0.95rem;
            color: #ffc107;
            background: #1e1e1e;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid #333333;
            text-align: right;
            line-height: 1.2;
        }
    </style>
</head>
<body>
    <div class="container my-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1 class="m-0">📚 Xiao Library</h1>
            <div id="liveClock" class="live-clock">Loading time...</div>
        </div>

        <div class="quote-banner">
            <p class="quote-text">
                ⏳ ရက်ပေါင်း ၃ သောင်းကျော် သေမျိုးနွယ် ဘဝ၏ တစ်ခုတည်းသော ထွက်ပေါက်မှာ <strong>'စာအုပ်များ'</strong> ဖြစ်သည်။ ခန္ဓာကိုယ်ကို မြေပြင်၌ ထားရစ်ကာ စိတ်ဝိညာဉ်ကို အတွေးဘုံ၌ လွှတ်တင်ခြင်းသည် ဘဝအမောများအတွက် အထိရောက်ဆုံးသော ကုထုံးဖြစ်သည် 📖✨
            </p>
        </div>

        <form method="GET" action="/" class="input-group mb-4">
            <input type="text" name="q" class="form-control" placeholder="စာအုပ်အမည်ဖြင့် ရှာရန်..." value="{{ query }}">
            <button class="btn btn-primary" type="submit">ရှာမည်</button>
        </form>

        <div class="row">
            {% if books %}
                {% for book in books %}
                <div class="col-md-6 mb-3">
                    <div class="card h-100 shadow-sm p-3">
                        <div class="card-body d-flex flex-column">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <h5 class="card-title m-0 pe-2">{{ book.title }}</h5>
                                <button class="btn btn-outline-warning btn-sm py-0 px-2 flex-shrink-0" style="font-size: 0.8rem;" data-bs-toggle="modal" data-bs-target="#previewModal_{{ loop.index }}">🔍 Preview</button>
                            </div>

                            <div class="mt-auto d-flex gap-2">
                                <a href="/read/{{ book.filename }}" class="btn btn-outline-primary flex-grow-1" target="_blank">📖 ဖတ်မည်</a>
                                <a href="/download/{{ book.filename }}" class="btn btn-success">📥 ဒေါင်းရန်</a>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="modal fade" id="previewModal_{{ loop.index }}" tabindex="-1" aria-labelledby="previewModalLabel_{{ loop.index }}" aria-hidden="true">
                  <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content bg-dark text-light border-secondary">
                      <div class="modal-header border-secondary">
                        <h5 class="modal-title" id="previewModalLabel_{{ loop.index }}">📖 {{ book.title }} (Preview)</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                      </div>
                      <div class="modal-body text-center" style="max-height: 70vh; overflow-y: auto;">
                        {% if book.preview %}
                            <div style="overflow: hidden; display: inline-block;">
                                <img src="data:image/png;base64,{{ book.preview }}" class="img-fluid rounded zoom-img" id="zoomImg_{{ loop.index }}" onclick="toggleZoom('zoomImg_{{ loop.index }}')" alt="First Page Preview" style="max-height: 500px; transform-origin: center center;">
                            </div>
                            <p class="text-muted small mt-2">💡 ပုံကို ကလစ်နှိပ်၍ Zoom ဆွဲကြည့်နိုင်ပါသည်</p>
                        {% else %}
                            <p class="text-muted">Preview မရှိပါ။</p>
                        {% endif %}
                      </div>
                    </div>
                  </div>
                </div>
                {% endfor %}
            {% else %}
                <p class="text-center text-muted">စာအုပ်များ မတွေ့ရှိပါ။ (books ဖိုဒါထဲသို့ PDF များထည့်ပါ)</p>
            {% endif %}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function toggleZoom(imgId) {
            const img = document.getElementById(imgId);
            if (img.style.transform === "scale(1.8)") {
                img.style.transform = "scale(1)";
                img.style.cursor = "zoom-in";
            } else {
                img.style.transform = "scale(1.8)";
                img.style.cursor = "zoom-out";
            }
        }

        function updateClock() {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');

            const ampm = hours >= 12 ? 'PM' : 'AM';
            const hours12 = String(now.getHours() % 12 || 12).padStart(2, '0');
            const timeStr = `${hours12}:${minutes}:${seconds} ${ampm}`;

            const day = String(now.getDate()).padStart(2, '0');
            const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            const monthStr = months[now.getMonth()];
            const year = now.getFullYear();
            const dateStr = `${day}-${monthStr}-${year}`;

            document.getElementById('liveClock').innerHTML = `${timeStr}<br>${dateStr}`;
        }

        setInterval(updateClock, 1000);
        updateClock();
    </script>
</body>
</html>
"""

READER_TEMPLATE = """
<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <title>Reading Book</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #121212; color: #fff; text-align: center; margin: 0; padding: 20px; }
        .toolbar {
            background: #1e1e1e; padding: 10px 20px; border-radius: 8px; display: inline-flex;
            align-items: center; gap: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            flex-wrap: wrap; justify-content: center;
        }
        .book-img { max-width: 100%; height: auto; box-shadow: 0 0 15px rgba(0,0,0,0.8); border-radius: 5px; }
        .page-input {
            width: 65px; text-align: center; background: #ffffff !important; color: #000000 !important;
            border: 1px solid #ced4da !important; border-radius: 4px; padding: 3px; font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <a href="/" class="btn btn-secondary btn-sm">🏠 ပင်မ</a>
        <a href="/download/{{ filename }}" class="btn btn-success btn-sm">📥 ဒေါင်းလုပ်ဆွဲရန်</a>

        <div class="vr bg-secondary"></div>

        <a href="/page/{{ filename }}/{{ current_page - 1 }}" class="btn btn-primary btn-sm {% if current_page <= 1 %}disabled{% endif %}">⬅️ ရှေ့</a>

        <form action="/page/{{ filename }}" method="POST" class="d-inline-flex align-items-center gap-1 m-0">
            <input type="number" name="page_num" value="{{ current_page }}" min="1" max="{{ total_pages }}" class="page-input">
            <span class="text-white fw-bold" style="margin-left: -2px; margin-right: 2px;">/ {{ total_pages }}</span>
            <button type="submit" class="btn btn-outline-light btn-sm py-0 px-2" style="font-size: 0.8rem;">Go</button>
        </form>

        <a href="/page/{{ filename }}/{{ current_page + 1 }}" class="btn btn-primary btn-sm {% if current_page >= total_pages %}disabled{% endif %}">နောက် ➡️</a>
    </div>

    <div>
        <img src="data:image/png;base64,{{ image_data }}" class="page-img book-img" alt="Book Page">
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)