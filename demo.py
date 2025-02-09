import os
import torch
import numpy as np
from NIMBLELayer import NIMBLELayer

from utils import batch_to_tensor_device, save_textured_nimble, smooth_mesh, save_mesh, load_nimble_dict
import pytorch3d
from pytorch3d.structures.meshes import Meshes

if __name__ == "__main__":
    device = torch.zeros(1).device

    pm_dict_name = r"assets/NIMBLE_DICT_9137.pkl"
    tex_dict_name = r"assets/NIMBLE_TEX_DICT.pkl"
    mano_vreg_name = r"assets/NIMBLE_MANO_VREG.pkl"

    pm_dict = load_nimble_dict(pm_dict_name, device)
    tex_dict = load_nimble_dict(tex_dict_name, device)
    nimble_mano_vreg = load_nimble_dict(mano_vreg_name, device)

    nlayer = NIMBLELayer(pm_dict, tex_dict, device, use_pose_pca=True, pose_ncomp=30, shape_ncomp=20, nimble_mano_vreg=nimble_mano_vreg)

    bn = 1
    pose_param = torch.rand(bn, 30) * 2 - 1
    shape_param = torch.rand(bn, 20) * 2 - 1
    tex_param = torch.rand(bn, 10) - 0.5

    skin_v, muscle_v, bone_v, bone_joints, tex_img = nlayer.forward(pose_param, shape_param, tex_param, handle_collision=True)

    skin_p3dmesh = Meshes(skin_v, nlayer.skin_f.repeat(bn, 1, 1))
    muscle_p3dmesh = Meshes(muscle_v, nlayer.muscle_f.repeat(bn, 1, 1))
    bone_p3dmesh = Meshes(bone_v, nlayer.bone_f.repeat(bn, 1, 1))

    skin_p3dmesh = smooth_mesh(skin_p3dmesh)
    muscle_p3dmesh = smooth_mesh(muscle_p3dmesh)
    bone_p3dmesh = smooth_mesh(bone_p3dmesh)

    skin_mano_v = nlayer.nimble_to_mano(skin_v, is_surface=True)

    tex_img = tex_img.detach().cpu().numpy()
    skin_v_smooth = skin_p3dmesh.verts_padded()

    # Type checking
    assert skin_v_smooth is not None
    skin_v_smooth = skin_v_smooth.detach().cpu().numpy()
    bone_joints = bone_joints.detach().cpu().numpy()

    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)
    for i in range(bn):
        np.savetxt("{:s}\\rand_{:d}_joints.xyz".format(output_folder,i), bone_joints[i])
        np.savetxt("{:s}\\rand_{:d}_manov.xyz".format(output_folder,i), skin_mano_v[i])

        save_mesh(bone_p3dmesh[i], "{:s}\\rand_{:d}_bone.obj".format(output_folder, i))
        save_mesh(muscle_p3dmesh[i], "{:s}\\rand_{:d}_muscle.obj".format(output_folder,i))
        save_textured_nimble("{:s}\\rand_{:d}.obj".format(output_folder, i), skin_v_smooth[i], tex_img[i])
