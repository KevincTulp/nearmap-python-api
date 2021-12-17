import laspy as lp
import numpy as np
import open3d as o3d
from pathlib import Path
import copy


def voxelize(input_point_cloud, voxel_size: float or None, rotate_view, output_mesh):

    assert Path(input_point_cloud).is_file(), f"Error: Count not detect {input_point_cloud} in path specified"
    assert Path(input_point_cloud).suffix.lower() in ['.las', '.zlas'], f"Error {input_point_cloud} file format not supported"
    point_cloud=lp.read(input_point_cloud)

    pcd_init = o3d.geometry.PointCloud()
    pcd_init.points = o3d.utility.Vector3dVector(np.vstack((point_cloud.x, point_cloud.y, point_cloud.z)).transpose())
    pcd_init.colors = o3d.utility.Vector3dVector(np.vstack((point_cloud.red, point_cloud.green, point_cloud.blue)).transpose()/65535)
    R = pcd_init.get_rotation_matrix_from_zxy((np.pi / 2, 0, np.pi / 4))
    pcd = pcd_init.rotate(R, center=(0,0,0))

    if not voxel_size or voxel_size <= 0:
        v_size = round(max(pcd.get_max_bound()-pcd.get_min_bound())*0.005,4)
    elif voxel_size:
        v_size = voxel_size

    voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(pcd, voxel_size=v_size)


    def rotate_viewer(vis):
        ctr = vis.get_view_control()
        ctr.rotate(1.0, 0.0)
        return False

    if rotate_view:
        o3d.visualization.draw_geometries_with_animation_callback([voxel_grid], rotate_viewer)
    else:
        o3d.visualization.draw_geometries([voxel_grid])

    voxels = voxel_grid.get_voxels()

    vox_mesh = o3d.geometry.TriangleMesh()

    for v in voxels:
        cube = o3d.geometry.TriangleMesh.create_box(width=1, height=1,
                                                    depth=1)
        cube.paint_uniform_color(v.color)
        cube.translate(v.grid_index, relative=False)
        vox_mesh += cube

    if output_mesh:

        vox_mesh.translate([0.5, 0.5, 0.5], relative=True)
    
        #vox_mesh.scale(voxel_size, [0, 0, 0])
    
        vox_mesh.translate(voxel_grid.origin, relative=True)
    
        vox_mesh.merge_close_vertices(0.0000001)
    
        #o3d.io.write_triangle_mesh(output_mesh, vox_mesh)

        T = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]])
        out_format = Path(output_mesh).suffix.lower()
        if out_format == ".obj":
            o3d.io.write_triangle_mesh(output_mesh, vox_mesh.transform(T), write_triangle_uvs=True)
        elif out_format == ".ply":
            o3d.io.write_triangle_mesh(output_mesh, vox_mesh.transform(T))
        elif out_format in [".gltf", ".glb"]:
            o3d.io.write_triangle_mesh(output_mesh, vox_mesh.transform(T))
        elif out_format == ".off":
            o3d.io.write_triangle_mesh(output_mesh, vox_mesh.transform(T))
        elif out_format == ".stl":
            o3d.io.write_triangle_mesh(output_mesh, vox_mesh.transform(T))
        else:
            print(f"{out_format} not supported")


if __name__ == "__main__":

    ###############
    # User Inputs
    #############
    input_point_cloud = r'biltmore_house_las/PointCloud.las'  # Input las or laz PointCloud file
    voxel_size = None # If None code will auto-determine. Integers ex: 0.4 are also supported
    output_mesh = None # r'mesh.ply' # Options include None or formats obj, ply, gltf, glb, off, and stl
    rotate_view = False

    ###############
    # Begin Script
    voxelize(input_point_cloud, voxel_size, rotate_view, output_mesh)
