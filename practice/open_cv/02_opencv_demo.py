import cv2
from pathlib import Path

import numpy as np


def read_image(image_path) -> np.ndarray:
    """读取图片"""
    path = Path(image_path)
    if not path.exists():
        print(f"给定路径 {image_path} 的文件不存在")
        raise FileNotFoundError

    # 读取图片
    img = cv2.imread(str(path))
    if img is None:
        print(f"无法读取图片: {image_path}")
        raise ValueError("图片读取失败")

    return img


def show_image(window_name, img):
    """显示图片"""
    cv2.imshow(window_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def compress_image(img, scale_percent=50) -> np.ndarray:
    """
    压缩图片分辨率
    
    参数:
        img: 输入图片
        scale_percent: 缩放百分比，默认50%
    返回:
        压缩后的图片
    """
    # 计算新的尺寸
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    new_dimensions = (width, height)

    # 使用 INTER_AREA 插值方法进行缩放（适合缩小图片）
    compressed_img = cv2.resize(img, new_dimensions, interpolation=cv2.INTER_AREA)

    print(f"原始尺寸: {img.shape[1]} x {img.shape[0]}")
    print(f"压缩后尺寸: {width} x {height}")

    return compressed_img


def prepare_image_for_vlm(img, max_size=768) -> np.ndarray:
    """
    为 VLM 模型准备图片 - 按长边压缩分辨率

    参数:
        img: 输入图片
        max_size: 长边最大尺寸，默认 768px
    返回:
        压缩后的图片（numpy array）
    """
    height, width = img.shape[:2]

    # 如果图片已经足够小，不需要压缩
    if max(height, width) <= max_size:
        print(f"图片尺寸 {width}x{height} 已符合要求，无需压缩")
        return img

    # 计算缩放比例（保持长边为 max_size）
    if width > height:
        scale_percent = (max_size / width) * 100
    else:
        scale_percent = (max_size / height) * 100

    # 计算新尺寸
    new_width = int(width * scale_percent / 100)
    new_height = int(height * scale_percent / 100)

    # 压缩分辨率（保持高质量）
    resized_img = cv2.resize(img, (new_width, new_height),
                             interpolation=cv2.INTER_AREA)

    print(f"VLM 压缩: {width}x{height} -> {new_width}x{new_height}")

    return resized_img


def prepare_and_save_image_for_vlm(img, output_path, max_size=768, quality=95):
    """
    为 VLM 模型准备图片并保存到文件

    参数:
        img: 输入图片
        output_path: 输出文件路径（字符串或 Path 对象）
        max_size: 长边最大尺寸，默认 768px
        quality: 保存质量（1-100），默认 95
                - JPEG: 直接使用 quality 值
                - PNG: 转换为压缩级别（0-9）
    """
    # 先压缩分辨率
    resized_img = prepare_image_for_vlm(img, max_size)

    output_path = str(output_path)

    # 根据文件格式使用不同的质量参数保存
    if output_path.lower().endswith(('.jpg', '.jpeg')):
        # JPEG 格式使用质量参数
        cv2.imwrite(output_path, resized_img,
                    [cv2.IMWRITE_JPEG_QUALITY, quality])
        print(f"已保存 JPEG 图片: {output_path}, 质量: {quality}")
    elif output_path.lower().endswith('.png'):
        # PNG 格式使用压缩级别（0-9，质量越高压缩级别越低）
        compression_level = max(0, min(9, int((100 - quality) / 10)))
        cv2.imwrite(output_path, resized_img,
                    [cv2.IMWRITE_PNG_COMPRESSION, compression_level])
        print(f"已保存 PNG 图片: {output_path}, 压缩级别: {compression_level}")
    else:
        cv2.imwrite(output_path, resized_img)
        print(f"已保存图片: {output_path}")


def main():
    """主函数"""
    # 图片路径（请修改为你的图片路径）
    cur_path = Path(__file__).parent
    image_path = cur_path / 'images' / 'image.png'

    try:
        # 1. 读取图片
        print("正在读取图片...")
        img = read_image(image_path)
        print("图片读取成功！")

        # 2. 展示原图
        print("\n展示原图（按任意键继续）...")
        show_image("original_image", img)

        # 3. 按百分比压缩图片（压缩到原来的50%）
        print("\n【方式1】按百分比压缩...")
        compressed_img = compress_image(img, scale_percent=50)
        show_image("compress_image_50%", compressed_img)

        # 4. 为 VLM 准备图片（按长边压缩到 768px）
        print("\n【方式2】为 VLM 模型准备图片...")
        vlm_img = prepare_image_for_vlm(img, max_size=768)
        show_image("vlm_ready_image", vlm_img)

        # 5. 保存 VLM 压缩后的图片
        print("\n保存 VLM 压缩图片...")
        output_path = cur_path / 'images' / 'image_vlm_compressed.jpeg'
        prepare_and_save_image_for_vlm(img, output_path, max_size=768, quality=95)

        print("\n完成！")

    except FileNotFoundError:
        print("请检查图片路径是否正确")
    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    main()
