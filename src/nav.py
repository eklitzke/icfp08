import math
import time

def A_star(start, goal, successors, edge_cost, heuristic_cost_to_goal=lambda position, goal:0):
  """Very general a-star search. Start and goal are objects to be compared
  with the 'is' operator, successors is a function that, given a node, returns
  other nodes reachable therefrom, edge_cost is a function that returns the
  cost to travel between two nodes, and heuristic_cost_to_goal is an
  admissible heuristic function that gives an underestimate of the cost from a
  position to the goal."""
  import heapq
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
    
    ............ (resolution w, resolution h)
    .          .
    .          . 
    .          .
    0...........          
    
    """
    def __init__(self, width, height, resolution): 
        self.width = float(width)
        self.height = float(height)
        self.grid_width = resolution
        self.grid_height = resolution
        self.resolution = resolution
        self.obstacles = set()  

    def node(self, x, y): 
        adj_x = x + (self.width / 2.0)
        adj_y = y + (self.height / 2.0)
        i = int(self.grid_width * adj_x / self.width)
        j = int(self.grid_height * adj_y / self.height)
        return (i*self.resolution) + j

    def cost(self, node1, node2): 
        return 1.0
    
    def distance(self, node1, node2):
        i1 = node1 % self.resolution
        j1 = node1 % self.resolution
        i2 = node2 % self.resolution
        j2 = node2 % self.resolution
        return math.hypot(i1 - i2, j1 - j2)

    def coord(self, node): 
        i = node % self.resolution
        j = node / self.resolution
        x = self.width * i / float(self.grid_width) 
        x -= self.width / 2.0
        y = self.height * j / float(self.grid_height)
        y -= self.height / 2.0
        return x, y

    def add_obstacle(self, x, y, radius):
        pass

    def path(self, start, goal):
        start_ = self.node(*start) 
        goal_ = self.node(*goal)
        result = A_star(start_, goal_, m.adjacent, m.cost, m.distance) 
        return map(m.coord, result)

    def adjacent(self, node): 
        for i in self._adjacent(node):
            if i not in self.obstacles:
                yield i
    
    def _adjacent(self, node): 
        i = node % self.resolution
        j = node / self.resolution
        res = self.resolution
        w = self.grid_width
        h = self.grid_height
        if i < w: # RIGHT
            yield ((i + 1) * res) + j
        if j < h: # UP
            yield (i * res) + j + 1
        if i < w and j <= h: # UP RIGHT
            yield ((i + 1) * res) + j + 1 
        if i < w and j > 0: # DOWN RIGHT
            yield ((i + 1) * res) + j - 1
        if i > 0 and j > 0:  # DOWN LEFT
            yield ((i + 1) * res) + j + 1
        if i > 0: # LEFT
            yield ((i - 1) * res) + j
        if j > 0: # DOWN
            yield (i * res) + j - 1
        if i > 0 and j <= h: # UP LEFT
            yield ((i-1) * res) + j + 1

if __name__ == '__main__':
    m = MapGrid(10, 10, 200)
    ts = time.time()
    path = m.path((-5, -5), (0, 0))
    te = time.time() 
    print path
    print te-ts

