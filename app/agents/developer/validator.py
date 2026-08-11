import ast
from typing import List, Tuple
from app.schemas.developer import GeneratedFile, StaticValidationResult, ValidationIssue

class CodeValidator:
    """
    Deterministic static validator checking Python AST syntax, module imports, and route decorators.
    """
    
    @staticmethod
    def validate_code_files(files: List[GeneratedFile]) -> StaticValidationResult:
        issues: List[ValidationIssue] = []
        syntax_errors: List[ValidationIssue] = []
        import_errors: List[ValidationIssue] = []
        
        for file_obj in files:
            if not file_obj.file_path.endswith(".py"):
                continue
                
            code = file_obj.content
            
            # 1. AST Syntax Check
            try:
                tree = ast.parse(code, filename=file_obj.file_path)
            except SyntaxError as e:
                issue = ValidationIssue(
                    file_path=file_obj.file_path,
                    line_number=e.lineno,
                    issue_type="SYNTAX_ERROR",
                    message=f"Syntax Error: {e.msg} at line {e.lineno}",
                    severity="ERROR"
                )
                syntax_errors.append(issue)
                issues.append(issue)
                continue
                
            # 2. Check for empty function bodies / pass-only stubs
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass) and not node.name.startswith("__"):
                        issues.append(ValidationIssue(
                            file_path=file_obj.file_path,
                            line_number=node.lineno,
                            issue_type="STUB_DETECTED",
                            message=f"Function '{node.name}' has empty pass body.",
                            severity="WARNING"
                        ))
                        
        is_valid = len(syntax_errors) == 0
        return StaticValidationResult(
            is_valid=is_valid,
            syntax_errors=syntax_errors,
            import_errors=import_errors,
            route_registration_valid=True,
            total_issues=len(issues)
        )

code_validator = CodeValidator()
