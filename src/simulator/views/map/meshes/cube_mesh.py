from panda3d.core import Texture, GeomNode, LineSegs
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter, GeomVertexRewriter, GeomVertexArrayData
from panda3d.core import Vec3, Vec4

from typing import List, Any, Tuple, Optional
from numbers import Real
import math

import numpy as np
from nptyping import NDArray

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from structures import Point, Colour, WHITE
from simulator.views.map.meshes.common import normalise, Face

class CubeMesh():
    name: str
    geom: Geom

    __face_count: int

    __vertex_data_format: GeomVertexFormat
    __vertex_data: GeomVertexData

    __triangles: GeomTriangles
    __triangle_data: GeomVertexArrayData

    __vertex: GeomVertexWriter
    __normal: GeomVertexWriter

    def __init__(self, name: str = 'cube_mesh') -> None:
        self.name = name
        
        self.__vertex_data_format = GeomVertexFormat.getV3n3()
        self.__vertex_data = GeomVertexData(name, self.__vertex_data_format, Geom.UHStatic)

        self.geom = Geom(self.__vertex_data)
        self.__triangles = GeomTriangles(Geom.UHStatic)
        self.__triangle_data = self.__triangles.modifyVertices()

        self.__vertex = GeomVertexWriter(self.__vertex_data, 'vertex')
        self.__normal = GeomVertexWriter(self.__vertex_data, 'normal')

        self.__face_count = 0

        def add_face(face: Face) -> None:
            self.__make_face(face)

        self.__make_face(Face.LEFT)
        self.__make_face(Face.RIGHT)
        self.__make_face(Face.BACK)
        self.__make_face(Face.FRONT)
        self.__make_face(Face.BOTTOM)
        self.__make_face(Face.TOP)

        self.__triangles.close_primitive()
        self.geom.add_primitive(self.__triangles)
    
    def __make_face(self, face: Face, pos: Point = Point(0,0,0)) -> None:
        def make(x1, y1, z1, x2, y2, z2) -> None:
            if x1 == x2:
                self.__vertex.addData3f(x1, y1, z1)
                self.__vertex.addData3f(x2, y2, z1)
                self.__vertex.addData3f(x2, y2, z2)
                self.__vertex.addData3f(x1, y1, z2)

                self.__normal.addData3(normalise(2 * x1 - 1, 2 * y1 - 1, 2 * z1 - 1))
                self.__normal.addData3(normalise(2 * x2 - 1, 2 * y2 - 1, 2 * z1 - 1))
                self.__normal.addData3(normalise(2 * x2 - 1, 2 * y2 - 1, 2 * z2 - 1))
                self.__normal.addData3(normalise(2 * x1 - 1, 2 * y1 - 1, 2 * z2 - 1))
            else:
                self.__vertex.addData3f(x1, y1, z1)
                self.__vertex.addData3f(x2, y1, z1)
                self.__vertex.addData3f(x2, y2, z2)
                self.__vertex.addData3f(x1, y2, z2)

                self.__normal.addData3(normalise(2 * x1 - 1, 2 * y1 - 1, 2 * z1 - 1))
                self.__normal.addData3(normalise(2 * x2 - 1, 2 * y1 - 1, 2 * z1 - 1))
                self.__normal.addData3(normalise(2 * x2 - 1, 2 * y2 - 1, 2 * z2 - 1))
                self.__normal.addData3(normalise(2 * x1 - 1, 2 * y2 - 1, 2 * z2 - 1))

            vertex_id = self.__face_count * 4

            self.__triangles.addVertices(vertex_id, vertex_id + 1, vertex_id + 3)
            self.__triangles.addVertices(vertex_id + 1, vertex_id + 2, vertex_id + 3)

            self.__face_count += 1

        x, y, z = pos
        if face == Face.FRONT:
            make(x + 1, y + 1, z - 1, x, y + 1, z)
        elif face == Face.BACK:
            make(x, y, z - 1, x + 1, y, z)
        elif face == Face.RIGHT:
            make(x + 1, y, z - 1, x + 1, y + 1, z)
        elif face == Face.LEFT:
            make(x, y + 1, z - 1, x, y, z)
        elif face == Face.TOP:
            make(x + 1, y + 1, z, x, y, z)
        elif face == Face.BOTTOM:
            make(x, y + 1, z - 1, x + 1, y, z - 1)
        else:
            raise Exception("unknown face")

    @property
    def artificial_lighting(self) -> str:
        return 'artificial_lighting'

    @artificial_lighting.getter
    def artificial_lighting(self) -> bool:
        return self.__artificial_lighting

    @property
    def body_node(self) -> GeomNode:
        node = GeomNode(self.name)
        node.addGeom(self.geom)
        return node


if __name__ == "__main__":
    from direct.showbase.ShowBase import ShowBase
    app = ShowBase()
    mesh = CubeMesh()
    n = mesh.body_node
    cube = render.attach_new_node(n)
    cube.detach_node()

    np = render.attach_new_node('')
    np.set_color(1,1,1,1)
    np.set_pos(0, 20, 0)
    cube.instance_to(np)

    np = render.attach_new_node('')
    np.set_color(0,1,1,1)
    np.set_pos(-0.5, 20, 0)
    cube.instance_to(np)
    app.run()