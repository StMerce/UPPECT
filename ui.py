import os
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QMainWindow, QFrame, QSizePolicy
from qfluentwidgets import TransparentPushButton, PushButton, ComboBox, LineEdit, SpinBox, PrimaryPushButton, CardWidget
from qfluentwidgets import FluentIcon as FIF
from PySide6.QtGui import QPixmap, QFont, QIcon
from PySide6.QtCore import Qt

class UPPECTUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建字体对象
        self.font = QFont("Arial", 12, QFont.Bold)
        
        # 设置窗口标题和大小
        self.setFixedSize(900, 530)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, 'img', 'UPPECT_pig.png')
        self.setWindowIcon(QIcon(icon_path))
        
        self.setWindowTitle('UPPECT')
        
        # 创建整体布局
        self.main_layout = QVBoxLayout()
        
        self.setup_header()
        self.setup_content()
        self.setup_buttons()
        
        # 设置窗口的中央 widget
        central_widget = QWidget(self)
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def setup_header(self):
        # 顶部区域带有背景颜色 #bdd7ee
        header_frame = QFrame(self)
        header_frame.setStyleSheet("background-color: #bdd7ee; border-radius: 8px;")
        header_frame.setFixedHeight(180)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignCenter)

        header_content_layout = QHBoxLayout()
        header_content_layout.setSpacing(20)

        profile_pic = QLabel(self)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, 'img', 'UPPECT_logo_white.png')
        pixmap = QPixmap(logo_path)  
        pixmap = pixmap.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        profile_pic.setPixmap(pixmap)
        profile_pic.setFixedSize(130, 130)

        name_label = QLabel("nnU-Net-based Pig Phenome Evaluation by CT", self)
        name_label.setFont(QFont("Arial", 20, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)

        header_content_layout.addWidget(profile_pic)
        header_content_layout.addWidget(name_label)

        header_layout.addLayout(header_content_layout)
        self.main_layout.addWidget(header_frame)

    def setup_content(self):
        content_frame = QFrame(self)
        content_frame.setStyleSheet("background-color: #f0f4f9;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addSpacing(10)
        
        self.setup_directory_card(content_layout)
        self.setup_hu_bone_cards(content_layout)
        
        self.main_layout.addWidget(content_frame)

    def setup_directory_card(self, content_layout):
        directory_card_widget = CardWidget(self)
        directory_card_layout = QVBoxLayout(directory_card_widget) 
        directory_card_layout.addSpacing(10)
        
        self.setup_input_directory(directory_card_layout)
        self.setup_output_directory(directory_card_layout)
        
        content_layout.addWidget(directory_card_widget)
        content_layout.addSpacing(10)

    def setup_input_directory(self, layout):
        input_label = QLabel("Input directory:", self)
        input_label.setFont(self.font)
        input_label.setStyleSheet("background-color: transparent;")
        self.input_edit = LineEdit(self)
        self.input_edit.setReadOnly(True)  # 设置为只读
        self.input_browse = PrimaryPushButton('Browse', self)
        self.input_browse.setFont(QFont("Arial", 10, QFont.Bold))
        self.input_browse.setMaximumHeight(30)

        input_box_layout = QHBoxLayout()
        input_box_layout.addWidget(self.input_edit)
        input_box_layout.addWidget(self.input_browse)
        layout.addWidget(input_label)
        layout.addLayout(input_box_layout)
        layout.addSpacing(10)

    def setup_output_directory(self, layout):
        output_label = QLabel("Output directory:", self)
        output_label.setFont(self.font)
        output_label.setStyleSheet("background-color: transparent;")
        self.output_edit = LineEdit(self)
        self.output_edit.setReadOnly(True)
        self.output_browse = PrimaryPushButton('Browse', self)
        self.output_browse.setFont(QFont("Arial", 10, QFont.Bold))
        self.output_browse.setMaximumHeight(30)

        output_box_layout = QHBoxLayout()
        output_box_layout.addWidget(self.output_edit)
        output_box_layout.addWidget(self.output_browse)
        layout.addWidget(output_label)
        layout.addLayout(output_box_layout)

    def setup_hu_bone_cards(self, content_layout):
        card_layout_container = QHBoxLayout()
        
        self.setup_hu_thresholds_card(card_layout_container)
        self.setup_bone_filling_card(card_layout_container)
        
        content_layout.addLayout(card_layout_container)
        content_layout.addSpacing(10)

    def setup_hu_thresholds_card(self, container):
        card_widget = CardWidget(self)
        card_layout_v = QVBoxLayout(card_widget)
        card_layout = QHBoxLayout()

        spin_layout = QHBoxLayout()
        
        self.spinBox_1 = SpinBox()
        self.spinBox_1.setAccelerated(True)
        self.spinBox_1.setMinimum(-100)
        self.spinBox_1.setMaximum(100)
        self.spinBox_1.setValue(-27)
        
        self.spinBox_2 = SpinBox()
        self.spinBox_2.setAccelerated(True)
        self.spinBox_2.setMinimum(100)
        self.spinBox_2.setMaximum(300)
        self.spinBox_2.setValue(143)
        
        spin_layout.addWidget(self.spinBox_1)
        spin_layout.addWidget(self.spinBox_2)
        
        self.hu_button = TransparentPushButton(FIF.LIBRARY, "HU thresholds", self)
        self.hu_button.setFont(self.font)
        self.hu_thresholds = ComboBox(self)
        self.hu_thresholds.addItems(["Default", "Adaptive", "Customize"])
        
        card_layout.addWidget(self.hu_button)
        card_layout.addWidget(self.hu_thresholds)
        
        card_layout_v.addLayout(card_layout)
        card_layout_v.addLayout(spin_layout)
        
        card_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        container.addWidget(card_widget)

    def setup_bone_filling_card(self, container):
        card_widget = CardWidget(self)
        card_layout_v = QVBoxLayout(card_widget)
        card_layout = QHBoxLayout()
        
        spin_layout = QHBoxLayout()
        
        self.tran = QLabel(self)
        self.tran.setStyleSheet("background-color: transparent;")
        
        self.spinBox_3 = SpinBox()
        self.spinBox_3.setAccelerated(True)
        self.spinBox_3.setMinimum(0)
        self.spinBox_3.setMaximum(20)
        self.spinBox_3.setValue(7)
        
        spin_layout.addWidget(self.tran)
        spin_layout.addWidget(self.spinBox_3)
        
        self.bone_button = TransparentPushButton(FIF.MOVE, "Bone filling size", self)
        self.bone_button.setFont(self.font)
        self.bone_size = ComboBox(self)
        self.bone_size.addItems(["Default", "Customize"])
        
        card_layout.addWidget(self.bone_button)
        card_layout.addWidget(self.bone_size)
        
        card_layout_v.addLayout(card_layout)
        card_layout_v.addLayout(spin_layout)
        
        card_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        container.addWidget(card_widget)

    def setup_buttons(self):
        button_layout = QHBoxLayout()

        self.auto_segmentation = PushButton("Automatic segmentation", self)
        self.auto_segmentation.setFont(self.font)
        self.traits_quant = PushButton("Traits quantification", self)
        self.traits_quant.setFont(self.font)
        self.one_step = PrimaryPushButton("One-step prediction", self)
        self.one_step.setFont(self.font)
        
        for button in [self.auto_segmentation, self.traits_quant, self.one_step]:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            button.setMaximumHeight(50)
            button_layout.addWidget(button)

        self.main_layout.addLayout(button_layout)
