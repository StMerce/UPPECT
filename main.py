import os
import sys
from PySide6.QtWidgets import QApplication, QFileDialog, QVBoxLayout
from qfluentwidgets import setTheme, Theme, MessageBox, IndeterminateProgressBar
from PySide6.QtCore import Qt, QThread, Signal
from ui import UPPECTUI
from autoseg import perform_prediction
from dcm_converter import dcm_converter
from bone_filling import bone_filling
from adaptive_thresholds import process_hu_values
        
class UPPECT(UPPECTUI):
    
    def __init__(self):
        super().__init__()
        
        self.Quantification_input = None
        # 连接信号和槽
        self.connect_signals()
        
    def connect_signals(self):
        # 连接 Browse 按钮
        self.input_browse.clicked.connect(self.browse_input)
        self.output_browse.clicked.connect(self.browse_output)
        
        # 连接 ComboBox
        self.hu_thresholds.currentIndexChanged.connect(self.onHuThresholdsChanged)
        self.bone_size.currentIndexChanged.connect(self.onBoneSizeChanged)
        
        # 连接 Auto segmentation 按钮
        self.auto_segmentation.clicked.connect(self.RunAutoseg)

        # 连接 Trait quantification 按钮
        self.traits_quant.clicked.connect(self.RunQuantification)
        
        # 连接 One-step prediction 按钮
        self.one_step.clicked.connect(self.RunOneStep)
    
        # 初始化 ComboBox 状态
        self.onHuThresholdsChanged(self.hu_thresholds.currentIndex())
        self.onBoneSizeChanged(self.bone_size.currentIndex())
    
    def updateHuThresholds(self, value1, value2):
        self.spinBox_1.setValue(value1)
        self.spinBox_2.setValue(value2)
        self.updateSpinBoxDisplay()
        
    def show_message_box(self, title, message):
        box = MessageBox(title, message, self)
        box.cancelButton.hide()
        box.buttonLayout.insertStretch(1)
        box.exec()
        
    def show_progress_dialog(self, message):
        self.progress_dialog = MessageBox(message, " ", self)
        bar = IndeterminateProgressBar(self.progress_dialog)
        bar.setFixedWidth(300)
        self.progress_dialog.contentLabel.setLayout(QVBoxLayout())
        self.progress_dialog.contentLabel.layout().addWidget(bar, alignment=Qt.AlignCenter)
        self.progress_dialog.yesButton.hide()
        
        self.progress_dialog.cancelButton.clicked.connect(self.terminate_thread)
        
        self.progress_dialog.buttonLayout.insertStretch(1)
        self.progress_dialog.show()
        
    def close_progress_dialog(self):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
    
    def terminate_thread(self):
        # 如果正在运行 AutoSegWorker，则调用 stop() 停止工作线程
        if hasattr(self, 'autoseg_worker') and self.autoseg_worker.isRunning():
            self.autoseg_worker.stop()
            self.show_message_box("Operation cancelled", "AutoSeg processing has been terminated.")
            self.progress_dialog.close()
        elif hasattr(self, 'quant_worker') and self.quant_worker.isRunning():
            self.quant_worker.stop()
            self.show_message_box("Operation cancelled", "Quantification processing has been terminated.")
            self.progress_dialog.close()        
        
        else:
            self.show_message_box("error", "There are no ongoing processes to cancel.")
    
    def browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if folder:
            self.input_edit.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_edit.setText(folder)
        
    def onHuThresholdsChanged(self, index):
        current_text = self.hu_thresholds.currentText()
        is_default = current_text == "Default"
        is_adaptive = current_text == "Adaptive"
        is_customize = current_text == "Customize"
        
        if is_default or is_customize:
            self.spinBox_1.setValue(-27)
            self.spinBox_2.setValue(143)
            
        elif is_adaptive:
            self.spinBox_1.setValue(self.spinBox_1.minimum() - 1)
            self.spinBox_2.setValue(self.spinBox_2.minimum() - 1)
            
        self.spinBox_1.setEnabled(is_customize)
        self.spinBox_2.setEnabled(is_customize)
            
        # 更新显示
        self.updateSpinBoxDisplay()

    def updateSpinBoxDisplay(self):
        for spinBox in [self.spinBox_1, self.spinBox_2]:
            if spinBox.value() <= spinBox.minimum():
                spinBox.setSpecialValueText(" ")  # 设置特殊值文本为空格
            else:
                spinBox.setSpecialValueText("")  # 清除特殊值文本
        
    def onBoneSizeChanged(self, index):
        current_text = self.bone_size.currentText()
        is_default = current_text == "Default"

        if is_default:
            self.spinBox_3.setValue(7)
        
        self.spinBox_3.setEnabled(not is_default)
        
    def RunAutoseg(self, onestep=False):
        input_folder = self.input_edit.text()
        output_folder = self.output_edit.text()

        if not input_folder or not output_folder:
            self.show_message_box("Invalid Directory", "Please select valid input and output directories.")
            return
        
        self.show_progress_dialog("Running AutoSeg...")
        
        # 创建并启动工作线程
        self.autoseg_worker = AutoSegWorker(input_folder, output_folder)
        if onestep:
            self.autoseg_worker.finished.connect(self.onestep_autoseg_finished)
        else:
            self.autoseg_worker.finished.connect(self.on_autoseg_finished)
        self.autoseg_worker.start()
    
    def on_autoseg_finished(self, success, message):
        self.close_progress_dialog()
        if success:
            self.show_message_box("Success", message)
        else:
            self.show_message_box("Error", message)
    
    def onestep_autoseg_finished(self, success, message):
        self.close_progress_dialog()
        self.run_quantification_after_autoseg(success, message)
        

        
    def RunQuantification(self, onestep=False):
        input_folder = self.input_edit.text()
        output_folder = self.output_edit.text()

        if not input_folder or not output_folder:
            self.show_message_box("Invalid Directory", "Please select valid input and output directories.")
            return
        
        if os.path.exists(os.path.join(output_folder, "Segmentation_out")):
            seg_dir = os.path.join(output_folder, "Segmentation_out")
        else:
            self.show_message_box("Error", "Please run segmentation before quantification.")
            return
        
        if os.path.exists(os.path.join(output_folder, "ImageReform_out")):
            image_dir = os.path.join(output_folder, "ImageReform_out")
        else:
            image_dir = input_folder
        
        self.show_progress_dialog("Running Quantification...")
          
        # 创建并启动工作线程
        self.quant_worker = QuantificationWorker(image_dir, seg_dir, self.hu_thresholds.currentText(), self.spinBox_1.value(), self.spinBox_2.value(), self.spinBox_3.value())
        self.quant_worker.finished.connect(lambda success, message: self.on_quantification_finished(success, message, onestep))
        self.quant_worker.hu_thresholds_calculated.connect(self.updateHuThresholds)

        self.quant_worker.start()

    def on_quantification_finished(self, success, message, onestep=False):
        self.close_progress_dialog()
        if success:
            if onestep:
                self.show_message_box("Success", "One-step prediction completed successfully.")
            else:    
                self.show_message_box("Success", message)
            
        else:
            self.show_message_box("Error", message)
        

    def RunOneStep(self):
        onestep = True
        self.RunAutoseg(onestep)

    def run_quantification_after_autoseg(self, success, message):
        if success:
            onestep = True
            self.RunQuantification(onestep)
        else:
            self.show_message_box("Error", "AutoSeg failed. One-step process stopped.\n" + message)



class AutoSegWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, input_folder, output_folder):
        super().__init__()
        
        input_folder = os.path.normpath(input_folder)
        output_folder = os.path.normpath(output_folder)
        
        self.input_folder = input_folder
        self.output_folder = output_folder

    def run(self):
        try:
            # 这里放置原来 RunAutoseg 方法中的主要逻辑
            nii_files = [f for f in os.listdir(self.input_folder) if f.endswith('.nii.gz')]
            subdirs = [d for d in os.listdir(self.input_folder) if os.path.isdir(os.path.join(self.input_folder, d))]

            if nii_files and not subdirs:
                perform_prediction(self.input_folder, self.output_folder)
                self.finished.emit(True, "AutoSeg completed successfully.")
                
            elif subdirs and not nii_files:
                # 只有文件夹，先转换
                nii_output_path = os.path.join(self.output_folder, "ImageReform_out")
                os.makedirs(nii_output_path, exist_ok=True)
                for individual_folder in subdirs:
                    individual_path = os.path.join(self.input_folder, individual_folder)
                    dcm_converter(individual_path, nii_output_path)
                    
                perform_prediction(nii_output_path, self.output_folder)
                self.finished.emit(True, "DICOM conversion and AutoSeg completed successfully.")
                
            elif nii_files and subdirs:
                self.finished.emit(False, "The input directory contains both nii.gz files and folders, please select only one type of images.")
            
            else:
                self.finished.emit(False, "The input directory does not contain valid nii.gz files or subfolders.")
        
        except Exception as e:
            self.finished.emit(False, str(e))

    def stop(self):
        self.terminate()
        self.wait()
        print("AutoSeg has stopped.")
        
class QuantificationWorker(QThread):
    finished = Signal(bool, str)
    hu_thresholds_calculated = Signal(int, int)
    
    def __init__(self, image_dir, seg_dir, hu_threshold_type, spinbox1_value, spinbox2_value, spinbox3_value):
        super().__init__()
        
        image_dir = os.path.normpath(image_dir)
        seg_dir = os.path.normpath(seg_dir)
        
        self.image_dir = image_dir
        self.seg_dir = seg_dir
        self.hu_threshold_type = hu_threshold_type
        self.spinbox1_value = spinbox1_value
        self.spinbox2_value = spinbox2_value
        self.spinbox3_value = spinbox3_value

    def run(self):
        try:
            if self.hu_threshold_type == "Adaptive":
                
                intersection1, intersection2 = process_hu_values(self.image_dir, self.seg_dir)

                # 设置 spinBox 的值
                self.hu_thresholds_calculated.emit(round(intersection1), round(intersection2))
            
            bone_filling(self.image_dir, self.seg_dir, self.spinbox1_value, self.spinbox2_value, self.spinbox3_value)
            self.finished.emit(True, "Quantification completed successfully.")
        except Exception as e:
            self.finished.emit(False, str(e))
            
    def stop(self):
        self.terminate()
        self.wait()
        print("Quantification has stopped.")

if __name__ == '__main__':
    app = QApplication([])
    setTheme(Theme.LIGHT)
    window = UPPECT()
    window.show()
    app.exec()

