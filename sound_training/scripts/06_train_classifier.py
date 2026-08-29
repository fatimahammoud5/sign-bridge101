from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import GroupShuffleSplit


# ============================================================
# SETTINGS
# ============================================================

RANDOM_SEED = 42
EPOCHS = 60
BATCH_SIZE = 32

CLASSES = [
    "explosion",
    "drone",
    "dog_bark",
    "aircraft",
    "siren",
    "other",
]

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "outputs"
MODEL_DIR = BASE_DIR / "models"

EMBEDDINGS_FILE = OUTPUT_DIR / "embeddings.npz"

KERAS_MODEL_FILE = MODEL_DIR / "sound_classifier.keras"
TFLITE_MODEL_FILE = MODEL_DIR / "sound_classifier.tflite"
LABELS_FILE = MODEL_DIR / "sound_classifier_labels.txt"

REPORT_FILE = OUTPUT_DIR / "classification_report.txt"
CONFUSION_FILE = OUTPUT_DIR / "confusion_matrix.png"
HISTORY_FILE = OUTPUT_DIR / "training_history.png"


# ============================================================
# REPRODUCIBILITY
# ============================================================

np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    print("=" * 70)
    print("LOADING EMBEDDINGS")
    print("=" * 70)

    data = np.load(
        EMBEDDINGS_FILE,
        allow_pickle=True,
    )

    X = data["X"].astype(np.float32)
    y = data["y"].astype(np.int64)
    groups = data["source_ids"]

    print(f"X shape      : {X.shape}")
    print(f"y shape      : {y.shape}")
    print(f"groups shape : {groups.shape}")

    print()
    print("Class distribution:")

    for index, class_name in enumerate(CLASSES):
        count = np.sum(y == index)

        print(
            f"{class_name:12s}: "
            f"{count} embeddings"
        )

    return X, y, groups


# ============================================================
# SPLIT DATA
# ============================================================

def split_data(X, y, groups):
    print()
    print("=" * 70)
    print("CREATING TRAIN / VALIDATION / TEST SPLITS")
    print("=" * 70)

    # --------------------------------------------------------
    # Test split = 20%
    # --------------------------------------------------------

    test_splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=RANDOM_SEED,
    )

    train_val_indices, test_indices = next(
        test_splitter.split(
            X,
            y,
            groups=groups,
        )
    )

    X_train_val = X[train_val_indices]
    y_train_val = y[train_val_indices]
    groups_train_val = groups[train_val_indices]

    X_test = X[test_indices]
    y_test = y[test_indices]

    # --------------------------------------------------------
    # Validation = 20% of remaining data
    # --------------------------------------------------------

    val_splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=RANDOM_SEED,
    )

    train_indices, val_indices = next(
        val_splitter.split(
            X_train_val,
            y_train_val,
            groups=groups_train_val,
        )
    )

    X_train = X_train_val[train_indices]
    y_train = y_train_val[train_indices]

    X_val = X_train_val[val_indices]
    y_val = y_train_val[val_indices]

    print(f"Train embeddings      : {len(X_train)}")
    print(f"Validation embeddings : {len(X_val)}")
    print(f"Test embeddings       : {len(X_test)}")

    return (
        X_train,
        y_train,
        X_val,
        y_val,
        X_test,
        y_test,
    )


# ============================================================
# MODEL
# ============================================================

def create_model():
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(
                shape=(1024,)
            ),

            tf.keras.layers.BatchNormalization(),

            tf.keras.layers.Dense(
                256,
                activation="relu",
            ),

            tf.keras.layers.Dropout(0.35),

            tf.keras.layers.Dense(
                128,
                activation="relu",
            ),

            tf.keras.layers.Dropout(0.25),

            tf.keras.layers.Dense(
                len(CLASSES),
                activation="softmax",
            ),
        ]
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=0.001,
        ),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


# ============================================================
# TRAINING PLOT
# ============================================================

