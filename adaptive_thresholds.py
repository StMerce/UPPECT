import os
import numpy as np
from SimpleITK import GetArrayFromImage, ReadImage
from pandas import DataFrame, ExcelWriter
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit, fsolve, minimize
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy.stats import skewnorm

class HU_statistics:   
    def __init__(self, bin_edges):
        self.bin_edges = bin_edges
        self.histogram_per_channel = [np.zeros(len(bin_edges) - 1, dtype=np.int64) for _ in range(3)]
        self.df = None

    def collect_foreground_statistics(self, segmentation: np.ndarray, images: np.ndarray):
        for i in range(1, 4):
            foreground_mask = segmentation == i
            foreground_pixels = np.round(images[foreground_mask])
            self.histogram_per_channel[i-1] += np.histogram(foreground_pixels, bins=self.bin_edges)[0]

    def get_density_data(self):
        return [(self.bin_edges[:-1], histogram) for histogram in self.histogram_per_channel]

    def save_to_excel(self, output_file):
        density_data = self.get_density_data()
        df = DataFrame({'Edges': density_data[0][0]})
        for i, data in enumerate(density_data):
            df[f'Foreground {i+1}'] = data[1]
        df['Sum'] = df.iloc[:, 1:].sum(axis=1)
        
        with ExcelWriter(output_file) as writer:
            df.to_excel(writer, sheet_name='Histogram Data', index=False)
        
        self.df = df

    def skew_normal(self, x, a, e, w, c):
        return c * skewnorm.pdf(x, a, loc=e, scale=w)

    def find_peak(self, params, x_range):
        objective = lambda x: -self.skew_normal(x, *params)
        result = minimize(objective, x0=np.mean(x_range), bounds=[(x_range[0], x_range[1])])
        if result.success:
            return result.x[0]
        else:
            raise ValueError("Optimization failed to find the peak.")

    def analyze_and_plot(self, output_figure):
        if self.df is None:
            raise ValueError("Data not loaded. Run save_to_excel first.")

        x = self.df.iloc[:, 0].values
        y = self.df.iloc[:, 4].values

        mask1 = (x >= -200) & (x <= -60)
        mask2a = (x >= -10) & (x <= 80)
        mask2b = (x >= 70) & (x <= 150)
        mask3 = (x >= 200) & (x <= 400)

        max_y1 = y[mask1].max()
        max_x1 = x[mask1][y[mask1].argmax()]
        max_y2 = y[mask2a].max()
        max_x2 = x[mask2a][y[mask2a].argmax()]
        max_y3 = y[mask3].max()
        max_x3 = x[mask3][y[mask3].argmax()]
        max_y2b = y[mask2b].max()
        max_x2b = x[mask2b][y[mask2b].argmax()]

        p0 = [1, max_x1, 30, max_y1]
        params1, _ = curve_fit(self.skew_normal, x[mask1], y[mask1], p0=p0, maxfev=15000)
        p0 = [1, max_x2, 30, max_y2]
        params2a, _ = curve_fit(self.skew_normal, x[mask2a], y[mask2a], p0=p0, maxfev=15000)
        p0 = [1, max_x2b, 30, max_y2b]
        params2b, _ = curve_fit(self.skew_normal, x[mask2b], y[mask2b], p0=p0, maxfev=150000)
        p0 = [1, max_x3, 300, max_y3]
        params3, _ = curve_fit(self.skew_normal, x[mask3], y[mask3], p0=p0, maxfev=15000)

        peak1 = self.find_peak(params1, (-200, -60))
        peak2a = self.find_peak(params2a, (-10, 150))
        peak3 = self.find_peak(params3, (180, 400))

        combined_func = lambda x: (self.skew_normal(x, *params1) + 
                                   self.skew_normal(x, *params2a) * (x <= 75) + 
                                   self.skew_normal(x, *params2b) * (x > 75) + 
                                   self.skew_normal(x, *params3))
        residuals = y - combined_func(x)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))** 2)
        r2 = 1 - (ss_res / ss_tot)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim(-200, 500)
        ax.plot(x, y, '-', color='grey', markersize=1, label='Original Data')

        x_fit1 = np.linspace(-200,50)
        y_fit1 = self.skew_normal(x_fit1, *params1)
        ax.plot(x_fit1, y_fit1, '--', label='Distribution 1')

        x_fit2a = np.linspace(-90, 70)
        y_fit2a = self.skew_normal(x_fit2a, *params2a)
        ax.plot(x_fit2a, y_fit2a, 'g--', label='Distribution 2a')

        x_fit2b = np.linspace(70, 180)
        y_fit2b = self.skew_normal(x_fit2b, *params2b)
        ax.plot(x_fit2b, y_fit2b, 'g--', label='Distribution 2b')

        x_fit3 = np.linspace(100, 500)
        y_fit3 = self.skew_normal(x_fit3, *params3)
        ax.plot(x_fit3, y_fit3, '--', label='Distribution 3')

        axins = inset_axes(ax, width="30%", height="40%", loc=1)
        axins.plot(x, y, '-', color='grey', markersize=1)
        axins.plot(x_fit1, y_fit1, '--')
        axins.plot(x_fit2a, y_fit2a, 'g-')
        axins.plot(x_fit2b, y_fit2b, 'g--')
        axins.plot(x_fit3, y_fit3, '--')

        axins.set_xlim(50, 300)
        axins.set_ylim(0, max_y3 * 4)

        axins.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

        func1 = lambda x: self.skew_normal(x, *params1)
        func2a = lambda x: self.skew_normal(x, *params2a)
        intersection1, = fsolve(lambda x: func1(x) - func2a(x), -20)

        func2b = lambda x: self.skew_normal(x, *params2b)
        func3 = lambda x: self.skew_normal(x, *params3)
        intersection2, = fsolve(lambda x: func2b(x) - func3(x), 100)

        txt_file = os.path.join(os.path.dirname(output_figure), 'fitting_results.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f'R²: {r2:.6f}\n')
            f.write(f"Peak of fat: HU = {round(peak1)}\n")
            f.write(f"Peak of lean meat: HU = {round(peak2a)}\n")
            f.write(f"Peak of bone: HU = {round(peak3)}\n")
            f.write(f"Threshold between fat and lean meat: HU = {round(intersection1)}\n")
            f.write(f"Threshold between lean meat and bone: HU = {round(intersection2)}\n")

        ax.set_xlabel("HU Value")
        ax.set_ylabel("Voxel count")

        plt.savefig(output_figure, format='pdf')
        
        return (intersection1, intersection2, r2, peak1, peak2a, peak3)

def process_hu_values(image_dir, seg_dir):
    bin_edges = np.arange(-1000, 2002, 1)
    statistics = HU_statistics(bin_edges)

    quantification_dir = os.path.join(os.path.dirname(seg_dir), 'Quantification_out')
    os.makedirs(quantification_dir, exist_ok=True)

    image_files = sorted([os.path.join(image_dir, file) for file in os.listdir(image_dir) if file.endswith('.nii.gz')])
    seg_dir = sorted([os.path.join(seg_dir, file) for file in os.listdir(seg_dir) if file.endswith('.nii.gz')])

    for image_file, segmentation_file in zip(image_files, seg_dir):
        itk_image = ReadImage(image_file)
        npy_image = GetArrayFromImage(itk_image)
        itk_segmentation = ReadImage(segmentation_file)
        npy_segmentation = GetArrayFromImage(itk_segmentation)

        statistics.collect_foreground_statistics(npy_segmentation, npy_image)
    
    output_file = os.path.join(quantification_dir, 'FDHU.xlsx')
    output_figure = os.path.join(quantification_dir, 'Adaptive_threshold.pdf')
    
    statistics.save_to_excel(output_file)
    
    results = statistics.analyze_and_plot(output_figure)

    return results[0], results[1]



