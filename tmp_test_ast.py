import ast
source_code = """
class IntegerOps:
    @staticmethod
    def fmt_num(val):
        '''格式化: 若 val < 0 則加上括號，如 -5 -> (-5)'''
        return f"({val})" if val < 0 else str(val)

    @staticmethod
    def safe_eval(expr):
        return eval(expr)
"""
class StubTransformer(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        docstring = ast.get_docstring(node)
        new_body = []
        if docstring:
            new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
        new_body.append(ast.Expr(value=ast.Constant(value=...)))
        node.body = new_body
        return node
    def visit_ClassDef(self, node):
        self.generic_visit(node)
        return node

tree = ast.parse(source_code)
transformer = StubTransformer()
new_tree = transformer.visit(tree)
ast.fix_missing_locations(new_tree)
print("=== UNPARSED ===")
print(ast.unparse(new_tree))
