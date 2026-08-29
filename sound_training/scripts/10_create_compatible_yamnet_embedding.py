from pathlib import Path

import tensorflow as tf
import tensorflow_hub as hub
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

OUTPUT_PATH = (
    MODEL_DIR
    / "yamnet_embedding_compatible.tflite"
)


class YamnetEmbeddingWrapper(tf.Module):
    def __init__(self):
        super().__init__()

        print("Loading YAMNet...")

        self.yamnet = hub.load(
            "https://tfhub.dev/google/yamnet/1"
        )

        print("YAMNet loaded.")

    @tf.function(
        input_signature=[
            tf.TensorSpec(
                shape=[15600],
                dtype=tf.float32,
                name="waveform",
            )
        ]
    )
    def infer(self, waveform):
        _, embeddings, _ = self.yamnet(
            waveform
        )

        return embeddings


def main():
    print("=" * 70)
    print("SIGNBRIDGE - COMPATIBLE YAMNET EMBEDDING EXPORT")
    print("=" * 70)

    print()
    print("TensorFlow:")
    print(tf.__version__)

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    wrapper = YamnetEmbeddingWrapper()

    print()
    print("Testing TensorFlow model...")

    test_input = tf.zeros(
        [15600],
        dtype=tf.float32,
    )

    test_output = wrapper.infer(
        test_input
    )

    print(
        "TensorFlow output:",
        test_output.shape,
    )

    concrete_function = (
        wrapper.infer
        .get_concrete_function()
    )

    print()
    print("Converting to TFLite...")

    converter = (
        tf.lite.TFLiteConverter
        .from_concrete_functions(
            [concrete_function],
            wrapper,
        )
    )

    # IMPORTANT:
    # Builtin TFLite ops only.
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS
    ]

    # No optimization during first compatible export.
    converter.optimizations = []

    converter.inference_input_type = (
        tf.float32
    )

    converter.inference_output_type = (
        tf.float32
    )

    tflite_model = converter.convert()

    OUTPUT_PATH.write_bytes(
        tflite_model
    )

    print()
    print("Saved:")
    print(OUTPUT_PATH)

    print(
        "Size:",
        f"{OUTPUT_PATH.stat().st_size / 1024 / 1024:.2f} MB",
    )

    print()
    print("=" * 70)
    print("LOCAL TFLITE TEST")
    print("=" * 70)

    interpreter = tf.lite.Interpreter(
        model_path=str(
            OUTPUT_PATH
        )
    )

    interpreter.allocate_tensors()

    inputs = interpreter.get_input_details()
    outputs = interpreter.get_output_details()

    print()
    print("INPUTS")

    for item in inputs:
        print(
            item["name"],
            item["shape"],
            item["dtype"],
        )

    print()
    print("OUTPUTS")

    for item in outputs:
        print(
            item["name"],
            item["shape"],
            item["dtype"],
        )

    # Run one actual inference.
    input_tensor = np.zeros(
        [15600],
        dtype=np.float32,
    )

    interpreter.set_tensor(
        inputs[0]["index"],
        input_tensor,
    )

    interpreter.invoke()

    output = interpreter.get_tensor(
        outputs[0]["index"]
    )

    print()
    print(
        "Actual output shape:",
        output.shape,
    )

    if tuple(output.shape) == (
        1,
        1024,
    ):
        print()
        print("SUCCESS")
        print(
            "Compatible YAMNet embedding "
            "model created."
        )
    else:
        print()
        print("WARNING")
        print(
            "Unexpected output shape."
        )

    print("=" * 70)


if __name__ == "__main__":
    main()