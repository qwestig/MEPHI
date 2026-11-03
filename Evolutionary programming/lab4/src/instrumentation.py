"""AST instrumentation for pure, loop-free integer functions with simple ifs."""
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Execution:
    genome: tuple
    covered: set
    distances: dict
    output: int


class Instrumenter(ast.NodeTransformer):
    def __init__(self):
        self.function, self.parents, self.metadata, self.functions = '', [], {}, []

    def visit_FunctionDef(self, node):
        self.function = node.name
        self.functions.append(node.name)
        return self.generic_visit(node)

    def visit_If(self, node):
        if not isinstance(node.test, ast.Compare) or len(node.test.ops) != 1:
            raise ValueError('Only single comparisons are supported')
        operator = type(node.test.ops[0]).__name__
        if operator not in {'Lt', 'LtE', 'Gt', 'GtE', 'Eq', 'NotEq'}:
            raise ValueError('Unsupported comparison')
        number = 1+sum(v['function'] == self.function for v in self.metadata.values())
        branch = f'{self.function}.{number}'
        self.metadata[branch] = dict(function=self.function, condition=ast.unparse(node.test),
                                    parents=self.parents[:], line=node.lineno)
        probe = ast.Call(func=ast.Name(id='_probe', ctx=ast.Load()),
                         args=[ast.Constant(branch), ast.Constant(operator), node.test.left,
                               node.test.comparators[0]], keywords=[])
        node.test = ast.copy_location(probe, node.test)
        old = self.parents
        self.parents = old+[branch+':T']
        node.body = [self.visit(child) for child in node.body]
        self.parents = old+[branch+':F']
        node.orelse = [self.visit(child) for child in node.orelse]
        self.parents = old
        return node


class Subject:
    def __init__(self, path: Path):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        if any(isinstance(n, (ast.For, ast.While, ast.Try, ast.AsyncFunctionDef)) for n in ast.walk(tree)):
            raise ValueError('Loops, exception handlers and async are outside this experiment')
        transform = Instrumenter()
        tree = transform.visit(tree)
        self.metadata, self.functions = transform.metadata, transform.functions
        self.goals = [branch+':'+side for branch in self.metadata for side in ['T', 'F']]
        self.paths = {goal: self.metadata[goal[:-2]]['parents']+[goal] for goal in self.goals}
        self.namespace = {'_probe': self.probe}
        # Only the bundled, inspected subject is compiled; this is not a sandbox.
        exec(compile(ast.fix_missing_locations(tree), str(path), 'exec'), self.namespace)
        self.trace, self.covered = {}, set()

    def probe(self, branch, op, a, b):
        distances = {
            'Lt': (max(0, a-b+1), max(0, b-a)),
            'LtE': (max(0, a-b), max(0, b-a+1)),
            'Gt': (max(0, b-a+1), max(0, a-b)),
            'GtE': (max(0, b-a), max(0, a-b+1)),
            'Eq': (abs(a-b), int(a == b)),
            'NotEq': (int(a == b), abs(a-b)),
        }[op]
        true_distance, false_distance = distances
        outcome = true_distance == 0
        self.trace[branch+':T'] = true_distance
        self.trace[branch+':F'] = false_distance
        self.covered.add(branch+(':T' if outcome else ':F'))
        return outcome

    def execute(self, genome):
        selector, x, y, z = genome
        if not 0 <= selector < len(self.functions) or any(not -100 <= v <= 100 for v in [x, y, z]):
            raise ValueError('Genome outside the fixed integer domain')
        self.trace, self.covered = {}, set()
        result = self.namespace[self.functions[selector]](x, y, z)
        return Execution(tuple(genome), self.covered.copy(), self.trace.copy(), result)

    def fitness(self, execution, goal):
        """Approach level plus normalized branch distance; zero covers the goal."""
        if self.functions[execution.genome[0]] != self.metadata[goal[:-2]]['function']:
            return len(self.paths[goal])+1.0
        path = self.paths[goal]
        for i, step in enumerate(path):
            if step not in execution.covered:
                distance = execution.distances.get(step)
                if distance is None:
                    return len(path)-i+1.0
                return len(path)-i-1 + distance/(distance+1.0)
        return 0.0
