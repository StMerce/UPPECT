import os
import numpy as np
from SimpleITK import ReadImage, GetArrayFromImage, GetImageFromArray, WriteImage
from scipy import ndimage as ndi
from pandas import DataFrame
from skimage.morphology import remove_small_objects

def create_ellipsoid_structure(radius_x, radius_y, radius_z):
    Lx, Ly, Lz = np.ceil(radius_x).astype(int), np.ceil(radius_y).astype(int), np.ceil(radius_z).astype(int)
    grid = np.ogrid[-Lx:Lx+1, -Ly:Ly+1, -Lz:Lz+1]
    ellipsoid = (grid[0]**2 / radius_x**2 + grid[1]**2 / radius_y**2 + grid[2]**2 / radius_z**2) <= 1
    return ellipsoid

def bone_filling(image_dir, seg_dir, threshold_1, threshold_2, radius):
    
    quantification_dir = os.path.join(os.path.dirname(seg_dir), 'Quantification_out')
    os.makedirs(quantification_dir, exist_ok=True)
    
    threshold_value = (-200, threshold_1, threshold_2, 1501)
    # threshold_value = (-200, 0, 201, 1501)
    # densitys = (0.92, 1.06, 1.4)
    weights = []

    image_files = sorted([file for file in os.listdir(image_dir) if file.endswith('.nii.gz')])
    seg_files = sorted([file for file in os.listdir(seg_dir) if file.endswith('.nii.gz')])
    
    for image_file, seg_file in zip(image_files, seg_files):
        # 读取图像和分割数据
        itk_image = ReadImage(os.path.join(image_dir, image_file))
        npy_image = GetArrayFromImage(itk_image)
        itk_segmentation = ReadImage(os.path.join(seg_dir, seg_file))
        npy_segmentation = GetArrayFromImage(itk_segmentation)
        
        #阈值
        npy_segmentation[npy_image < threshold_value[0]] = 0
        npy_segmentation[npy_image >= threshold_value[3]] = 0
        
        # 给npy_segmentation增加一个维度
        npy_segmentation = np.expand_dims(npy_segmentation, axis=-1)
        npy_segmentation = np.concatenate((npy_segmentation, np.zeros_like(npy_segmentation)), axis=-1)

        # 根据条件赋值
        npy_segmentation[..., 1] = np.where(npy_segmentation[..., 0] == 0, 0, 1)

        # 对第二个通道进行操作
        # 1. 阈值处理
        foreground_mask = npy_segmentation[..., 1] == 1
        foreground_pixels = npy_image[foreground_mask]
        bone_mask = foreground_pixels >= threshold_value[2]
        npy_segmentation[..., 1][foreground_mask] = np.where(bone_mask, 3, npy_segmentation[..., 1][foreground_mask])

        # 2. 过滤小岛
        filtered_segmentation = remove_small_objects(npy_segmentation[..., 1] == 3, min_size=64)

        # 3. 膨胀和腐蚀
        depth_structuring_element = create_ellipsoid_structure(radius_x=1.5, radius_y=0.5, radius_z=0.5)
        
        radius = radius-0.5
        height_width_structuring_element = create_ellipsoid_structure(radius_x=0.5, radius_y=radius  , radius_z=radius)

        dilated_depth = ndi.binary_dilation(filtered_segmentation, structure=depth_structuring_element)
        dilated_final = ndi.binary_dilation(dilated_depth, structure=height_width_structuring_element)
        eroded_depth = ndi.binary_erosion(dilated_final, structure=depth_structuring_element)
        eroded_final = ndi.binary_erosion(eroded_depth, structure=height_width_structuring_element)

        npy_segmentation[..., 1] = np.where(eroded_final, 3, 1)
        npy_segmentation[..., 1] = np.where(npy_segmentation[..., 0] == 0, 0, npy_segmentation[..., 1])

        # 4. 保留肌肉和脂肪的最大岛
        label_of_interest = 1
        binary_image = (npy_segmentation[..., 1] == label_of_interest)
        labeled_image, num_features = ndi.label(binary_image)
        sizes = ndi.sum(binary_image, labeled_image, range(num_features + 1))
        max_label = np.argmax(sizes[1:]) + 1
        largest_island = (labeled_image == max_label)
        npy_segmentation[..., 1] = np.where(largest_island, label_of_interest, 3)
        npy_segmentation[..., 1] = np.where(npy_segmentation[..., 0] == 0, 0, npy_segmentation[..., 1])

        # 5. 阈值分割肌肉和脂肪
        fat_lean_mask = npy_segmentation[..., 1] == 1
        fat_lean_pixels = npy_image[fat_lean_mask]
        lean_mask = fat_lean_pixels >= threshold_value[1]
        npy_segmentation[..., 1][fat_lean_mask] = np.where(lean_mask, 2, npy_segmentation[..., 1][fat_lean_mask])
        
        # 输出量化label
        quantification = GetImageFromArray(npy_segmentation[..., 1])
        quantification.CopyInformation(itk_segmentation)

        # 构造输出文件名
        output_filename = f"q_{seg_file}"
        output_path = os.path.join(quantification_dir, output_filename)

        # 保存处理后的label为新的 .nii.gz 文件
        WriteImage(quantification, output_path)
        
        # 计算单个体素的体积
        voxel_size = np.array(itk_image.GetSpacing())
        voxel_volume = np.prod(voxel_size)
        
        row = [None] * 31
        row[0] = image_file.replace('.nii.gz', '')  # 将文件名去除末尾的“.nii.gz”并添加到第一列
        index_1 = 7  # 从第8个位置开始（索引从0开始，所以是7）
        index_2 = 1  # 从第2个位置开始（索引从0开始，所以是1）
        for channel1_value in range(1, 4):
            part_weight = 0
            for channel2_value in range(1, 4):
                mask = (npy_segmentation[..., 0] == channel1_value) & (npy_segmentation[..., 1] == channel2_value)
                num = np.sum(mask)
                volume = num * voxel_volume
                mean_hu = np.mean(npy_image[mask])
                
                
                weight = volume * (mean_hu * 0.001009 + 1.003424) / 1000000
                row[index_1] = weight
                part_weight += weight
                index_1 += 1
                
            row[index_2] = part_weight    
            index_2 += 1  

        for index_2 in range(4, 7):
            composition = row[index_2 + 3] + row[index_2 + 6] + row[index_2 + 9]
            row[index_2] = composition
            
        for index_3 in range(0, 5):
            for index_4 in range(1, 4):
                percentage = row[index_3*3 + index_4] / (row[index_3*3 + 1]+row[index_3*3 + 2]+row[index_3*3 + 3]) * 100
                row[index_3*3 + index_4 + 15] = percentage
            
        weights.append(row)

    # 将二维数组转换为 DataFrame
    columns = ["ID", "前段重", "中段重", "后段重", 
            "脂肪重", "瘦肉重", "骨重", 
            "前段脂肪重", "前段瘦肉重", "前段骨重", 
            "中段脂肪重", "中段瘦肉重", "中段骨重", 
            "后段脂肪重", "后段瘦肉重", "后段骨重", 
            "前段比", "中段比", "后段比", 
            "脂肪率", "瘦肉率", "骨率", 
            "前段脂肪率", "前段瘦肉率", "前段骨率", 
            "中段脂肪率", "中段瘦肉率", "中段骨率", 
            "后段脂肪率", "后段瘦肉率", "后段骨率"]
    traits = DataFrame(weights, columns=columns)

    # 将 DataFrame 写入 Excel 文件
    parent_dir = os.path.dirname(seg_dir)
    output_file = os.path.join(parent_dir, 'Prediction_result.xlsx')
    traits.to_excel(output_file, index=False)