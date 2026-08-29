import tensorflow as tf
import tensorflow_hub as hub


def main():
    print("=" * 60)
    print("SIGNBRIDGE - YAMNET TRAINING TEST")
    print("=" * 60)

    print("\nTensorFlow version:")
    print(tf.__version__)

    print("\nLoading YAMNet from TensorFlow Hub...")

    yamnet = hub.load(
        "https://tfhub.dev/google/yamnet/1"
    )

    print("YAMNet loaded successfully.")

    # 3 seconds of silence at 16 kHz.
    waveform = tf.zeros(
        [16000 * 3],
        dtype=tf.float32,
    )

    print("\nRunning test inference...")

    scores, embeddings, spectrogram = yamnet(
        waveform
    )

    print("\nOutputs:")

    print("Scores shape:")
    print(scores.shape)

    print("Embeddings shape:")
    print(embeddings.shape)

    print("Spectrogram shape:")
    print(spectrogram.shape)

    print("\nEmbedding dimension:")
    print(embeddings.shape[-1])

    if embeddings.shape[-1] == 1024:
        print("\nSUCCESS")
        print(
            "YAMNet embeddings are ready "
            "for custom classifier training."
        )
    else:
        print("\nWARNING")
        print(
            "Unexpected embedding dimension:",
            embeddings.shape[-1],
        )


if __name__ == "__main__":
    main()