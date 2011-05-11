"""Implementation of Blender mathutils module interface.
"""

# So can test my code outside of Blender.


__author__ = "howard.trickey@gmail.com"

import math

FLOAT_TOL = 1e-7  # floats as close as this count as 'equal'

class Vector(object):
    """2d, 3d, or 4d vector of float coordinates.

    Note: this doesn't enforce that assignments to x, y, z
    should be float values.  Could do that by using internal
    slots for them and using properties, but let's just rely
    on programs respecting this.
    """
    __slots__ = "n", "x", "y", "z", "w"

    def __init__(self, tup):
        """Initialize Vector from a 2-, 3-, or 4-tuple"""
        self.n = n = len(tup)
        # do the most common case first
        if n == 3:
            self.x = float(tup[0])
            self.y = float(tup[1])
            self.z = float(tup[2])
        elif n == 2:
            self.x = float(tup[0])
            self.y = float(tup[1])
        elif n == 4:
            self.x = float(tup[0])
            self.y = float(tup[1])
            self.z = float(tup[2])
            self.w = float(tup[3])
        else:
            raise ValueError

    def __getitem__(self, i):
        if i < 0 or i >= self.n:
            raise ValueError
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        elif i == 2:
            return self.z
        elif i == 3:
            return self.w

    def __setitem__(self, i, val):
        if i < 0 or i >= self.n:
            raise ValueError
        if i == 0:
            self.x = float(val)
        elif i == 1:
            self.y = float(val)
        elif i == 2:
            self.z = float(val)
        elif i == 3:
            self.w = float(val)

    def __repr__(self):
        return "Vector(" + self.to_tuple().__repr__() + ")"

    def __str__(self):
        return self.to_tuple().__str__()

    def to_tuple(self):
        if self.n == 3:
            return (self.x, self.y, self.z)
        elif self.n == 2:
            return (self.x, self.y)
        else:
            return (self.x, self.y, self.z, self.w)

    def copy(self):
        return Vector(self.to_tuple())

    def _getmagnitude(self):
        """Return vector magnitude (length)"""
        if self.n == 3:
            ss = self.x * self.x + self.y * self.y + self.z * self.z
        elif self.n == 2:
            ss = self.x * self.x + self.y * self.y
        else:
            ss = self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w
        return math.sqrt(ss)

    def _setmagnitude(self, mag):
        """Change the vector components to make the magnitude be mag"""
        if mag <= 0.0:
            factor = 0.0
        else:
            curmag = self._getmagnitude()
            if curmag == 0.0:
                factor = 1.0
            else:
                factor = (mag / curmag) ** 2
        self.x *= factor
        self.y *= factor
        if self.n > 2:
            self.z *= factor
        if self.n > 3:
            self.w *= factor

    length = property(_getmagnitude, _setmagnitude)
    magnitude = property(_getmagnitude, _setmagnitude)

    def __lt__(self, other):
        return self.magnitude < other.magnitude

    def __le__(self, other):
        return self.magnitude <= other.magnitude

    def __gt__(self, other):
        return self.magnitude > other.magnitude

    def __ge__(self, other):
        return self.magnitude >= other.magnitude

    def __eq__(self, other):
        if abs(self.x - other.x) > FLOAT_TOL:
            return False
        if abs(self.y - other.y) > FLOAT_TOL:
            return False
        if self.n > 2:
            if abs(self.z - other.z) > FLOAT_TOL:
                return False
            if self.n > 3:
                if abs(self.w - other.w) > FLOAT_TOL:
                    return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        if abs(self.x) > FLOAT_TOL:
            return True
        if abs(self.y) > FLOAT_TOL:
            return True
        if self.n > 2:
            if abs(self.z) > FLOAT_TOL:
                return True
            if self.n > 3:
                if abs(self.w) > FLOAT_TOL:
                    return True
        return False

    def __len__(self):
        return self.n

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y
        if self.n == 2:
            return Vector((x, y))
        z = self.z + other.z
        if self.n == 3:
            return Vector((x, y, z))
        w = self.w + other.w
        return Vector((x, y, z, w))

    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y
        if self.n == 2:
            return Vector((x, y))
        z = self.z - other.z
        if self.n == 3:
            return Vector((x, y, z))
        w = self.w - other.w
        return Vector((x, y, z, w))

    def __mul__(self, other):
        if type(other) == type(self):
            return self.dot(other)
        elif isinstance(other, Matrix):
            return other.__rmul__(self)
        x = self.x * other
        y = self.y * other
        if self.n == 2:
            return Vector((x, y))
        z = self.z - other
        if self.n == 3:
            return Vector((x, y, z))
        w = self.w - other
        return Vector((x, y, z, w))

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        x = self.x / other
        y = self.y / other
        if self.n == 2:
            return Vector((x, y))
        z = self.z / other
        if self.n == 3:
            return Vector((x, y, z))
        w = self.w / other
        return Vector((x, y, z, w))

    def __truediv__(self, other):
        return self.__div__(other)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        if self.n == 2:
            return self
        self.z += other.z
        if self.n == 3:
            return self
        self.w += other.w
        return self

    def __iadd__(self, other):
        self.x -= other.x
        self.y -= other.y
        if self.n == 2:
            return self
        self.z -= other.z
        if self.n == 3:
            return self
        self.w -= other.w
        return self

    def __imul__(self, other):
        self.x *= other
        self.y *= other
        if self.n == 2:
            return self
        self.z *= other
        if self.n == 3:
            return self
        self.w *= other
        return self

    def __idiv__(self, other):
        self.x /= other
        self.y /= other
        if self.n == 2:
            return self
        self.z /= other
        if self.n == 3:
            return self
        self.w /= other
        return self

    def __neg__(self):
        x = -self.x
        y = -self.y
        if self.n == 2:
            return Vector((x, y))
        z = -self.z
        if self.n == 3:
            return Vector((x, y, z))
        w = -self.w
        return Vector((x, y, z, w))

    def dot(self, other):
        """"Returns the dot product of two vectors"""
        sum = self.x * other.x + self.y * other.y
        if self.n == 2:
            return sum
        sum += self.z * other.z
        if self.n == 3:
            return sum
        return sum + self.w * other.w

    def angle(self, other):
        """Returns the angle in radians between self and other in [0,pi]"""
        n1 = self.length
        n2 = other.length
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        else:
            costheta = self.dot(other) / (n1 * n2)
            if costheta > 1.0:
                costheta = 1.0
            if costheta < -1.0:
                costheta = -1.0
            return math.acos(costheta)

    def cross(self, other):
        """Returns the cross product between self and other"""
        if self.n == 3:
            return Vector((self.y * other.z - self.z * other.y,
                           self.z * other.x - self.x * other.z,
                           self.x * other.y - self.y * other.x))
        else:
            raise ValueError

    def negate(self):
        """Negate each component of self"""
        self.x = -self.x
        self.y = -self.y
        if self.n > 2:
            self.z = -self.z
            if self.n > 3:
                self.w = -self.w

    def lerp(self, other, factor):
        """Return linear interpolation factor of the way from self to other"""
        beta = 1.0 - factor
        x = beta * self.x + factor * other.x
        y = beta * self.y + factor * other.y
        if self.n == 2:
            return Vector((x, y))
        z = beta * self.z + factor * other.z
        if self.n == 3:
            return Vector((x, y, z))
        w = beta * self.w + factor * other.w
        return Vector((x, y, z, w))

    def normalize(self):
        """Adjust length of self to be 1.0, filling with nan if fail."""
        m = self.magnitude
        try:
            self.x /= m
            self.y /= m
            if self.n > 2:
                self.z /= m
                if self.n > 3:
                    self.w /= m
        except:
            self.x = float('nan')
            self.y = float('nan')
            self.z = float('nan')
            self.w = float('nan')

    def normalized(self):
        """Return a new normalized copy of self."""
        v = self.copy()
        v.normalize()
        return v

    def resize_2d(self):
        """Resize self to be 2d"""
        self.n = 2

    def resize_3d(self):
        """Resize self to be 3d, filling with 0.0 if necessary"""
        if self.n == 2:
            self.z = 0.0
        self.n = 3

    def resize_4d(self):
        """Resize self to be 4d, filling with 0.0 if necessary"""
        if self.n < 3:
            self.z = 0.0
        if self.n < 4:
            self.w = 0.0
        self.n = 4

    def to_2d(self):
        """Return a 2d copy of this vector"""
        return Vector((self.x, self.y))

    def to_3d(self):
        """Return a 3d copy of this vector"""
        if self.n == 2:
            return Vector((self.x, self.y, 0.0))
        return Vector((self.x, self.y, self.z))

    def to_4d(self):
        """Return a 4d copy of this vector"""
        if self.n == 2:
            return Vector((self.x, self.y, 0.0, 0.0))
        if self.n == 3:
            return Vector((self.x, self.y, self.z, 0.0))
        return self.copy()

    def zero(self):
        """Set all values to zero"""
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.w = 0.0


