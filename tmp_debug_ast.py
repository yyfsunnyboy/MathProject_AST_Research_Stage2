import ast
import random

s = 'v1 / ((v2 * v3) - v4)'
v1 = random.randint(-100,-1)
v2 = random.randint(-100,-1)
v3 = random.randint(1,100)
v4 = random.randint(1,100)

tree = ast.parse(s, mode='eval')

class DivVisitor(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Div):
            # Evaluate denominator to find its value
            # Then replace numerator node.left with ast.BinOp(node.left, ast.Mult(), node.right_eval)
            return ast.Call(
                func=ast.Name(id='_force_divisible', ctx=ast.Load()),
                args=[node.left, node.right],
                # We need to know which variable is the numerator to update math_str!
                # If we just return a value, the math_str won't match. 
                # This is tricky because math_str is purely string replacement.
                keywords=[]
            )
        return node
