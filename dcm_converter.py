import os
from SimpleITK import ImageSeriesReader, ResampleImageFilter, sitkLinear, WriteImage

def dcm_converter(dicom_directory, output_file):

    reader = ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(dicom_directory)
    reader.SetFileNames(dicom_names)
    image = reader.Execute()
    
    original_spacing = image.GetSpacing()
    if original_spacing[2] != 5.0:
        new_spacing = [original_spacing[0], original_spacing[1], 5.0]
        original_size = image.GetSize()

        new_size = [int(round(osz * ospc / nspc)) for osz, ospc, nspc in zip(original_size, original_spacing, new_spacing)]
    
        resampler = ResampleImageFilter()
        resampler.SetSize(new_size)
        resampler.SetOutputSpacing(new_spacing)
        resampler.SetOutputOrigin(image.GetOrigin())
        resampler.SetOutputDirection(image.GetDirection())
        resampler.SetInterpolator(sitkLinear)
        
        image = resampler.Execute(image)
    
    
    # 获取 DICOM 目录的基本名称
    base_name = os.path.basename(dicom_directory)

    # 构建输出文件名
    output_filename = f"{base_name}_0000.nii.gz"

    output_file = os.path.join(output_file, output_filename)
    WriteImage(image, output_file, True)  # True 用于保存为压缩格式(.nii.gz)
