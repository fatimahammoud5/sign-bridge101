استبدلي classes_v2.txt بالقائمة الجديدة داخل:
data/WLASL100/classes_v2.txt

ثم سجلي البيانات باستخدام:
python src_v2/07_record_webcam_dataset.py

لكل فئة:
train = 12
val = 3
test = 3

ثم:
python src_v2/08_extract_webcam_features.py
python src_v2/03_train_model.py
python src_v2/04_test_model.py

بعد التدريب انسخي 09_live_sentence.py إلى src_v2 وشغلي:
python src_v2/09_live_sentence.py

لا تستخدمي 01_check_dataset.py مع هذه القائمة إذا لم تكن الكلمات موجودة في WLASL،
لأننا سنعتمد على تسجيلات كاميرتك لهذه الكلمات.
