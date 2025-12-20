"""
Snap Manager - система привязок
Менеджер привязок для геометрических примитивов
"""

from typing import List, Tuple, Optional, Dict, Set, TYPE_CHECKING
from dataclasses import dataclass
from ..primitives.base import Primitive, SnapPoint, SnapType
from ..utils.math_utils import distance, line_intersection

if TYPE_CHECKING:
    from ..primitives.segment import Segment
    from ..primitives.circle import Circle
    from ..primitives.arc import Arc


@dataclass
class SnapResult:
    """Result of snap detection"""
    x: float
    y: float
    snap_type: SnapType
    primitive_id: Optional[str] = None
    distance: float = 0.0


class SnapManager:
    """Snap manager for geometric primitives"""
    
    def __init__(self):
        self._enabled_snaps: Set[SnapType] = {
            SnapType.ENDPOINT, SnapType.MIDPOINT, SnapType.CENTER,
            SnapType.INTERSECTION, SnapType.PERPENDICULAR, SnapType.QUADRANT
        }
        self.snap_tolerance: float = 10.0
        self.current_snap: Optional[SnapResult] = None
        self._marker_ids: List[int] = []
    
    def enable_snap(self, snap_type: SnapType):
        """Enable snap type"""
        self._enabled_snaps.add(snap_type)
    
    def disable_snap(self, snap_type: SnapType):
        """Disable snap type"""
        self._enabled_snaps.discard(snap_type)
    
    def toggle_snap(self, snap_type: SnapType):
        """Toggle snap type"""
        if snap_type in self._enabled_snaps:
            self._enabled_snaps.discard(snap_type)
        else:
            self._enabled_snaps.add(snap_type)
    
    def is_snap_enabled(self, snap_type: SnapType) -> bool:
        """Check if snap type is enabled"""
        return snap_type in self._enabled_snaps
    
    def get_enabled_snaps(self) -> Set[SnapType]:
        """Get enabled snap types"""
        return self._enabled_snaps.copy()
    
    def set_enabled_snaps(self, snap_types: Set[SnapType]):
        """Set enabled snap types"""
        self._enabled_snaps = snap_types.copy()
    
    def find_snap(self, x: float, y: float, primitives: List[Primitive], transform, exclude_ids: Set[str] = None) -> Optional[SnapResult]:
        """Find nearest snap point"""
        if exclude_ids is None:
            exclude_ids = set()
        
        best_snap: Optional[SnapResult] = None
        best_distance = self.snap_tolerance
        wx, wy = transform.inverse_transform_point(x, y)
        
        for primitive in primitives:
            if primitive.id in exclude_ids or not primitive.visible:
                continue
            
            snap_points = primitive.get_snap_points()
            for sp in snap_points:
                if sp.snap_type not in self._enabled_snaps:
                    continue
                
                sx, sy = transform.transform_point(sp.x, sp.y)
                d = distance((x, y), (sx, sy))
                if d < best_distance:
                    best_distance = d
                    best_snap = SnapResult(
                        x=sp.x, y=sp.y,
                        snap_type=sp.snap_type,
                        primitive_id=sp.primitive_id,
                        distance=d
                    )
        
        if SnapType.INTERSECTION in self._enabled_snaps and len(primitives) >= 2:
            intersection_snap = self._find_intersection_snap(x, y, primitives, transform, exclude_ids, best_distance)
            if intersection_snap and intersection_snap.distance < best_distance:
                best_snap = intersection_snap
                best_distance = intersection_snap.distance
        
        if SnapType.PERPENDICULAR in self._enabled_snaps:
            perp_snap = self._find_perpendicular_to_nearest(x, y, primitives, transform, exclude_ids, best_distance)
            if perp_snap and perp_snap.distance < best_distance:
                best_snap = perp_snap
        
        self.current_snap = best_snap
        return best_snap
    
    def _find_perpendicular_to_nearest(self, x: float, y: float, primitives: List[Primitive], transform, exclude_ids: Set[str], max_distance: float) -> Optional[SnapResult]:
        """Find perpendicular snap to nearest segment"""
        from ..primitives.segment import Segment
        from ..utils.math_utils import perpendicular_point
        
        if exclude_ids is None:
            exclude_ids = set()
        
        wx, wy = transform.inverse_transform_point(x, y)
        best_snap = None
        best_distance = max_distance
        
        for primitive in primitives:
            if primitive.id in exclude_ids or not primitive.visible:
                continue
            
            if isinstance(primitive, Segment):
                perp = perpendicular_point((wx, wy), (primitive.x1, primitive.y1), (primitive.x2, primitive.y2))
                seg_len = distance((primitive.x1, primitive.y1), (primitive.x2, primitive.y2))
                d1 = distance((primitive.x1, primitive.y1), perp)
                d2 = distance(perp, (primitive.x2, primitive.y2))
                if d1 <= seg_len + 0.01 and d2 <= seg_len + 0.01:
                    sx, sy = transform.transform_point(perp[0], perp[1])
                    d = distance((x, y), (sx, sy))
                    if d < best_distance:
                        best_distance = d
                        best_snap = SnapResult(
                            x=perp[0], y=perp[1],
                            snap_type=SnapType.PERPENDICULAR,
                            primitive_id=primitive.id,
                            distance=d
                        )
        
        return best_snap
    
    def _find_intersection_snap(self, x: float, y: float, primitives: List[Primitive], transform, exclude_ids: Set[str], max_distance: float) -> Optional[SnapResult]:
        """Find intersection snap"""
        from ..primitives.segment import Segment
        from ..primitives.circle import Circle
        from ..primitives.arc import Arc
        
        if exclude_ids is None:
            exclude_ids = set()
        
        visible_prims = [p for p in primitives if p.id not in exclude_ids and p.visible]
        best_snap = None
        best_distance = max_distance
        
        for i, prim1 in enumerate(visible_prims):
            for prim2 in visible_prims[i + 1:]:
                intersections = self._find_primitive_intersections(prim1, prim2)
                for intersection in intersections:
                    if intersection:
                        ix, iy = intersection
                        sx, sy = transform.transform_point(ix, iy)
                        d = distance((x, y), (sx, sy))
                        if d < best_distance:
                            best_distance = d
                            best_snap = SnapResult(
                                x=ix, y=iy,
                                snap_type=SnapType.INTERSECTION,
                                primitive_id=None,
                                distance=d
                            )
        
        return best_snap
    
    def _find_primitive_intersections(self, prim1: Primitive, prim2: Primitive) -> List[Tuple[float, float]]:
        """Find intersections between two primitives"""
        from ..primitives.segment import Segment
        from ..primitives.circle import Circle
        from ..primitives.arc import Arc
        from ..primitives.rectangle import Rectangle
        from ..primitives.ellipse import Ellipse
        from ..primitives.polygon import Polygon
        from ..primitives.spline import Spline
        
        intersections = []
        edges1 = self._get_primitive_edges(prim1)
        edges2 = self._get_primitive_edges(prim2)
        seen = set()
        
        for e1 in edges1:
            for e2 in edges2:
                result = self._segment_intersection(e1[0], e1[1], e1[2], e1[3], e2[0], e2[1], e2[2], e2[3])
                if result:
                    key = (round(result[0], 6), round(result[1], 6))
                    if key not in seen:
                        seen.add(key)
                        intersections.append(result)
        
        if isinstance(prim1, Arc) and isinstance(prim2, Arc):
            arc_ints = self._arc_arc_intersection(prim1, prim2)
            for result in arc_ints:
                key = (round(result[0], 6), round(result[1], 6))
                if key not in seen:
                    seen.add(key)
                    intersections.append(result)
        
        return intersections
    
    def _get_primitive_edges(self, prim: Primitive) -> List[Tuple[float, float, float, float]]:
        """Get edges of primitive as segments"""
        from ..primitives.segment import Segment
        from ..primitives.rectangle import Rectangle
        from ..primitives.polygon import Polygon
        from ..primitives.ellipse import Ellipse
        from ..primitives.spline import Spline
        from ..primitives.circle import Circle
        from ..primitives.arc import Arc
        import math
        
        edges = []
        
        if isinstance(prim, Segment):
            edges.append((prim.x1, prim.y1, prim.x2, prim.y2))
        elif isinstance(prim, Rectangle):
            edges.extend(self._get_rectangle_edges(prim))
        elif isinstance(prim, Circle):
            num_segments = 64
            points = []
            for i in range(num_segments + 1):
                angle = 2 * math.pi * i / num_segments
                x = prim.cx + prim.radius * math.cos(angle)
                y = prim.cy + prim.radius * math.sin(angle)
                points.append((x, y))
            for i in range(len(points) - 1):
                edges.append((points[i][0], points[i][1], points[i + 1][0], points[i + 1][1]))
        elif isinstance(prim, Arc):
            from ..utils.line_renderer import sample_arc_points
            points = sample_arc_points(prim.cx, prim.cy, prim.radius, prim.start_angle, prim.end_angle, 32)
            for i in range(len(points) - 1):
                edges.append((points[i][0], points[i][1], points[i + 1][0], points[i + 1][1]))
        elif isinstance(prim, Polygon):
            vertices = prim._get_vertices()
            for i in range(len(vertices)):
                p1 = vertices[i]
                p2 = vertices[(i + 1) % len(vertices)]
                edges.append((p1[0], p1[1], p2[0], p2[1]))
        elif isinstance(prim, Ellipse):
            num_segments = 64
            points = []
            for i in range(num_segments):
                angle = 2 * math.pi * i / num_segments
                px, py = prim._get_point_on_ellipse(angle)
                points.append((px, py))
            if points:
                points.append(points[0])
            for i in range(len(points) - 1):
                edges.append((points[i][0], points[i][1], points[i + 1][0], points[i + 1][1]))
        elif isinstance(prim, Spline):
            if len(prim.control_points) >= 2:
                curve_points = prim._get_curve_points()
                for i in range(len(curve_points) - 1):
                    p1 = curve_points[i]
                    p2 = curve_points[i + 1]
                    edges.append((p1[0], p1[1], p2[0], p2[1]))
        
        return edges
    
    def _get_rectangle_edges(self, rect: "Rectangle") -> List[Tuple[float, float, float, float]]:
        """Get rectangle edges as segments"""
        corners = rect._get_rotated_corners()
        edges = []
        for i in range(4):
            p1 = corners[i]
            p2 = corners[(i + 1) % 4]
            edges.append((p1[0], p1[1], p2[0], p2[1]))
        return edges
    
    def _arc_arc_intersection(self, arc1: "Arc", arc2: "Arc") -> List[Tuple[float, float]]:
        """Find intersections between two arcs"""
        from ..primitives.circle import Circle
        import math
        
        temp_circle1 = Circle(arc1.cx, arc1.cy, arc1.radius)
        temp_circle2 = Circle(arc2.cx, arc2.cy, arc2.radius)
        circle_ints = self._circle_circle_intersection(temp_circle1, temp_circle2)
        
        results = []
        
        def normalize(a):
            while a < 0:
                a += 2 * math.pi
            while a >= 2 * math.pi:
                a -= 2 * math.pi
            return a
        
        def point_on_arc(arc, x, y):
            angle = math.atan2(y - arc.cy, x - arc.cx)
            angle_n = normalize(angle)
            start_n = normalize(arc.start_angle)
            end_n = normalize(arc.end_angle)
            sweep = (end_n - start_n) % (2 * math.pi)
            if sweep <= math.pi:
                if start_n <= end_n:
                    return start_n <= angle_n <= end_n
                else:
                    return angle_n >= start_n or angle_n <= end_n
            elif start_n <= end_n:
                return angle_n >= end_n or angle_n <= start_n
            else:
                return end_n <= angle_n <= start_n
        
        for ix, iy in circle_ints:
            if point_on_arc(arc1, ix, iy) and point_on_arc(arc2, ix, iy):
                results.append((ix, iy))
        
        return results
    
    def _segment_intersection(self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, x4: float, y4: float) -> Optional[Tuple[float, float]]:
        """Find intersection of two segments"""
        dx1 = x2 - x1
        dy1 = y2 - y1
        dx2 = x4 - x3
        dy2 = y4 - y3
        
        cross = dx1 * dy2 - dy1 * dx2
        if abs(cross) < 1e-10:
            return None
        
        dx3 = x3 - x1
        dy3 = y3 - y1
        
        t = (dx3 * dy2 - dy3 * dx2) / cross
        u = (dx3 * dy1 - dy3 * dx1) / cross
        
        eps = 1e-06
        if -eps <= t <= 1 + eps and -eps <= u <= 1 + eps:
            ix = x1 + t * dx1
            iy = y1 + t * dy1
            return (ix, iy)
        return None
    
    def _segment_circle_intersection(self, segment: "Segment", circle: "Circle") -> List[Tuple[float, float]]:
        """Find intersections between segment and circle"""
        import math
        
        dx = segment.x2 - segment.x1
        dy = segment.y2 - segment.y1
        fx = segment.x1 - circle.cx
        fy = segment.y1 - circle.cy
        
        a = dx * dx + dy * dy
        b = 2 * (fx * dx + fy * dy)
        c = fx * fx + fy * fy - circle.radius * circle.radius
        
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return []
        
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)
        
        results = []
        for t in [t1, t2]:
            if 0 <= t <= 1:
                ix = segment.x1 + t * dx
                iy = segment.y1 + t * dy
                results.append((ix, iy))
        
        return results
    
    def _segment_arc_intersection(self, segment: "Segment", arc: "Arc") -> List[Tuple[float, float]]:
        """Find intersections between segment and arc"""
        from ..primitives.circle import Circle
        import math
        
        temp_circle = Circle(arc.cx, arc.cy, arc.radius)
        circle_ints = self._segment_circle_intersection(segment, temp_circle)
        
        results = []
        for ix, iy in circle_ints:
            angle = math.atan2(iy - arc.cy, ix - arc.cx)
            
            def normalize(a):
                while a < 0:
                    a += 2 * math.pi
                while a >= 2 * math.pi:
                    a -= 2 * math.pi
                return a
            
            start_n = normalize(arc.start_angle)
            end_n = normalize(arc.end_angle)
            angle_n = normalize(angle)
            
            if start_n <= end_n:
                in_arc = start_n <= angle_n <= end_n
            else:
                in_arc = angle_n >= start_n or angle_n <= end_n
            
            if in_arc:
                results.append((ix, iy))
        
        return results
    
    def _circle_circle_intersection(self, circle1: "Circle", circle2: "Circle") -> List[Tuple[float, float]]:
        """Find intersections between two circles"""
        import math
        
        dx = circle2.cx - circle1.cx
        dy = circle2.cy - circle1.cy
        d = math.sqrt(dx * dx + dy * dy)
        
        if d > circle1.radius + circle2.radius or d < abs(circle1.radius - circle2.radius):
            return []
        if d < 1e-10:
            return []
        
        a = (circle1.radius * circle1.radius - circle2.radius * circle2.radius + d * d) / (2 * d)
        h = math.sqrt(circle1.radius * circle1.radius - a * a)
        
        px = circle1.cx + a * dx / d
        py = circle1.cy + a * dy / d
        
        results = [
            (px + h * -dy / d, py + h * dx / d),
            (px - h * -dy / d, py - h * dx / d)
        ]
        
        return results
    
    def find_perpendicular_snap(self, x: float, y: float, from_point: Tuple[float, float], primitives: List[Primitive], transform, exclude_ids: Set[str] = None) -> Optional[SnapResult]:
        """Find perpendicular snap from point"""
        if SnapType.PERPENDICULAR not in self._enabled_snaps:
            return None
        
        if exclude_ids is None:
            exclude_ids = set()
        
        from ..primitives.segment import Segment
        from ..utils.math_utils import perpendicular_point
        
        best_snap = None
        best_distance = self.snap_tolerance
        
        for primitive in primitives:
            if primitive.id in exclude_ids or not primitive.visible:
                continue
            
            if isinstance(primitive, Segment):
                perp = primitive.get_perpendicular_point(from_point[0], from_point[1])
                seg_len = distance((primitive.x1, primitive.y1), (primitive.x2, primitive.y2))
                d1 = distance((primitive.x1, primitive.y1), perp)
                d2 = distance(perp, (primitive.x2, primitive.y2))
                if d1 <= seg_len and d2 <= seg_len:
                    sx, sy = transform.transform_point(perp[0], perp[1])
                    d = distance((x, y), (sx, sy))
                    if d < best_distance:
                        best_distance = d
                        best_snap = SnapResult(
                            x=perp[0], y=perp[1],
                            snap_type=SnapType.PERPENDICULAR,
                            primitive_id=primitive.id,
                            distance=d
                        )
        
        return best_snap
    
    def draw_snap_marker(self, canvas, transform):
        """Draw snap marker"""
        self.clear_markers(canvas)
        if self.current_snap is None:
            return
        
        sx, sy = transform.transform_point(self.current_snap.x, self.current_snap.y)
        marker_size = 8
        
        if self.current_snap.snap_type == SnapType.ENDPOINT:
            marker_id = canvas.create_rectangle(
                sx - marker_size, sy - marker_size,
                sx + marker_size, sy + marker_size,
                outline="#FF6600", width=2
            )
        elif self.current_snap.snap_type == SnapType.MIDPOINT:
            points = [sx, sy - marker_size, sx - marker_size, sy + marker_size, sx + marker_size, sy + marker_size]
            marker_id = canvas.create_polygon(points, outline="#FF6600", fill="", width=2)
        elif self.current_snap.snap_type == SnapType.CENTER:
            marker_id = canvas.create_oval(
                sx - marker_size, sy - marker_size,
                sx + marker_size, sy + marker_size,
                outline="#FF6600", width=2
            )
        elif self.current_snap.snap_type == SnapType.INTERSECTION:
            marker_id = canvas.create_line(
                sx - marker_size, sy - marker_size,
                sx + marker_size, sy + marker_size,
                fill="#FF6600", width=2
            )
            self._marker_ids.append(marker_id)
            marker_id = canvas.create_line(
                sx - marker_size, sy + marker_size,
                sx + marker_size, sy - marker_size,
                fill="#FF6600", width=2
            )
        elif self.current_snap.snap_type == SnapType.PERPENDICULAR:
            marker_id = canvas.create_line(sx - marker_size, sy, sx + marker_size, sy, fill="#FF6600", width=2)
            self._marker_ids.append(marker_id)
            marker_id = canvas.create_line(sx, sy - marker_size, sx, sy + marker_size, fill="#FF6600", width=2)
        elif self.current_snap.snap_type == SnapType.QUADRANT:
            points = [sx, sy - marker_size, sx + marker_size, sy, sx, sy + marker_size, sx - marker_size, sy]
            marker_id = canvas.create_polygon(points, outline="#FF6600", fill="", width=2)
        else:
            marker_id = canvas.create_oval(
                sx - marker_size, sy - marker_size,
                sx + marker_size, sy + marker_size,
                outline="#FF6600", width=2
            )
        
        self._marker_ids.append(marker_id)
    
    def clear_markers(self, canvas):
        """Clear snap markers"""
        for marker_id in self._marker_ids:
            try:
                canvas.delete(marker_id)
            except:
                pass
        self._marker_ids.clear()
    
    def clear(self):
        """Clear current snap"""
        self.current_snap = None


SNAP_TYPE_NAMES = {
    SnapType.ENDPOINT: "Конец",
    SnapType.MIDPOINT: "Середина",
    SnapType.CENTER: "Центр",
    SnapType.INTERSECTION: "Пересечение",
    SnapType.PERPENDICULAR: "Перпендикуляр",
    SnapType.TANGENT: "Касательная",
    SnapType.QUADRANT: "Квадрант",
}
