import subprocess
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import os, glob, cv2
from scipy import ndimage
import skimage.measure
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ================= nnUNet PATHS =================
os.environ["nnUNet_raw"] = os.path.join(BASE_DIR, "nnUNet_raw")
os.environ["nnUNet_preprocessed"] = os.path.join(BASE_DIR, "nnUNet_preprocessed")
os.environ["nnUNet_results"] = os.path.join(BASE_DIR, "nnUNet_results")

INPUT_DIR = os.path.join(BASE_DIR, "static", "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "output_case012")
CHECKPOINT = os.path.join(BASE_DIR, "checkpoint_best.pth")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= READ INPUT IMAGE =================
with open("file.txt", "r") as f:
    INPUT_IMAGE = f.read().strip()

print("Running nnU-Net inference...")

# ================= RUN nnUNet =================
subprocess.check_call([
    "nnUNetv2_predict",
    "-i", INPUT_DIR,
    "-o", OUTPUT_DIR,
    "-d", "0",
    "-c", "3d_fullres",
    "-f", "0",
    "-device", "cpu",
    "-chk", CHECKPOINT
])

# ================= LOAD PREDICTION =================
pred_file = glob.glob(os.path.join(OUTPUT_DIR, "*.nii*"))[0]
pred_img = nib.load(pred_file)
pred = pred_img.get_fdata()
spacing = pred_img.header.get_zooms()[:3]

ct_img = nib.load(INPUT_IMAGE)
ct = ct_img.get_fdata()

mask = (pred > 0).astype(np.uint8)

# ================= METRICS =================
voxel_count = int(mask.sum())
voxel_volume_mm3 = spacing[0] * spacing[1] * spacing[2]
volume_mm3 = voxel_count * voxel_volume_mm3
# ================= TUMOR SIZE CALCULATION =================
coords = np.where(mask > 0)

if len(coords[0]) > 0:
    x_min, x_max = coords[0].min(), coords[0].max()
    y_min, y_max = coords[1].min(), coords[1].max()
    z_min, z_max = coords[2].min(), coords[2].max()

    tumor_size_x_mm = (x_max - x_min + 1) * spacing[0]
    tumor_size_y_mm = (y_max - y_min + 1) * spacing[1]
    tumor_size_z_mm = (z_max - z_min + 1) * spacing[2]

    tumor_max_diameter_mm = max(
        tumor_size_x_mm,
        tumor_size_y_mm,
        tumor_size_z_mm
    )
else:
    tumor_size_x_mm = tumor_size_y_mm = tumor_size_z_mm = tumor_max_diameter_mm = 0

# ================= FIND BEST TUMOR SLICE =================
tumor_slices = np.where(mask.sum(axis=(0,1)) > 0)[0]
z = int(tumor_slices[len(tumor_slices)//2]) if len(tumor_slices) > 0 else mask.shape[2]//2

# ======================================================
# OVERLAY → CT + LIGHT RED FILL + RED BOUNDARY
# ======================================================
plt.figure(figsize=(6,6))
plt.imshow(ct[:,:,z], cmap="gray")

# light fill
plt.imshow(
    np.ma.masked_where(mask[:,:,z] == 0, mask[:,:,z]),
    cmap="Reds",
    alpha=0.25
)

# boundary
contours = skimage.measure.find_contours(mask[:,:,z], 0.5)
for cnt in contours:
    plt.plot(cnt[:,1], cnt[:,0], color="red", linewidth=2)

plt.axis("off")
plt.savefig(os.path.join(OUTPUT_DIR, "overlay.png"), dpi=200, bbox_inches="tight")
plt.close()

# ================= SEGMENTATION (CT + FILLED MASK) =================
# ================= SEGMENTATION (MASK ONLY – NO CT) =================
seg_mask = (mask[:, :, z] * 255).astype(np.uint8)

plt.figure(figsize=(6,6))
plt.imshow(seg_mask, cmap="gray")   # or cmap="Blues"
plt.axis("off")

plt.savefig(
    os.path.join(OUTPUT_DIR, "segmentation.png"),
    dpi=200,
    bbox_inches="tight"
)
plt.close()




# ======================================================
# HEATMAP (XAI) → CT + ATTENTION
# ======================================================
dist = ndimage.distance_transform_edt(mask[:,:,z])
if dist.max() > 0:
    dist = dist / dist.max()

ct_slice = ct[:,:,z]
ct_norm = ct_slice - ct_slice.min()
if ct_norm.max() > 0:
    ct_norm = ct_norm / ct_norm.max()

ct_rgb = cv2.cvtColor((ct_norm*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
heatmap = cv2.applyColorMap((dist*255).astype(np.uint8), cv2.COLORMAP_JET)
xai_overlay = cv2.addWeighted(ct_rgb, 0.6, heatmap, 0.4, 0)
cv2.imwrite(os.path.join(OUTPUT_DIR, "xai_overlay.png"), xai_overlay)

# ================= SAVE RESULTS =================
with open("dice_vol.txt", "w") as f:
    f.write(
        f"NA|{volume_mm3}|{mask.shape}|{voxel_count}|{spacing}|{z}|"
        f"{tumor_size_x_mm:.2f}|{tumor_size_y_mm:.2f}|"
        f"{tumor_size_z_mm:.2f}|{tumor_max_diameter_mm:.2f}"
    )


print("Inference completed successfully")
