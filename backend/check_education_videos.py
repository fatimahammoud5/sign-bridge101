from pathlib import Path
import cv2


BACKEND_ROOT = Path(__file__).resolve().parent

VIDEOS_DIR = (
    BACKEND_ROOT
    / "education_data"
    / "videos"
)


def main():

    print()
    print("=" * 80)
    print("SIGNBRIDGE - VIDEO CHECK")
    print("=" * 80)

    videos = sorted(
        VIDEOS_DIR.glob("l1_*.mp4")
    )

    if not videos:
        print("No videos found.")
        return

    for video_path in videos:

        cap = cv2.VideoCapture(
            str(video_path)
        )

        fps = cap.get(
            cv2.CAP_PROP_FPS
        )

        frames = cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )

        width = cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )

        height = cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )

        duration = 0

        if fps > 0:
            duration = frames / fps

        size_kb = (
            video_path.stat().st_size
            / 1024
        )

        print()
        print("-" * 80)

        print(
            f"File     : {video_path.name}"
        )

        print(
            f"Size     : {size_kb:.2f} KB"
        )

        print(
            f"FPS      : {fps}"
        )

        print(
            f"Frames   : {frames}"
        )

        print(
            f"Duration : {duration:.3f} sec"
        )

        print(
            f"Resolution: "
            f"{int(width)}x{int(height)}"
        )

        ok, frame = cap.read()

        print(
            f"Can read first frame: {ok}"
        )

        if (
            not ok
            or frames <= 1
            or duration < 0.2
        ):

            print(
                "STATUS   : ❌ BAD / INCOMPLETE"
            )

        else:

            print(
                "STATUS   : ✅ OK"
            )

        cap.release()

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()