def save_training_plot(history):
    plt.figure(figsize=(8, 5))

    plt.plot(
        history.history["accuracy"],
        label="Train Accuracy",
    )

    plt.plot(
        history.history["val_accuracy"],
        label="Validation Accuracy",
    )

    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("SignBridge Sound Classifier Training")
    plt.legend()

    plt.tight_layout()

    plt.savefig(
        HISTORY_FILE,
        dpi=150,
    )

    plt.close()


# ============================================================
# CONFUSION MATRIX
# ============================================================

def save_confusion_matrix(
    y_true,
    y_pred,
):
    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=list(range(len(CLASSES))),
    )

    plt.figure(
        figsize=(8, 7)
    )

    plt.imshow(matrix)

    plt.title("Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")

    plt.xticks(
        range(len(CLASSES)),
        CLASSES,
        rotation=45,
        ha="right",
    )

    plt.yticks(
        range(len(CLASSES)),
        CLASSES,
    )

    for row in range(len(CLASSES)):
        for column in range(len(CLASSES)):
            plt.text(
                column,
                row,
                str(matrix[row, column]),
                ha="center",
                va="center",
            )

    plt.tight_layout()

    plt.savefig(
        CONFUSION_FILE,
        dpi=150,
    )

    plt.close()


# ============================================================
# EXPORT TFLITE
# ============================================================

def export_tflite(model):
    print()
    print("=" * 70)
    print("EXPORTING TFLITE")
    print("=" * 70)

    converter = tf.lite.TFLiteConverter.from_keras_model(
        model
    )

    converter.optimizations = [
        tf.lite.Optimize.DEFAULT
    ]

    tflite_model = converter.convert()

    TFLITE_MODEL_FILE.write_bytes(
        tflite_model
    )

    print("TFLite model saved:")
    print(TFLITE_MODEL_FILE)


# ============================================================
# MAIN
# ============================================================

def main():
    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    X, y, groups = load_data()

    (
        X_train,
        y_train,
        X_val,
        y_val,
        X_test,
        y_test,
    ) = split_data(
        X,
        y,
        groups,
    )

    print()
    print("=" * 70)
    print("BUILDING MODEL")
    print("=" * 70)

    model = create_model()

    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=8,
            restore_best_weights=True,
        ),

        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=4,
            min_lr=1e-6,
        ),
    ]

    print()
    print("=" * 70)
    print("TRAINING")
    print("=" * 70)

    history = model.fit(
        X_train,
        y_train,
        validation_data=(
            X_val,
            y_val,
        ),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1,
    )

    print()
    print("=" * 70)
    print("TESTING")
    print("=" * 70)

    test_loss, test_accuracy = model.evaluate(
        X_test,
        y_test,
        verbose=0,
    )

    print(
        f"Test loss     : "
        f"{test_loss:.4f}"
    )

    print(
        f"Test accuracy : "
        f"{test_accuracy:.4f}"
    )

    probabilities = model.predict(
        X_test,
        verbose=0,
    )

    predictions = np.argmax(
        probabilities,
        axis=1,
    )

    report = classification_report(
        y_test,
        predictions,
        labels=list(
            range(len(CLASSES))
        ),
        target_names=CLASSES,
        digits=4,
        zero_division=0,
    )

    print()
    print("=" * 70)
    print("CLASSIFICATION REPORT")
    print("=" * 70)

    print(report)

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            f"Test accuracy: "
            f"{test_accuracy:.6f}\n\n"
        )

        file.write(report)

    save_training_plot(
        history
    )

    save_confusion_matrix(
        y_test,
        predictions,
    )

    model.save(
        KERAS_MODEL_FILE
    )

    LABELS_FILE.write_text(
        "\n".join(CLASSES),
        encoding="utf-8",
    )

    export_tflite(
        model
    )

    print()
    print("=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)

    print()
    print("Keras model:")
    print(KERAS_MODEL_FILE)

    print()
    print("TFLite model:")
    print(TFLITE_MODEL_FILE)

    print()
    print("Labels:")
    print(LABELS_FILE)

    print()
    print("Classification report:")
    print(REPORT_FILE)

    print()
    print("Confusion matrix:")
    print(CONFUSION_FILE)

    print()
    print("Training graph:")
    print(HISTORY_FILE)


if __name__ == "__main__":
    main()