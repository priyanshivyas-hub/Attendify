# navigation.py
import math
from database import get_db_connection

class NavigationGraph:
    def __init__(self):
        self.locations = {}   # id -> {name, lat, lon}
        self.graph = {}       # adjacency list

    def load_from_db(self):
        conn = get_db_connection()
        if not conn:
            print("DB connection failed")
        return 
        cursor = conn.cursor()

        cursor.execute("SELECT location_id, name, latitude, longitude FROM locations")
        for row in cursor.fetchall():
            self.locations[row['location_id']] = {
                'name': row['name'],
                'lat': row['latitude'],
                'lon': row['longitude']
            }
        cursor.execute("SELECT from_location, to_location, distance FROM paths")
        for row in cursor.fetchall():
            frm = row['from_location']
            to = row['to_location']
            dist = row['distance']
            self.graph.setdefault(frm, []).append((to, dist))
            self.graph.setdefault(to, []).append((frm, dist))
        cursor.close()
        conn.close()

    def haversine(self, lat1, lon1, lat2, lon2):
        # approximate distance between two points (if no direct path)
        R = 6371000  # metres
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def shortest_path(self, start_id, end_id):
        # Dijkstra's algorithm
        import heapq
        dist = {loc: float('inf') for loc in self.locations}
        prev = {loc: None for loc in self.locations}
        dist[start_id] = 0
        pq = [(0, start_id)]

        while pq:
            d, u = heapq.heappop(pq)
            if u == end_id:
                break
            if d > dist[u]:
                continue
            for v, w in self.graph.get(u, []):
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))

        # Reconstruct path
        if dist[end_id] == float('inf'):
            return None, float('inf')
        path = []
        cur = end_id
        while cur is not None:
            path.append(self.locations[cur]['name'])
            cur = prev[cur]
        path.reverse()
        return path, dist[end_id]