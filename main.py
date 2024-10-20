import os
import sys
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget
from qfluentwidgets import setTheme, Theme, MessageBox
from PySide6.QtCore import Qt, QThread, Signal
from ui import UPPECTUI
from autoseg import perform_prediction
from dcm_converter import dcm_converter



class UPPECT(UPPECTUI):
    def __init__(self):
        super().__init__()
        
        # 连接信号和槽
        self.connect_signals()

    def connect_signals(self):
        # 连接 Browse 按钮
        self.input_browse.clicked.connect(self.browse_input)
        self.output_browse.clicked.connect(self.browse_output)
        
        # 连接 ComboBox
        self.hu_thresholds.currentIndexChanged.connect(self.onHuThresholdsChanged)
        self.bone_size.currentIndexChanged.connect(self.onBoneSizeChanged)
        
        # 链接 Auto segmentation 按钮
        self.auto_segmentation.clicked.connect(self.RunAutoseg)
    
        # 初始化 ComboBox 状态
        self.onHuThresholdsChanged(self.hu_thresholds.currentIndex())
        self.onBoneSizeChanged(self.bone_size.currentIndex())

    def browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if folder:
            self.input_edit.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_edit.setText(folder)

    def onHuThresholdsChanged(self, index):
        is_default = self.hu_thresholds.currentText() == "Default"
        self.spinBox_1.setEnabled(not is_default)
        self.spinBox_2.setEnabled(not is_default)

    def onBoneSizeChanged(self, index):
        is_default = self.bone_size.currentText() == "Default"
        self.spinBox_3.setEnabled(not is_default)
        
    def RunAutoseg(self):
        input_folder = self.input_edit.text()
        output_folder = self.output_edit.text()

        if not input_folder or not output_folder:
            w = MessageBox("路径无效", "请输入有效的DICOM目录和输出路径。", window)
            w.cancelButton.hide()
            w.buttonLayout.insertStretch(1)
            w.exec()
            return
        
        # 检查输入目录的内容
        input_folder = os.path.normpath(input_folder)
        output_folder = os.path.normpath(output_folder)
        nii_files = [f for f in os.listdir(input_folder) if f.endswith('.nii.gz')]
        subdirs = [d for d in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, d))]

        if nii_files and not subdirs:
            # 只有 nii.gz 文件，直接autoseg
            perform_prediction(input_folder, output_folder)
            
        elif subdirs and not nii_files:
            # 只有文件夹，先转换
            nii_output_path = os.path.join(output_folder, "img_nii")
            os.makedirs(nii_output_path, exist_ok=True)
            for individual_folder in subdirs:
                individual_path = os.path.join(input_folder, individual_folder)
                dcm_converter(individual_path, nii_output_path)
                
            perform_prediction(nii_output_path, output_folder)
            
        elif nii_files and subdirs:
            # 既有 nii.gz 文件又有文件夹
            w = MessageBox("非法内容", "输入目录同时包含 nii.gz 文件和文件夹，请只选择一种类型的内容。", window)
            w.cancelButton.hide()
            w.buttonLayout.insertStretch(1)
            w.exec()
            return
        
        else:
            # 其他非法情况
            w = MessageBox("非法内容", "输入目录不包含有效的 nii.gz 文件或子文件夹。", window)
            w.cancelButton.hide()
            w.buttonLayout.insertStretch(1)
            w.exec()
            return            

if __name__ == '__main__':
    app = QApplication([])
    setTheme(Theme.LIGHT)
    window = UPPECT()
    window.show()
    app.exec()