class Matrix(object):
    """mxn matrices, with m and n each 2, 3, or 4"""
    # These slot names aren't part of the public api
    __slots__ = "nrows", "ncols", "rows"

    def __init__(self, rowtup):
        """Initialize matrix from a sequence of tuples.
        There can be 2 to 4 tuples, and each can
        have 2 to 4 floats (same number of floats in each)."""

        self.nrows = len(rowtup)
        if self.nrows < 2 or self.nrows > 4:
            raise ValueError
        self.ncols = len(rowtup[0])
        if self.ncols < 2 or self.ncols > 4:
            raise ValueError
        for i in range(self.nrows):
            if len(rowtup[i]) != self.ncols:
                raise ValueError
        self.rows = [Vector(row) for row in rowtup]

    def __repr__(self):
        return "Matrix(" + ",\n       ".join([str(r) for r in self.rows]) + ")"

    def __str__(self):
        return "(" + ", ".join([str(r) for r in self.rows]) + ")"

    def __rmul__(self, other):
        """Vector times self multiplication.  Extend vector with 1s if needed"""
        print("matrix rmul, self=", self, "other=", other)
        a = []
        olen = len(other)
        for i in range(self.ncols):
            s = 0.0
            for j in range(self.nrows):
                if j < olen:
                    s += other[j] * self.rows[j][i]
                else:
                    s += self.rows[j][i]
            a.append(s)
        return Vector(a)

