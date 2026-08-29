from pathlib import Path

import tensorflow as tf


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"

KERAS_MODEL_PATH = (
    MODEL_DIR
    / "sound_classifier.keras"
)

OUTPUT_MODEL_PATH = (
    MODEL_DIR
    / "sound_classifier_compatible.tflite"
)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("SIGNBRIDGE - COMPATIBLE CLASSIFIER EXPORT")
    print("=" * 70)

    print()
    print("TensorFlow version:")
    print(tf.__version__)

    print()
    print("Loading Keras model:")
    print(KERAS_MODEL_PATH)

    model = tf.keras.models.load_model(
        KERAS_MODEL_PATH
    )

    print()
    print("Keras model loaded successfully.")

    # --------------------------------------------------------
    # Important:
    #
    # Do NOT use Optimize.DEFAULT here.
    #
    # We want a plain float32 TFLite model with only
    # builtin operations wherever possible.
    # --------------------------------------------------------

    converter = (
        tf.lite.TFLiteConverter
        .from_keras_model(model)
    )

    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS
    ]

    converter.optimizations = []

    # Keep float32.
    converter.inference_input_type = tf.float32
    converter.inference_output_type = tf.float32

    print()
    print("Converting...")

    tflite_model = converter.convert()

    OUTPUT_MODEL_PATH.write_bytes(
        tflite_model
    )

    print()
    print("=" * 70)
    print("MODEL EXPORTED")
    print("=" * 70)

    print("Saved:")
    print(OUTPUT_MODEL_PATH)

    print(
        f"Size: "
        f"{OUTPUT_MODEL_PATH.stat().st_size / 1024:.2f} KB"
    )

    # --------------------------------------------------------
    # Test model locally
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CHECKING INPUT / OUTPUT")
    print("=" * 70)

    interpreter = tf.lite.Interpreter(
        model_path=str(
            OUTPUT_MODEL_PATH
        )
    )

    interpreter.allocate_tensors()

    print()
    print("INPUTS")

    for tensor in interpreter.get_input_details():
        print(
            tensor["name"],
            tensor["shape"],
            tensor["dtype"],
        )

    print()
    print("OUTPUTS")

    for tensor in interpreter.get_output_details():
        print(
            tensor["name"],
            tensor["shape"],
            tensor["dtype"],
        )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()