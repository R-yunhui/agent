"""
OpenCV 视频处理示例

cv2.CAP_PROP_FPS - 帧率
cv2.CAP_PROP_FRAME_COUNT - 总帧数
cv2.CAP_PROP_POS_FRAMES - 当前帧位置
cv2.CAP_PROP_POS_MSEC - 当前毫秒位置
"""
import os
import time

import cv2


def extract_video_frame(video_path: str, output_dir: str, interval: int = 1) -> bool:
    """
    从视频中提取帧并保存到指定目录
    :param video_path: 视频文件路径
    :param output_dir: 输出目录路径
    :param interval: 每隔多少帧抽取一帧，默认1表示每帧都抽
    :return: 是否成功抽帧
    """
    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return False

    fps = capture.get(cv2.CAP_PROP_FPS)  # 获取帧率
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))  # 总帧数

    print(f"视频帧率: {fps}, 总帧数: {total_frames}")

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = capture.read()
        if not ret:
            break

        if frame_count % interval == 0:
            output_path = os.path.join(output_dir, f"frame_{saved_count:06d}.jpg")
            cv2.imwrite(output_path, frame)
            saved_count += 1

        frame_count += 1

    capture.release()
    print(f"抽帧完成，共保存 {saved_count} 帧")
    return True


def extract_frames_by_time(video_path: str, output_dir: str, time_interval: float = 1.0) -> bool:
    """
    从视频中按时间间隔提取帧并保存到指定目录
    :param video_path: 视频文件路径
    :param output_dir: 输出目录路径
    :param time_interval: 时间间隔，单位秒，默认1秒抽1帧
    :return: 是否成功抽帧
    """
    os.makedirs(output_dir, exist_ok=True)

    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return False

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * time_interval)  # 计算帧间隔

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = capture.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            cv2.imwrite(f"{output_dir}/frame_{saved_count:04d}.jpg", frame)
            saved_count += 1

        frame_count += 1

    capture.release()
    print(f"抽帧完成，共保存 {saved_count} 帧")
    return True


def extract_frame_at_time(video_path, time_sec):
    """
    从视频中抽取指定秒数的帧
    :param video_path: 视频文件路径
    :param time_sec: 指定的秒数
    :return: 提取到的帧（如果成功），否则 None
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_number = int(time_sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    ret, frame = cap.read()
    cap.release()

    return frame if ret else None


def main():
    start_time = time.time()
    # extract_video_frame(os.path.join(os.getcwd(), "video_data", "test.mp4"), os.path.join(os.getcwd(), "video_frames"), 1)
    # 按照时间进行抽帧，每1秒抽1帧
    # success = extract_frames_by_time(os.path.join(os.getcwd(), "video_data", "test.mp4"),
    #                                  os.path.join(os.getcwd(), "video_frames_by_time"), 1.0)
    # if success:
    #     end_time = time.time()
    #     print(f"抽帧耗时: {end_time - start_time:.2f} 秒")
    # else:
    #     print("抽帧失败")

    # 抽取指定秒数的帧
    frame = extract_frame_at_time(os.path.join(os.getcwd(), "video_data", "test.mp4"), 10.0)
    if frame is not None:
        cv2.imwrite(os.path.join(os.getcwd(), "video_frames_by_time", "frame_10.0.jpg"), frame)
        print(f"指定秒数的帧提取成功, 耗时: {time.time() - start_time:.2f} 秒")
    else:
        print("指定秒数的帧提取失败")


if __name__ == "__main__":
    main()
