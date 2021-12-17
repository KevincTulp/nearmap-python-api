import laspy as lp
import numpy as np
import open3d as o3d
from pathlib import Path


def voxelize(input_point_cloud, voxel_size: float or None, output_mesh):

    assert Path(input_point_cloud).is_file(), f"Error: Count not detect {input_point_cloud} in path specified"
    assert Path(input_point_cloud).suffix.lower() in ['.las', '.zlas'], f"Error {input_point_cloud} file format not supported"
    point_cloud=lp.read(input_point_cloud)

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.vstack((point_cloud.x, point_cloud.y, point_cloud.z)).transpose())
    pcd.colors = o3d.utility.Vector3dVector(np.vstack((point_cloud.red, point_cloud.green, point_cloud.blue)).transpose()/65535)

    if not voxel_size or voxel_size <= 0:
        v_size = round(max(pcd.get_max_bound()-pcd.get_min_bound())*0.005,4)
    elif voxel_size:
        v_size = voxel_size
    voxel_grid=o3d.geometry.VoxelGrid.create_from_point_cloud(pcd,voxel_size=v_size)

    voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(pcd, voxel_size=v_size)

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
    voxel_size = None # If None code will auto-determine. Integers ex: 0.45 are also supported
    output_mesh = None # r'mesh.ply' # Options include None or formats obj, ply, gltf, glb, off, and stl

    ###############
    # Begin Script
    voxelize(input_point_cloud, voxel_size, output_mesh)