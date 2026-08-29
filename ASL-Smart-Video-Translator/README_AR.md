# نظام التعرف على إشارات ASL — النسخة V2

## لا تحذفي المشروع القديم

انسخي مجلد `src_v2` إلى جذر مشروعك، وأنشئي `models_v2`.

ضعي ملف `classes_v2.txt` داخل مجلد `WLASL100`.

الهيكل المتوقع:

```text
project/
├── src_v2/
├── models/
│   └── mediapipe/
│       └── hand_landmarker.task
├── models_v2/
└── WLASL100/
    ├── classes_v2.txt
    ├── train/
    ├── val/
    └── test/
```

يمكن أيضًا أن يكون `WLASL100` داخل `data/WLASL100`، والكود سيكتشفه تلقائيًا.

## الأوامر بالترتيب

من داخل جذر المشروع:

```bash
python src_v2/01_check_dataset.py
```

يجب أن ينتهي بالرسالة:

```text
Dataset structure is ready.
```

بعد ذلك:

```bash
python src_v2/02_extract_features.py
```

إذا أردتِ إعادة استخراج الملفات الموجودة:

```bash
python src_v2/02_extract_features.py --overwrite
```

ثم التدريب:

```bash
python src_v2/03_train_model.py
```

ثم اختبار النموذج على بيانات الاختبار المحفوظة:

```bash
python src_v2/04_test_model.py
```

ثم اختبار نقاط الكاميرا:

```bash
python src_v2/05_test_webcam_landmarks.py
```

وأخيرًا تشغيل المترجم:

```bash
python src_v2/06_live_translator.py
```

## مهم

لا تنتقلي إلى الكاميرا إذا كانت دقة `04_test_model.py` ضعيفة.
يجب أولًا إصلاح البيانات أو اختيار إشارات أخرى.

## تعديل الكلمات

عدلي فقط:

```text
WLASL100/classes_v2.txt
```

ويجب أن تكون كل كلمة موجودة داخل:

```text
WLASL100/train/<word>
WLASL100/val/<word>
WLASL100/test/<word>
```

بعد تغيير الكلمات، احذفي فقط:

```text
WLASL100/features_v2
models_v2
```

ثم أعيدي الاستخراج والتدريب. لا تحذفي الفيديوهات الأصلية.
