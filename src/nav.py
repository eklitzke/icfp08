import math
import time
import heapq

import mars_math

def A_star(start, goal, successors, edge_cost, heuristic_cost_to_goal=lambda position, goal:0):
  """Very general a-star search. Start and goal are objects to be compared
  with the 'is' operator, successors is a function that, given a node, returns
  other nodes reachable therefrom, edge_cost is a function that returns the
  cost to travel between two nodes, and heuristic_cost_to_goal is an
  admissible heuristic function that gives an underestimate of the cost from a
  position to the goal."""
  closed = set()
  open = [(0, 0, (start,))]
  while open:
    heuristic_cost, cost_so_far, path = heapq.heappop(open)
    tail = path[-1]
    if tail in closed:
      continue
    if tail == goal:
      return path
    closed.add(tail)
    for new_tail in successors(tail):
      new_cost_so_far = cost_so_far + edge_cost(tail, new_tail)
      new_heuristic_cost = new_cost_so_far + heuristic_cost_to_goal(new_tail, goal)
      heapq.heappush(open, (new_cost_so_far, new_heuristic_cost, path+(new_tail,)))
  raise RuntimeError('No path found.')

class MapGrid(object):
    """a map grid centered on the origin with width w and height h and resolution
    map:
    ...........w,h
    .          .
    .   0,0    . 
    .          .
    -w,-h.......          
 


    grid:
    ............ (resolution w, resolution h)
    .          .
    .          . 
    .          .
    0...........          
    
    """
    def __init__(self, width, height, resolution): 
        self.width = float(width)
        self.height = float(height)
        resolution = int(resolution)
        self.grid_width = resolution
        self.grid_height = resolution
        self.resolution = resolution
        self.obstacles = set()  

    def node(self, x, y): 
        adj_x = x + (self.width / 2.0)
        adj_y = y + (self.height / 2.0)
        i = int(self.grid_width * adj_x / self.width)
        j = int(self.grid_height * adj_y / self.height)
        return self._encode(i, j)

    def cost(self, node1, node2): 
        return self.distance(node1, node2)

    def distance(self, node1, node2):
        i1, j1 = self._decode(node1)
        i2, j2 = self._decode(node2)
        return math.hypot(float(i1 - i2), float(j1 - j2))

    def _decode(self, node): 
        i, j = node
        return i, j

    def _encode(self, i, j): 
        assert 0 <= i < self.resolution, i
        assert 0 <= j < self.resolution, j
        return (i, j)

    def coord(self, node): 
        i, j = self._decode(node)
        assert i >= 0, i
        assert j >= 0, j
        x = self.width * i / float(self.grid_width) 
        x -= self.width / 2.0
        y = self.height * j / float(self.grid_height)
        y -= self.height / 2.0
        return mars_math.Point(x, y)

    def add_obstacle(self, point, radius):
        """Add an obstacle to the grid
        Args:
        """
        # find the units this will take up on the grid
        gwidth = int(round((self.resolution / self.width) * radius, 0))
        gheight = int(round((self.resolution / self.height) * radius, 0))

        node = self.node(*point)
        center_i, center_j = self._decode(node)
        start_i = max(0, center_i - gwidth)
        end_i = min(self.grid_width, center_i + gwidth)
        start_j = max(0, center_j - gheight)
        end_j = min(self.grid_height, center_j + gheight)

        print "adding obstacle from:", self.coord(self._encode(start_i, start_j)), "to", self.coord(self._encode(end_i, end_j))
        for i in range(start_i, end_i + 1):
            for j in range(start_j, end_j + 1):
                self.obstacles.add(self._encode(i, j))

    def path(self, start, goal):
        """Find a path from start to goal"""
        start_ = self.node(start.x, start.y) 
        goal_ = self.node(goal.x, goal.y)
        result = A_star(start_, goal_, self.adjacent, self.cost, self.distance) 
        return map(self.coord, result)

    def adjacent(self, node): 
        for i in self._adjacent(node):
            if i not in self.obstacles:
                yield i

    def _adjacent(self, node): 
        i, j = self._decode(node)
        res = self.resolution
        w = self.grid_width
        h = self.grid_height
        if i + 1 < w: # RIGHT
            yield self._encode(i + 1, j)
        if j + 1 < h: # UP
            yield self._encode(i, j + 1)
        if i + 1 < w and j + 1 < h: # UP RIGHT
            yield self._encode(i + 1, j + 1)
        if i + 1 < w and j > 0: # DOWN RIGHT
            yield self._encode(i + 1, j - 1)
        if i > 0 and j > 0:  # DOWN LEFT
            yield self._encode(i - 1, j - 1)
        if i > 0: # LEFT
            yield self._encode(i - 1, j)
        if j > 0: # DOWN
            yield self._encode(i, j - 1)
        if i > 0 and j + 1 < h: # UP LEFT
            yield self._encode(i - 1, j + 1)

if __name__ == '__main__':
    m = MapGrid(10, 10, 100)
    ts = time.time()
    m.add_obstacle((1.0, 1.0), 1.0)
    path = m.path((0, 0), (4.5, 4.5))
    te = time.time() 
    print path
    print te-ts

