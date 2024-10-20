import os
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
import torch
from nnunetv2.paths import nnUNet_results

def perform_prediction(input_folder, output_folder):
    
    new_output_folder = os.path.join(output_folder, "seg_nii")
    os.makedirs(new_output_folder, exist_ok=True)
    
    predictor = nnUNetPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=True,
        perform_everything_on_device=True,
        device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'),
        verbose=False,
        verbose_preprocessing=False,
        allow_tqdm=True
    )
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'model')
    
    predictor.initialize_from_trained_model_folder(
        model_path,
        use_folds=('all',),
        checkpoint_name='checkpoint_final.pth',
    )
    
    predictor.predict_from_files(
        input_folder,
        new_output_folder,
        save_probabilities=False,
        overwrite=True,
        num_processes_preprocessing=3,
        num_processes_segmentation_export=3,
        folder_with_segs_from_prev_stage=None,
        num_parts=1,
        part_id=0
    )
