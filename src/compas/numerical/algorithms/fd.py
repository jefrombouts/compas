from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


__author__    = ['Tom Van Mele', ]
__copyright__ = 'Copyright 2017, Block Research Group - ETH Zurich'
__license__   = 'MIT'
__email__     = 'vanmelet@ethz.ch'


__all__ = [
    'fd'
]


def fd(vertices, edges, fixed, q, loads):
    """Implementation of the force density method to compute equilibrium of axial force networks.

    Parameters
    ----------
    vertices : list
        XYZ coordinates of the vertices of the network
    edges : list
        Edges between vertices represented by
    fixed : list
        Indices of fixed vertices.
    q : list
        Force density of edges.
    loads : list
        XYZ components of the loads on the vertices.

    Returns
    -------
    xyz : array
        XYZ coordinates of the equilibrium geometry.
    q : array
        Force densities in the edges.
    f : array
        Forces in the edges.
    l : array
        Lengths of the edges
    r : array
        Residual forces.

    Notes
    -----
    For more info, see [1]_.

    References
    ----------
    .. [1] Schek H., *The Force Density Method for Form Finding and Computation of General Networks*,
           Computer Methods in Applied Mechanics and Engineering 3: 115-134, 1974.

    Examples
    --------
    .. plot::
        :include-source:

        import compas

        from compas.datastructures import Mesh
        from compas.plotters import MeshPlotter
        from compas.numerical import fd_numpy
        from compas.utilities import i_to_black

        # make a mesh
        # add default attributes for form finding

        mesh = Mesh.from_obj(compas.get('faces.obj'))

        mesh.update_default_vertex_attributes({'is_anchor': False, 'px': 0.0, 'py': 0.0, 'pz': 0.0})
        mesh.update_default_edge_attributes({'q': 1.0})

        # identify the anchors
        # move two anchors up to create anticlastic boundary conditions

        for key, attr in mesh.vertices(True):
            attr['is_anchor'] = mesh.vertex_degree(key) == 2
            if key in (18, 35):
                attr['z'] = 5.0

        # preprocess

        k_i   = mesh.key_index()
        xyz   = mesh.get_vertices_attributes(('x', 'y', 'z'))
        loads = mesh.get_vertices_attributes(('px', 'py', 'pz'))
        q     = mesh.get_edges_attribute('q')
        fixed = mesh.vertices_where({'is_anchor': True})
        fixed = [k_i[k] for k in fixed]
        edges = [(k_i[u], k_i[v]) for u, v in mesh.edges()]

        # compute equilibrium
        # update the mesh geometry

        xyz, q, f, l, r = fd_numpy(xyz, edges, fixed, q, loads)

        for key, attr in mesh.vertices(True):
            index = k_i[key]
            attr['x'] = xyz[index, 0]
            attr['y'] = xyz[index, 1]
            attr['z'] = xyz[index, 2]

        # visualisae the result
        # color the vertices according to their elevation

        plotter = MeshPlotter(mesh)

        zmax = max(mesh.get_vertices_attribute('z'))

        plotter.draw_vertices(
            facecolor={key: i_to_black(attr['z'] / zmax) for key, attr in mesh.vertices(True)}
        )
        plotter.draw_faces()
        plotter.draw_edges()
        plotter.show()

    """
    v    = len(vertices)
    free = list(set(range(v)) - set(fixed))
    xyz  = asarray(vertices, dtype=float).reshape((-1, 3))
    q    = asarray(q, dtype=float).reshape((-1, 1))
    p    = asarray(loads, dtype=float).reshape((-1, 3))
    C    = connectivity_matrix(edges, 'csr')
    Ci   = C[:, free]
    Cf   = C[:, fixed]
    Ct   = C.transpose()
    Cit  = Ci.transpose()
    Q    = diags([q.flatten()], [0])
    A    = Cit.dot(Q).dot(Ci)
    b    = p[free] - Cit.dot(Q).dot(Cf).dot(xyz[fixed])

    xyz[free] = spsolve(A, b)

    l = normrow(C.dot(xyz))
    f = q * l
    r = p - Ct.dot(Q).dot(C).dot(xyz)

    return xyz, q, f, l, r


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    import compas

    from compas.datastructures import Mesh
    from compas.plotters import MeshPlotter
    from compas.utilities import i_to_rgb

    mesh = Mesh.from_obj(compas.get('faces.obj'))

    lines = []
    for u, v in mesh.edges():
        lines.append({
            'start' : mesh.vertex_coordinates(u, 'xy'),
            'end'   : mesh.vertex_coordinates(v, 'xy'),
            'color' : '#cccccc',
            'width' : 0.5
        })

    mesh.update_default_vertex_attributes({'is_anchor': False, 'px': 0.0, 'py': 0.0, 'pz': 0.0})
    mesh.update_default_edge_attributes({'q': 1.0})

    for key, attr in mesh.vertices(True):
        attr['is_anchor'] = mesh.vertex_degree(key) == 2

    k_i   = mesh.key_index()
    xyz   = mesh.get_vertices_attributes(('x', 'y', 'z'))
    loads = mesh.get_vertices_attributes(('px', 'py', 'pz'))
    q     = mesh.get_edges_attribute('q')
    fixed = mesh.vertices_where({'is_anchor': True})
    fixed = [k_i[k] for k in fixed]
    edges = [(k_i[u], k_i[v]) for u, v in mesh.edges()]

    xyz, q, f, l, r = fd_numpy(xyz, edges, fixed, q, loads)

    for key, attr in mesh.vertices(True):
        index = k_i[key]
        attr['x'] = xyz[index, 0]
        attr['y'] = xyz[index, 1]
        attr['z'] = xyz[index, 2]

    for index, (u, v, attr) in enumerate(mesh.edges(True)):
        attr['f'] = f[index, 0]

    plotter = MeshPlotter(mesh, figsize=(10, 7))

    zmax = max(mesh.get_vertices_attribute('z'))
    fmax = max(mesh.get_edges_attribute('f'))

    plotter.draw_lines(lines)

    plotter.draw_vertices()
    plotter.draw_faces()
    plotter.draw_edges(
        width={(u, v): 10 * attr['f'] / fmax for u, v, attr in mesh.edges(True)},
        color={(u, v): i_to_rgb(attr['f'] / fmax) for u, v, attr in mesh.edges(True)},
    )

    plotter.show()
