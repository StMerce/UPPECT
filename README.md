<p align="center">
  <img width="18%" align="center" src="https://github.com/StMerce/UPPECT/blob/main/img/UPPECT_logo_white.png" alt="logo">
</p>
<p align="center">
  nnU-Net-based Pig Phenome Evaluation by CT
</p>

---

## 👋 Welcome to UPPECT! 

UPPECT is your go-to tool for automatic carcass segmentation and composition quantification of live pigs using CT images. 

Powered by nnU-Net, UPPECT has been trained on a massive dataset of 10,676 CT images from 50 pigs to automatically segment three different cuts of pig carcasses. After segmentation, UPPECT can classify and quantify fat, lean and bone, enabling accurate prediction of 15 carcass segmentation and composition (CSC) traits.

UPPECT enables non-invasive and precise measurement of CSC traits of live pigs, which can make an important contribution to the breeding practice.

<p align="center">
  <img width="80%" align="center" src="https://github.com/StMerce/UPPECT/blob/main/img/Github_Graphical_abstract.png" alt="Graphical_abstract">
</p>

## 🚀 Getting Started with UPPECT

UPPECT is a Windows desktop application. Before you start, make sure you meet the [hardware requirements for inference](https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/installation_instructions.md) of nnU-Net.

<p align="center">
  <img width="80%" align="center" src="https://github.com/StMerce/UPPECT/blob/main/img/GUI.png">
</p>

### 🛠️ Setting Up Your Environment

Please install the latest [PyTorch](https://pytorch.org/get-started/locally/) compatible with your CUDA version.

### 📥Get UPPECT

 Run `git clone https://github.com/StMerce/UPPECT.git` to get UPPECT, and then run `python main.py` to use it.

### 📁 Organizing Your Input Data

UPPECT supports two types of CT image formats:

1. **DICOM Files(`.dcm`):**
   * Create a separate folder for each pig's .dcm files.
   * Put all these folders in your input directory.
   
   like this:

```
input_directory
    ├── pig_1
    │   ├── pig_1_001.dcm
    │   ├── pig_1_002.dcm
    │   ├── pig_1_003.dcm
    │   └── ...
    ├── pig_2
    │   ├── pig_2_001.dcm
    │   ├── pig_2_002.dcm
    │   ├── pig_2_003.dcm
    │   └── ...
    ├── ...
```

2. **(Recommended) NIfTI Files (`.nii.gz`)  :**
   * One `.nii.gz` file per pig.
   * All files go directly in the input directory.
   
   like this:

```
input_directory
    ├── pig_1.nii.gz
    ├── pig_2.nii.gz
    ├── pig_3.nii.gz
    ├── ...
```

### 📂 Setting Up Your Output

Choose a spot for your output directory. This is where all of UPPECT's results will land.

### 🏃‍♂️ Running Predictions

Before starting the prediction process, make sure you've set up both the input and output directories. UPPECT offers two ways to run predictions:

1. **One-step prediction:** UPPECT offers a streamlined process that performs segmentation and quantification in a single step. Click on the `One-Step Prediction` button and then just wait patiently ;-)
2. **Two-step prediction:** If you prefer, you can perform segmentation and quantification separately. This allows you to check the segmentation mask before moving on to quantification.

Choose what works best for you. If you want to verify interim results, the two-step approach might be preferable. In general, the one-step prediction is ideal to speed up the process.

### 🔧(Optional) Parameter fine-tuning

You can modify certain parameters in the trait quantification process to potentially make UPPECT more suitable for your CT images. This step is optional and our optimal parameters will be used by default. There are two sets of parameters you can modify:

1. **HU Thresholds:** These help distinguish between fat, lean meat, and bone structure. 

   * `Default`: -27 and 143 (based on our dataset).

   - `Adaptive Thresholds`: Let UPPECT figure it out based on your images.
   - `Custom`: Set your thresholds manually.

2. **Bone Filling:** This fills in hollow areas in bones, representing the size of the structural element.

   * `Default`: 7.
   * `Custom`: Set the size manually

   **Tip: Best to leave this alone unless you're not happy with how bones look in your results after checking the segmentation mask.**

Remember, these tweaks are totally optional. When in doubt, the defaults have got your back!



### Happy UPPECTing! 🐷✨
