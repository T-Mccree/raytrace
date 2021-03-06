#!/usr/bin/env python

cdef extern from "math.h":
    double sqrt(double arg)

cdef extern from "float.h":
    #double INFINITY
    double DBL_MAX

cdef double INF


from libc.stdlib cimport malloc, free

############################################
### C type declarations for internal use ###
############################################

cdef struct vector_t:
    double x,y,z

cdef struct orientation_t:
    vector_t normal, tangent

IF UNAME_SYSNAME == "Windows":
    ctypedef double complex complex_t
ELSE:
    cdef struct complex_t:
        double real
        double imag

cdef packed struct ray_t:
    #vectors
    vector_t origin, direction, normal, E_vector
    #complex attribs
    complex_t refractive_index, E1_amp, E2_amp
    #simple attribs
    double length, phase
    #reference ids to related objects
    unsigned int wavelength_idx, parent_idx, end_face_idx
    ##objects
    #object face, end_face, child_refl, child_trans

cdef struct transform_t:
    double m00, m01, m02, m10, m11, m12, m20, m21, m22
    double tx, ty, tz

cdef struct ray_pair_t:
    ray_t trans, refln

##############################
### Vector maths functions ###
##############################

cdef  vector_t transform_c(transform_t t, vector_t p)
cdef  vector_t rotate_c(transform_t t, vector_t p)
cdef  vector_t set_v(object O)
cdef  double sep_(vector_t p1, vector_t p2)
cdef  vector_t multvv_(vector_t a, vector_t b)
cdef  vector_t multvs_(vector_t a, double b)
cdef  vector_t addvv_(vector_t a, vector_t b)
cdef  vector_t addvs_(vector_t a, double b)
cdef  vector_t subvv_(vector_t a, vector_t b)
cdef  vector_t subvs_(vector_t a, double b)
cdef  double dotprod_(vector_t a, vector_t b)
cdef  vector_t cross_(vector_t a, vector_t b)
cdef  vector_t norm_(vector_t a)
cdef  double mag_(vector_t a)
cdef  double mag_sq_(vector_t a)
cdef  vector_t invert_(vector_t v)


##################################
### Python extension types
##################################

cdef class Transform:
    cdef transform_t trans

cdef class Ray:
    cdef ray_t ray

cdef class RayCollection:
    cdef ray_t *rays
    cdef readonly unsigned long n_rays, max_size
    cdef public RayCollection parent

    cdef add_ray_c(self, ray_t r)

cdef class RayCollectionIterator:
    cdef:
        RayCollection rays
        unsigned int counter


cdef class InterfaceMaterial(object):
    """Abstract base class for objects describing
    the materials characterics of a Face
    """
    cdef double[:] _wavelengths

    cdef eval_child_ray_c(self, ray_t *old_ray,
                            unsigned int ray_idx,
                            vector_t point,
                            orientation_t orient,
                            RayCollection new_rays)

    cdef on_set_wavelengths(self)


cdef class Face(object):
    cdef public object owner
    cdef public char *name
    cdef public double tolerance
    cdef public int idx #index in the global face list
    cdef public double max_length
    cdef public InterfaceMaterial material
    cdef public short int invert_normal
    cdef public unsigned int count

    cdef double intersect_c(self, vector_t p1, vector_t p2)

    cdef vector_t compute_normal_c(self, vector_t p)
    cdef vector_t compute_tangent_c(self, vector_t p)


cdef class FaceList(object):
    """A group of faces which share a transform"""
    cdef transform_t trans
    cdef transform_t inv_trans
    cdef public list faces
    cdef public object owner

    cdef int intersect_c(self, ray_t *ray, vector_t end_point, double max_length)
    cdef orientation_t compute_orientation_c(self, Face face, vector_t point)


##################################
### Python module functions
##################################

cdef RayCollection trace_segment_c(RayCollection rays,
                                    list face_sets,
                                    list all_faces,
                                    float max_length)

cdef double ray_power_(ray_t ray)
