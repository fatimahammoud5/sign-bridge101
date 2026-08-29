from pathlib import Path

import tensorflow as tf
import tensorflow_hub as hub


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"

OUTPUT_MODEL = (
    MODEL_DIR
    / "yamnet_embedding.tflite"
)


# ============================================================
# YAMNET WRAPPER
# ============================================================

class YamnetEmbeddingModel(tf.Module):

    def __init__(self):
        super().__init__()

        print("Loading YAMNet from TensorFlow Hub...")

        self.yamnet = hub.load(
            "https://tfhub.dev/google/yamnet/1"
        )

        print("YAMNet loaded successfully.")

    @tf.function(
        input_signature=[
            tf.TensorSpec(
                shape=[15600],
                dtype=tf.float32,
                name="waveform",
            )
        ]
    )
    def __call__(self, waveform):

        scores, embeddings, spectrogram = (
            self.yamnet(waveform)
        )

        # ====================================================
        # For a 15600-sample waveform,
        # YAMNet normally produces one embedding:
        #
        # [1, 1024]
        #
        # We return only the embeddings.
        # ====================================================

        return {
            "embeddings": embeddings
        }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SIGNBRIDGE - CREATE YAMNET EMBEDDING TFLITE")
    print("=" * 70)

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = YamnetEmbeddingModel()

    print()
    print("Creating concrete function...")

    concrete_function = (
        model.__call__.get_concrete_function()
    )

    # ========================================================
    # Test TensorFlow version first
    # ========================================================

    print()
    print("Testing TensorFlow model...")

    test_waveform = tf.zeros(
        [15600],
        dtype=tf.float32,
    )

    result = model(
        test_waveform
    )

    embeddings = result[
        "embeddings"
    ]

    print(
        "TensorFlow embedding shape:",
        embeddings.shape,
    )

    # ========================================================
    # Convert to TFLite
    # ========================================================

    print()
    print("Converting to TensorFlow Lite...")

    converter = (
        tf.lite.TFLiteConverter
        .from_concrete_functions(
            [concrete_function],
            model,
        )
    )

    # Enable builtin + select TensorFlow ops
    # in case YAMNet requires them.
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS,
    ]

    converter.optimizations = [
        tf.lite.Optimize.DEFAULT
    ]

    tflite_model = converter.convert()

    OUTPUT_MODEL.write_bytes(
        tflite_model
    )

    print()
    print("=" * 70)
    print("MODEL CREATED")
    print("=" * 70)

    print(
        f"Saved to:\n{OUTPUT_MODEL}"
    )

    print(
        f"Size: "
        f"{OUTPUT_MODEL.stat().st_size / 1024 / 1024:.2f} MB"
    )

    # ========================================================
    # Test TFLite
    # ========================================================

    print()
    print("=" * 70)
    print("TESTING TFLITE MODEL")
    print("=" * 70)

    interpreter = tf.lite.Interpreter(
        model_path=str(
            OUTPUT_MODEL
        )
    )

    interpreter.allocate_tensors()

    input_details = (
        interpreter.get_input_details()
    )

    output_details = (
        interpreter.get_output_details()
    )

    print()
    print("INPUTS")

    for item in input_details:
        print(
            item["name"],
            item["shape"],
            item["dtype"],
        )

    print()
    print("OUTPUTS")

    for item in output_details:
        print(
            item["name"],
            item["shape"],
            item["dtype"],
        )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()