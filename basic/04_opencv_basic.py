import cv2
import os

import numpy as np


def read_image(image_path: str):
    """
    :arg1 image_path: 图像文件路径
    """
    """
    读取图像文件
    :param image_path: 图像文件路径
    :return: 图像数组
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图像文件不存在: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图像文件: {image_path}")

    # 展示图片
    show_image(image)

    # 添加水印
    watermark_image(image, "Watermark")
    return image


def show_image(image: np.ndarray):
    """
    显示图像
    :param image: 图像数组
    """
    cv2.imshow("Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def watermark_image(image: np.ndarray, watermark: str):
    """
    为图像添加水印
    :param image: 图像数组
    :param watermark: 水印文字
    :return: 添加水印后的图像数组
    """
    # 复制原始图像
    watermarked_image = image.copy()

    # 居中添加水印
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_color = (255, 255, 255)  # 白
    font_thickness = 2
    position = (image.shape[1] // 2 - len(watermark) * 10, image.shape[0] // 2)  # 水印位置
    cv2.putText(watermarked_image, watermark, position, font, font_scale, font_color, font_thickness)

    # 展示图片
    show_image(watermarked_image)
    return watermarked_image


def main():
    """
    主函数
    """
    image_dir = os.path.join(os.getcwd(), "image")
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
        print(f"创建目录: {image_dir}")

    image_files = os.listdir(image_dir)
    for image_file in image_files:
        image_path = os.path.join(image_dir, image_file)
        try:
            image = read_image(image_path)
            print(f"成功读取图像: {image_file}, 大小: {image.size}")
        except (FileNotFoundError, ValueError) as e:
            print(f"读取图像 {image_file} 时出错: {e}")


if __name__ == '__main__':
    main()
