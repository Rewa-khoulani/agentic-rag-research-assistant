# 1. استخدام صورة Python خفيفة
FROM python:3.11-slim

# 2. تعيين مجلد العمل
WORKDIR /app

# 3. تثبيت متطلبات النظام الضرورية (لـ PyMuPDF و OpenCV وغيرها)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. نسخ ملف المتطلبات أولاً (لاستغلال التخزين المؤقت لطبقات Docker)
COPY requirements.txt .

# 5. تثبيت مكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# 6. نسخ باقي كود المشروع
COPY . .

# 7. كشف المنفذ 8080 (الذي تتوقعه غيمة)
EXPOSE 8080

# 8. أمر تشغيل Streamlit على المنفذ 8080
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]