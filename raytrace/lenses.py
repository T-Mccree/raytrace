#    Copyright 2009, Teraview Ltd., Bryan Cole
#
#    This file is part of Raytrace.
#
#    Raytrace is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from traits.api import Float, Instance, on_trait_change

from traitsui.api import View, Item, ListEditor, VSplit,\
            RangeEditor, ScrubberEditor, HSplit, VGroup

from tvtk.api import tvtk
     
from raytrace.bases import Optic, normaliseVector, NumEditor,\
    ComplexEditor, Traceable, transformPoints, transformNormals
    
from raytrace.cfaces import CircularFace, SphericalFace
from raytrace.ctracer import FaceList
from raytrace.cmaterials import DielectricMaterial

from raytrace.custom_sources import EmptyGridSource

import math, numpy


class BaseLens(Optic):
    abstract = True


class PlanoConvexLens(BaseLens):
    abstract = False
    name = "Plano-Convex Lens"
    
    CT = Float(5.0, desc="centre thickness")
    diameter = Float(15.0)
    offset = Float(0.0)
    curvature = Float(11.7, desc="radius of curvature for spherical face")
    
    #vtkproperty = tvtk.Property(representation="wireframe")
    
    vtk_grid = Instance(EmptyGridSource, ())
    vtk_cylinder = Instance(tvtk.Cylinder, ())
    vtk_sphere = Instance(tvtk.Sphere, ())
    
    clip2 = Instance(tvtk.ClipDataSet, ())
        
    traits_view = View(VGroup(
                       Traceable.uigroup,  
                       Item('n_inside'),
                       Item('CT', editor=NumEditor),
                       Item('diameter', editor=NumEditor),
                       Item('curvature', editor=NumEditor)
                       )
                    )
                    
    
    def _faces_default(self):
        fl = FaceList(owner=self)
        fl.faces = [CircularFace(owner=self, diameter=self.diameter,
                                material = self.material), 
                SphericalFace(owner=self, diameter=self.diameter,
                                material=self.material,
                                z_height=self.CT, curvature=self.curvature)]
        return fl
    
    def _CT_changed(self, new_ct):
        self.faces.faces[1].z_height = new_ct
        
    def _curvature_changed(self, new_curve):
        self.faces.faces[1].curvature = new_curve
    
    def make_step_shape(self):
        from .step_export import make_spherical_lens
        shape = make_spherical_lens(self.CT, self.diameter, self.curvature, 
                                   self.centre, self.direction, self.x_axis)
        return shape, "blue1"
    
    @on_trait_change("CT, diameter, curvature")
    def config_pipeline(self):
        ct = self.CT
        rad = self.diameter/2
        curve = self.curvature
        
        size = 41
        spacing = 2*rad / (size-1)
        if curve >= 0.0:
            extra=0.0
        else:
            extra = - curve - math.sqrt(curve**2 - rad**2)
        lsize = int((ct+extra)/spacing) + 2
        
        grid = self.vtk_grid
        grid.dimensions = (size,size,lsize)
        grid.origin = (-rad, -rad, 0)
        grid.spacing = (spacing, spacing, spacing)
                      
        cyl = self.vtk_cylinder
        cyl.center = (0,0,0)
        cyl.radius = rad
        
        s = self.vtk_sphere
        s.center = (0,0,ct - curve)
        s.radius = abs(curve)
        
        self.clip2.inside_out = bool(curve >= 0.0)
        
        self.vtk_grid.modified()
        self.update=True
        
                                         
    def _pipeline_default(self):
        grid = self.vtk_grid
        #grid.set_execute_method(self.create_grid)
        grid.modified()
        
        trans = tvtk.Transform()
        trans.rotate_x(90.)
        cyl = self.vtk_cylinder
        cyl.transform = trans
        
        clip1 = tvtk.ClipVolume(input_connection=grid.output_port,
                                 clip_function=self.vtk_cylinder,
                                 inside_out=1)
        
        self.clip2.set(input_connection = clip1.output_port,
                      clip_function=self.vtk_sphere,
                      inside_out=1)
        
        topoly = tvtk.GeometryFilter(input_connection=self.clip2.output_port)
        norms = tvtk.PolyDataNormals(input_connection=topoly.output_port)
        
        transF = tvtk.TransformFilter(input_connection=norms.output_port, 
                                      transform=self.transform)
        self.config_pipeline()
        grid.modified()
        return transF

        
if __name__=="__main__":
    from raytrace.tracer import RayTraceModel
    from raytrace.sources import ConfocalRaySource
    
    lens = PlanoConvexLens(orientation=0.0,
                           elevation=0.0,
                           CT=5.,
                           curvature=12.)
    
    source = ConfocalRaySource(focus=(0,0,-30),
                            direction=(0,0,1),
                            working_dist = 0.1,
                            number=20,
                            detail_resolution=5,
                            theta=10.,
                            scale_factor=0.1)
    
    model = RayTraceModel(optics=[lens], 
                          sources=[source,])
    model.configure_traits()
