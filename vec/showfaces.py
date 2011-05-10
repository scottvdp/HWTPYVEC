#!/usr/bin/python

import sys
if sys.version[0] == '3':
    from tkinter import Frame, Tk, Canvas, ALL, TOP, BOTH, mainloop
else:
    from Tkinter import Frame, Tk, Canvas, ALL, TOP, BOTH, mainloop


class Plotter(Frame):
    """Tk widget for plotting lines and points.

    Attributes:
      xspan: float - max difference in x coords in plot
      yspan: float - max difference in y coords in plot
      xorg: float - x coordinate of origin in plot
      yorg: float - y coordinate of origin in plot
      c: Canvas - the Tk Canvas used for plotting
      lines: list of [x0, y0, x1, y1], lines to plot
      points: list of [idnum, (x,y)], points to plot
      title: string - a title string
      longside: int - length in pixels of the long side of the window
    """

    def __init__(self, minx, miny, maxx, maxy, title="showfaces",
            longside=700):
        self.xspan = maxx - minx
        self.yspan = maxy - miny
        if self.xspan == 0.0:
            self.xspan = 1.0
        if self.yspan == 0.0:
            self.yspan = 1.0
        # add 10% on either end
        self.xorg = minx - 0.1 * self.xspan
        self.yorg = miny - 0.1 * self.yspan
        self.xspan *= 1.2
        self.yspan *= 1.2
        self.title = title
        self.longside = longside
        root = Tk()
        Frame.__init__(self, root)
        root.title(self.title)
        wtoh = self.xspan / self.yspan
        if wtoh >= 1.0:
            width = longside
            height = int(longside / wtoh)
        else:
            height = longside
            width = int(longside * wtoh)
        geometry = str(width) + "x" + str(height) + "+0+20"
        root.geometry(geometry)
        self.c = Canvas(root)
        self.c.pack(side=TOP, fill=BOTH, expand=1)
        self.c.bind('<Configure>', self.Reconfigure)

    def Xconv(self, x):
        CX = self.c.winfo_width()
        xx = int(CX * (x - self.xorg) / self.xspan)
        return xx

    def Yconv(self, y):
        CY = self.c.winfo_height()
        yy = int(CY - CY * (y - self.yorg) / self.yspan)
        return yy

    def PlotLines(self, lines):
        """Plot lines, list of [x0, y0, x1, y1]."""
        self.lines = lines

    def PlotPoints(self, points):
        """Plot points, list of [idnum, (x,y)]."""
        self.points = points

    def Reconfigure(self, event):
        self.Redraw()

    def Redraw(self):
        self.c.delete(ALL)
        for i in range(0, len(self.lines)):
            (x0, y0, x1, y1) = self.lines[i]
            self.c.create_line(self.Xconv(x0), self.Yconv(y0),
                self.Xconv(x1), self.Yconv(y1))
        for i in range(0, len(self.points)):
            (idnum, p) = self.points[i]
            (x, y) = p
            xx = self.Xconv(x)
            yy = self.Yconv(y)
            b = 8
            self.c.create_oval(xx - b, yy - b, xx + b, yy + b, fill="yellow")
            self.c.create_text(xx, yy, text=str(idnum))


def ShowFaces(faces, points, name="showfaces"):
    """Plot faces on a tk canvas.

    Args:
      faces: list of list of int - each sublist is a face
      points: geom.Points - gives coords for vertices
        If coords or 3d, project onto (x,y) plane.
    """

    vmap = points.pos
    if len(vmap) == 0:
        return
    if len(vmap[0]) == 3:
        vmap = [(x, y) for (x, y, _) in vmap]
    minx = 1e6
    maxx = -1e6
    miny = 1e6
    maxy = -1e6
    viset = set()
    lines = []
    prevp = None
    for i in range(0, len(faces)):
        f = faces[i]
        for j in range(0, len(f)):
            vertindex = f[j]
            viset.add(vertindex)
            (x, y) = p = vmap[vertindex]
            minx = min(x, minx)
            miny = min(y, miny)
            maxx = max(x, maxx)
            maxy = max(y, maxy)
            if prevp is not None:
                lines.append([prevp[0], prevp[1], x, y])
            prevp = p
        if len(f) != 0:
            # close the face
            (x, y) = vmap[f[0]]
            lines.append([prevp[0], prevp[1], x, y])
        prevp = None
    if len(viset) == 0:
        return
    points = []
    for i in range(0, len(vmap)):
        if i in viset:
            points.append([i, vmap[i]])
    plotter = Plotter(minx, miny, maxx, maxy, name)
    plotter.PlotLines(lines)
    plotter.PlotPoints(points)
    mainloop()


def ShowPolyArea(polyarea, name="showpolyarea"):
    """Plot a PolyArea on a tk canvas.

    Starts a tk mainloop, and only exits when
    user closes the tk window.

    Args:
      polyarea: geom.PolyArea
    """

    ShowFaces([polyarea.poly] + polyarea.holes, polyarea.points, name)
