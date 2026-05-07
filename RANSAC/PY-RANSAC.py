# r: numpy, pyransac3d

import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import numpy as np
import pyransac3d as pyrsc
import scriptcontext as sc

def fit_tight_planes_final():
    mesh_id = rs.GetObject("Select mesh", rs.filter.mesh)
    if not mesh_id: return
    
    mesh = rs.coercemesh(mesh_id)
    pts = np.array([[v.X, v.Y, v.Z] for v in mesh.Vertices])
    
    num_planes = rs.GetInteger("How many planes?", 5, 1, 50)
    thresh = rs.GetReal("Distance threshold", 0.5)
    
    remaining_pts = pts
    planes_found = 0

    for i in range(num_planes):
        if len(remaining_pts) < 10: break
            
        plane_gen = pyrsc.Plane()
        best_eq, inliers = plane_gen.fit(remaining_pts, thresh=thresh, maxIteration=1000)
        
        if len(inliers) < 10: break

        # 1. Plane Equation & Normal
        a, b, c, d = best_eq
        normal = rg.Vector3d(a, b, c)
        inlier_pts = remaining_pts[inliers]
        
        # Create origin at the average of inliers
        avg = np.mean(inlier_pts, axis=0)
        origin = rg.Point3d(avg[0], avg[1], avg[2])
        
        # Define local plane
        base_plane = rg.Plane(origin, normal)

        # 2. Project points to find local Min/Max (the 'Natural' size)
        min_u, max_u = float('inf'), float('-inf')
        min_v, max_v = float('inf'), float('-inf')
        
        for p in inlier_pts:
            success, u, v = base_plane.ClosestPoint(rg.Point3d(p[0], p[1], p[2]))
            if success:
                min_u, max_u = min(min_u, u), max(max_u, u)
                min_v, max_v = min(min_v, v), max(max_v, v)

        # 3. Create the Plane Surface
        u_domain = rg.Interval(min_u, max_u)
        v_domain = rg.Interval(min_v, max_v)
        tight_srf = rg.PlaneSurface(base_plane, u_domain, v_domain)

        # 4. Add to Rhino Document
        if tight_srf:
            obj_id = sc.doc.Objects.AddSurface(tight_srf)
            rs.ObjectName(obj_id, f"RANSAC_Plane_{i}")
            planes_found += 1
        
        # Remove points and continue
        remaining_pts = np.delete(remaining_pts, inliers, axis=0)

    sc.doc.Views.Redraw()
    print(f"Successfully created {planes_found} tight planes.")

if __name__ == "__main__":
    fit_tight_planes_final()