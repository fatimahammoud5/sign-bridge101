from __future__ import annotations

import time

import cv2
import mediapipe as mp

from common import create_video_detector, result_to_vector


def main() -> None:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Cannot open camera.")

    start_time = time.monotonic()
    previous_timestamp = -1

    with create_video_detector() as detector:
        while True:
            success, frame = cap.read()

            if not success:
                break

            # Detection uses the original, unmirrored frame.
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb,
            )

            timestamp_ms = int(
                (time.monotonic() - start_time) * 1000
            )
            if timestamp_ms <= previous_timestamp:
                timestamp_ms = previous_timestamp + 1
            previous_timestamp = timestamp_ms

            result = detector.detect_for_video(
                mp_image,
                timestamp_ms,
            )

            _, detected, handedness_labels = result_to_vector(
                result
            )

            # Mirror only the display, not the data sent to the model.
            display = cv2.flip(frame, 1)
            height, width = display.shape[:2]

            for hand_index, landmarks in enumerate(
                result.hand_landmarks
            ):
                label = "Unknown"
                if (
                    hand_index < len(result.handedness)
                    and result.handedness[hand_index]
                ):
                    label = (
                        result.handedness[hand_index][0]
                        .category_name
                    )

                for landmark in landmarks:
                    x = width - int(landmark.x * width)
                    y = int(landmark.y * height)
                    cv2.circle(display, (x, y), 3, (255, 255, 255), -1)

                first = landmarks[0]
                text_x = width - int(first.x * width)
                text_y = int(first.y * height)
                cv2.putText(
                    display,
                    label,
                    (text_x, text_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

            status = (
                "Detected: " + ", ".join(handedness_labels)
                if detected
                else "No hand detected"
            )

            cv2.putText(
                display,
                status,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                display,
                "Q: quit",
                (20, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Webcam Landmark Test V2", display)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
