"""AI-Powered Test Generation for Comprehensive Quality Assurance."""

import ast
import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import inspect
from pathlib import Path

from ..common.logging import get_logger
from ..model_router.models import ModelRequest, ModelResponse
from ..model_router.claude_client import get_claude_client
from ..plan_management.models import Plan, Task

logger = get_logger("ai_test_generator")


class TestType(str, Enum):
    """Types of tests that can be generated."""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    END_TO_END = "end_to_end"
    API = "api"
    UI = "ui"


class TestFramework(str, Enum):
    """Supported test frameworks."""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    JEST = "jest"
    MOCHA = "mocha"
    JUNIT = "junit"
    RSPEC = "rspec"


class CoverageType(str, Enum):
    """Types of test coverage to analyze."""
    STATEMENT = "statement"
    BRANCH = "branch"
    FUNCTION = "function"
    LINE = "line"


@dataclass
class CodeContext:
    """Context information about code to test."""
    filename: str
    content: str
    language: str
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity_score: float = 0.0


@dataclass
class TestCase:
    """Generated test case."""
    test_id: str
    name: str
    test_type: TestType
    framework: TestFramework
    code: str
    description: str
    assertions: List[str]
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
    mock_requirements: List[str] = field(default_factory=list)
    expected_coverage: float = 0.0
    priority: int = 5  # 1-10, higher is more important
    estimated_execution_time: float = 1.0  # seconds
    tags: List[str] = field(default_factory=list)


@dataclass
class TestSuite:
    """Collection of generated test cases."""
    suite_id: str
    name: str
    test_cases: List[TestCase]
    framework: TestFramework
    total_coverage_estimate: float
    setup_requirements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_total_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TestGenerationRequest:
    """Request for test generation."""
    code_context: CodeContext
    test_types: List[TestType] = field(default_factory=lambda: [TestType.UNIT])
    framework: TestFramework = TestFramework.PYTEST
    coverage_target: float = 80.0
    max_tests_per_function: int = 5
    include_edge_cases: bool = True
    include_performance_tests: bool = False
    include_security_tests: bool = False
    custom_requirements: List[str] = field(default_factory=list)


@dataclass
class TestAnalysis:
    """Analysis of existing or generated tests."""
    total_tests: int
    coverage_analysis: Dict[CoverageType, float]
    test_distribution: Dict[TestType, int]
    quality_score: float
    missing_coverage_areas: List[str]
    recommendations: List[str]
    potential_issues: List[str]


class CodeAnalyzer:
    """Analyzes code to extract testable components."""
    
    def __init__(self):
        self.supported_languages = ['python', 'javascript', 'typescript', 'java']
    
    def analyze_code(self, code: str, filename: str) -> CodeContext:
        """Analyze code and extract context for test generation."""
        language = self._detect_language(filename)
        
        if language == 'python':
            return self._analyze_python_code(code, filename)
        elif language in ['javascript', 'typescript']:
            return self._analyze_js_code(code, filename)
        else:
            return self._analyze_generic_code(code, filename, language)
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c'
        }
        
        suffix = Path(filename).suffix.lower()
        return extension_map.get(suffix, 'unknown')
    
    def _analyze_python_code(self, code: str, filename: str) -> CodeContext:
        """Analyze Python code using AST."""
        try:
            tree = ast.parse(code)
            
            functions = []
            classes = []
            imports = []
            complexity_score = 0.0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                    complexity_score += self._calculate_function_complexity(node)
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)
                    complexity_score += self._calculate_function_complexity(node)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.extend(self._extract_import_names(node))
            
            # Normalize complexity score
            complexity_score = complexity_score / max(len(functions), 1)
            
            return CodeContext(
                filename=filename,
                content=code,
                language='python',
                functions=functions,
                classes=classes,
                imports=imports,
                complexity_score=complexity_score
            )
            
        except SyntaxError as e:
            logger.warning(f"Python syntax error in {filename}: {e}")
            return self._analyze_generic_code(code, filename, 'python')
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> float:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return float(complexity)
    
    def _extract_import_names(self, node) -> List[str]:
        """Extract import names from import nodes."""
        names = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
            for alias in node.names:
                names.append(alias.name)
        
        return names
    
    def _analyze_js_code(self, code: str, filename: str) -> CodeContext:
        """Analyze JavaScript/TypeScript code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        # Extract function declarations
        function_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*\(',
            r'let\s+(\w+)\s*=\s*\(',
            r'var\s+(\w+)\s*=\s*\(',
            r'(\w+)\s*:\s*function\s*\(',
            r'async\s+function\s+(\w+)\s*\('
        ]
        
        for pattern in function_patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            functions.extend(matches)
        
        # Extract class declarations
        class_matches = re.findall(r'class\s+(\w+)', code, re.MULTILINE)
        classes.extend(class_matches)
        
        # Extract imports
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            imports.extend(matches)
        
        # Simple complexity estimation
        complexity_indicators = ['if', 'else', 'for', 'while', 'switch', 'try', 'catch']
        complexity_score = sum(len(re.findall(rf'\b{indicator}\b', code)) for indicator in complexity_indicators)
        complexity_score = complexity_score / max(len(functions), 1)
        
        return CodeContext(
            filename=filename,
            content=code,
            language=self._detect_language(filename),
            functions=functions,
            classes=classes,
            imports=imports,
            complexity_score=complexity_score
        )
    
    def _analyze_generic_code(self, code: str, filename: str, language: str) -> CodeContext:
        """Generic code analysis fallback."""
        # Basic line and complexity analysis
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Simple heuristics for functions/classes
        functions = []
        classes = []
        
        for line in lines:
            line = line.strip().lower()
            if any(keyword in line for keyword in ['def ', 'function ', 'func ']):
                # Extract potential function name
                words = line.split()
                if len(words) > 1:
                    functions.append(words[1])
            elif any(keyword in line for keyword in ['class ', 'struct ', 'interface ']):
                words = line.split()
                if len(words) > 1:
                    classes.append(words[1])
        
        complexity_score = len(non_empty_lines) / 100.0  # Simple complexity metric
        
        return CodeContext(
            filename=filename,
            content=code,
            language=language,
            functions=functions,
            classes=classes,
            complexity_score=complexity_score
        )


class TestPatternLibrary:
    """Library of test patterns and templates."""
    
    def __init__(self):
        self.patterns = {
            TestFramework.PYTEST: self._get_pytest_patterns(),
            TestFramework.UNITTEST: self._get_unittest_patterns(),
            TestFramework.JEST: self._get_jest_patterns()
        }
    
    def _get_pytest_patterns(self) -> Dict[TestType, str]:
        """Get pytest test patterns."""
        return {
            TestType.UNIT: """
def test_{function_name}_{test_case}():
    \"\"\"Test {function_name} {test_description}.\"\"\"
    # Arrange
    {setup_code}
    
    # Act
    result = {function_call}
    
    # Assert
    {assertions}
""",
            TestType.INTEGRATION: """
def test_{function_name}_integration_{test_case}():
    \"\"\"Integration test for {function_name} {test_description}.\"\"\"
    # Setup dependencies
    {setup_code}
    
    # Execute integration
    result = {function_call}
    
    # Verify integration
    {assertions}
    
    # Cleanup
    {teardown_code}
""",
            TestType.PERFORMANCE: """
def test_{function_name}_performance():
    \"\"\"Performance test for {function_name}.\"\"\"
    import time
    
    start_time = time.time()
    {function_call}
    execution_time = time.time() - start_time
    
    assert execution_time < {max_execution_time}, f"Execution time {{execution_time}} exceeded limit"
""",
            TestType.SECURITY: """
def test_{function_name}_security_{test_case}():
    \"\"\"Security test for {function_name} - {test_description}.\"\"\"
    # Test for security vulnerability
    {setup_code}
    
    # Attempt security breach
    try:
        result = {function_call}
        {security_assertions}
    except {expected_exception} as e:
        # Expected security exception
        assert str(e) == "{expected_message}"
"""
        }
    
    def _get_unittest_patterns(self) -> Dict[TestType, str]:
        """Get unittest test patterns."""
        return {
            TestType.UNIT: """
def test_{function_name}_{test_case}(self):
    \"\"\"Test {function_name} {test_description}.\"\"\"
    # Arrange
    {setup_code}
    
    # Act
    result = {function_call}
    
    # Assert
    {assertions}
"""
        }
    
    def _get_jest_patterns(self) -> Dict[TestType, str]:
        """Get Jest test patterns."""
        return {
            TestType.UNIT: """
test('{function_name} {test_description}', () => {{
    // Arrange
    {setup_code}
    
    // Act
    const result = {function_call};
    
    // Assert
    {assertions}
}});
"""
        }


class AITestGenerator:
    """Main AI-powered test generator."""
    
    def __init__(self):
        self.code_analyzer = CodeAnalyzer()
        self.pattern_library = TestPatternLibrary()
        self.claude_client = get_claude_client()
        
        # AI generation settings
        self.ai_enabled = True
        self.fallback_to_templates = True
        self.max_ai_generation_time = 30.0  # seconds
    
    async def generate_test_suite(self, request: TestGenerationRequest) -> TestSuite:
        """Generate comprehensive test suite for given code."""
        logger.info(f"Generating test suite for {request.code_context.filename}")
        
        start_time = datetime.utcnow()
        test_cases = []
        
        # Generate tests for each function
        for function_name in request.code_context.functions:
            function_tests = await self._generate_function_tests(
                function_name, request
            )
            test_cases.extend(function_tests)
        
        # Generate class tests
        for class_name in request.code_context.classes:
            class_tests = await self._generate_class_tests(
                class_name, request
            )
            test_cases.extend(class_tests)
        
        # Generate integration tests if requested
        if TestType.INTEGRATION in request.test_types:
            integration_tests = await self._generate_integration_tests(request)
            test_cases.extend(integration_tests)
        
        # Generate performance tests if requested
        if TestType.PERFORMANCE in request.test_types or request.include_performance_tests:
            performance_tests = await self._generate_performance_tests(request)
            test_cases.extend(performance_tests)
        
        # Generate security tests if requested
        if TestType.SECURITY in request.test_types or request.include_security_tests:
            security_tests = await self._generate_security_tests(request)
            test_cases.extend(security_tests)
        
        # Calculate coverage estimate
        total_coverage = self._estimate_coverage(test_cases, request.code_context)
        
        # Calculate total estimated time
        total_time = sum(test.estimated_execution_time for test in test_cases)
        
        suite_id = f"suite-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        test_suite = TestSuite(
            suite_id=suite_id,
            name=f"Test Suite for {request.code_context.filename}",
            test_cases=test_cases,
            framework=request.framework,
            total_coverage_estimate=total_coverage,
            setup_requirements=self._extract_setup_requirements(request.code_context),
            dependencies=request.code_context.dependencies,
            estimated_total_time=total_time,
            created_at=start_time
        )
        
        logger.info(f"Generated {len(test_cases)} tests with {total_coverage:.1f}% estimated coverage")
        return test_suite
    
    async def _generate_function_tests(self, function_name: str, 
                                     request: TestGenerationRequest) -> List[TestCase]:
        """Generate tests for a specific function."""
        test_cases = []
        
        # Extract function signature and context
        function_context = self._extract_function_context(function_name, request.code_context)
        
        # Generate AI-powered tests if enabled
        if self.ai_enabled:
            try:
                ai_tests = await self._generate_ai_tests(function_name, function_context, request)
                test_cases.extend(ai_tests)
            except Exception as e:
                logger.warning(f"AI test generation failed for {function_name}: {e}")
                if self.fallback_to_templates:
                    template_tests = self._generate_template_tests(function_name, request)
                    test_cases.extend(template_tests)
        else:
            template_tests = self._generate_template_tests(function_name, request)
            test_cases.extend(template_tests)
        
        return test_cases[:request.max_tests_per_function]
    
    async def _generate_ai_tests(self, function_name: str, function_context: Dict[str, Any],
                               request: TestGenerationRequest) -> List[TestCase]:
        """Generate tests using AI/LLM."""
        prompt = self._create_test_generation_prompt(function_name, function_context, request)
        
        model_request = ModelRequest(
            messages=[{"role": "user", "content": prompt}],
            text=prompt,
            request_id=f"test-gen-{function_name}-{datetime.utcnow().timestamp()}"
        )
        
        try:
            response = await self.claude_client.generate_response(model_request)
            return self._parse_ai_test_response(response.result, function_name, request)
        except Exception as e:
            logger.error(f"AI test generation failed: {e}")
            return []
    
    def _create_test_generation_prompt(self, function_name: str, function_context: Dict[str, Any],
                                     request: TestGenerationRequest) -> str:
        """Create prompt for AI test generation."""
        context = request.code_context
        
        prompt = f"""
Generate comprehensive test cases for the function '{function_name}' in {context.language}.

Function Context:
- Filename: {context.filename}
- Language: {context.language}
- Function: {function_name}
- Code snippet: {function_context.get('code', 'Not available')}
- Complexity: {context.complexity_score:.2f}

Requirements:
- Test Framework: {request.framework.value}
- Test Types: {', '.join(t.value for t in request.test_types)}
- Coverage Target: {request.coverage_target}%
- Include edge cases: {request.include_edge_cases}
- Include performance tests: {request.include_performance_tests}
- Include security tests: {request.include_security_tests}

Please generate {request.max_tests_per_function} test cases that cover:
1. Normal operation (happy path)
2. Edge cases and boundary conditions
3. Error handling and exception cases
4. Input validation
{f'5. Performance characteristics' if request.include_performance_tests else ''}
{f'6. Security vulnerabilities' if request.include_security_tests else ''}

For each test case, provide:
- Test name and description
- Complete test code using {request.framework.value}
- Expected assertions
- Any required setup/teardown
- Mock requirements if needed

Format the response as JSON with the following structure:
{{
    "test_cases": [
        {{
            "name": "test_function_name_scenario",
            "description": "Description of what this test validates",
            "code": "Complete test code",
            "assertions": ["list of assertions"],
            "setup_code": "setup code if needed",
            "teardown_code": "teardown code if needed",
            "mock_requirements": ["list of mocks needed"],
            "test_type": "unit|integration|performance|security",
            "priority": 1-10,
            "tags": ["list", "of", "tags"]
        }}
    ]
}}
"""
        return prompt
    
    def _parse_ai_test_response(self, response: str, function_name: str,
                              request: TestGenerationRequest) -> List[TestCase]:
        """Parse AI response into TestCase objects."""
        test_cases = []
        
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            for i, test_data in enumerate(data.get('test_cases', [])):
                test_case = TestCase(
                    test_id=f"{function_name}_{i}_{datetime.utcnow().timestamp()}",
                    name=test_data.get('name', f'test_{function_name}_{i}'),
                    test_type=TestType(test_data.get('test_type', 'unit')),
                    framework=request.framework,
                    code=test_data.get('code', ''),
                    description=test_data.get('description', ''),
                    assertions=test_data.get('assertions', []),
                    setup_code=test_data.get('setup_code'),
                    teardown_code=test_data.get('teardown_code'),
                    mock_requirements=test_data.get('mock_requirements', []),
                    priority=test_data.get('priority', 5),
                    tags=test_data.get('tags', [])
                )
                test_cases.append(test_case)
                
        except json.JSONDecodeError:
            # Fallback: try to extract test code blocks
            test_cases = self._extract_tests_from_text(response, function_name, request)
        
        return test_cases
    
    def _extract_tests_from_text(self, text: str, function_name: str,
                               request: TestGenerationRequest) -> List[TestCase]:
        """Extract test cases from plain text response."""
        test_cases = []
        
        # Look for code blocks
        code_blocks = re.findall(r'```(?:python|javascript|typescript)?\n(.*?)\n```', text, re.DOTALL)
        
        for i, code_block in enumerate(code_blocks):
            if 'def test_' in code_block or 'test(' in code_block:
                test_case = TestCase(
                    test_id=f"{function_name}_extracted_{i}",
                    name=f"test_{function_name}_{i}",
                    test_type=TestType.UNIT,
                    framework=request.framework,
                    code=code_block.strip(),
                    description=f"Extracted test for {function_name}",
                    assertions=self._extract_assertions(code_block)
                )
                test_cases.append(test_case)
        
        return test_cases
    
    def _extract_assertions(self, code: str) -> List[str]:
        """Extract assertion statements from test code."""
        assertions = []
        
        # Common assertion patterns
        assertion_patterns = [
            r'assert\s+(.+)',
            r'self\.assert\w+\((.+)\)',
            r'expect\((.+)\)',
            r'\.should\((.+)\)'
        ]
        
        for pattern in assertion_patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            assertions.extend(matches)
        
        return assertions
    
    def _generate_template_tests(self, function_name: str,
                               request: TestGenerationRequest) -> List[TestCase]:
        """Generate tests using templates as fallback."""
        test_cases = []
        
        patterns = self.pattern_library.patterns.get(request.framework, {})
        
        for test_type in request.test_types:
            if test_type in patterns:
                # Generate basic test from template
                template = patterns[test_type]
                
                test_code = template.format(
                    function_name=function_name,
                    test_case="basic",
                    test_description="basic functionality",
                    setup_code="# Setup test data",
                    function_call=f"{function_name}()",
                    assertions="assert result is not None",
                    teardown_code="# Cleanup",
                    max_execution_time="1.0",
                    expected_exception="Exception",
                    expected_message="Expected error",
                    security_assertions="assert 'safe' in str(result)"
                )
                
                test_case = TestCase(
                    test_id=f"{function_name}_{test_type.value}_template",
                    name=f"test_{function_name}_{test_type.value}",
                    test_type=test_type,
                    framework=request.framework,
                    code=test_code,
                    description=f"Template-generated {test_type.value} test for {function_name}",
                    assertions=["assert result is not None"]
                )
                
                test_cases.append(test_case)
        
        return test_cases[:request.max_tests_per_function]
    
    async def _generate_class_tests(self, class_name: str,
                                  request: TestGenerationRequest) -> List[TestCase]:
        """Generate tests for a class."""
        # For now, generate basic class instantiation and method tests
        test_cases = []
        
        # Basic instantiation test
        test_case = TestCase(
            test_id=f"{class_name}_instantiation",
            name=f"test_{class_name}_instantiation",
            test_type=TestType.UNIT,
            framework=request.framework,
            code=f"""
def test_{class_name.lower()}_instantiation():
    \"\"\"Test {class_name} can be instantiated.\"\"\"
    instance = {class_name}()
    assert instance is not None
    assert isinstance(instance, {class_name})
""",
            description=f"Test {class_name} instantiation",
            assertions=[f"assert isinstance(instance, {class_name})"]
        )
        
        test_cases.append(test_case)
        return test_cases
    
    async def _generate_integration_tests(self, request: TestGenerationRequest) -> List[TestCase]:
        """Generate integration tests."""
        test_cases = []
        
        # Basic integration test template
        test_case = TestCase(
            test_id="integration_basic",
            name="test_integration_workflow",
            test_type=TestType.INTEGRATION,
            framework=request.framework,
            code="""
def test_integration_workflow():
    \"\"\"Test integration between components.\"\"\"
    # Setup integration environment
    # Execute workflow
    # Verify results
    assert True  # Replace with actual integration test
""",
            description="Basic integration test",
            assertions=["assert True"]
        )
        
        test_cases.append(test_case)
        return test_cases
    
    async def _generate_performance_tests(self, request: TestGenerationRequest) -> List[TestCase]:
        """Generate performance tests."""
        test_cases = []
        
        for function_name in request.code_context.functions[:3]:  # Limit to 3 functions
            test_case = TestCase(
                test_id=f"{function_name}_performance",
                name=f"test_{function_name}_performance",
                test_type=TestType.PERFORMANCE,
                framework=request.framework,
                code=f"""
def test_{function_name}_performance():
    \"\"\"Test {function_name} performance.\"\"\"
    import time
    
    start_time = time.time()
    for _ in range(100):
        {function_name}()
    execution_time = time.time() - start_time
    
    assert execution_time < 1.0, f"Performance test failed: {{execution_time:.3f}}s"
""",
                description=f"Performance test for {function_name}",
                assertions=[f"assert execution_time < 1.0"],
                estimated_execution_time=2.0
            )
            
            test_cases.append(test_case)
        
        return test_cases
    
    async def _generate_security_tests(self, request: TestGenerationRequest) -> List[TestCase]:
        """Generate security tests."""
        test_cases = []
        
        # SQL injection test
        test_case = TestCase(
            test_id="security_sql_injection",
            name="test_sql_injection_prevention",
            test_type=TestType.SECURITY,
            framework=request.framework,
            code="""
def test_sql_injection_prevention():
    \"\"\"Test SQL injection prevention.\"\"\"
    malicious_input = "'; DROP TABLE users; --"
    
    # Test that malicious input is properly handled
    try:
        result = process_user_input(malicious_input)
        assert 'DROP TABLE' not in str(result)
    except ValueError:
        # Expected to reject malicious input
        pass
""",
            description="Test SQL injection prevention",
            assertions=["assert 'DROP TABLE' not in str(result)"]
        )
        
        test_cases.append(test_case)
        return test_cases
    
    def _extract_function_context(self, function_name: str, code_context: CodeContext) -> Dict[str, Any]:
        """Extract context information for a specific function."""
        # Try to find function definition in code
        lines = code_context.content.split('\n')
        function_start = None
        function_code = ""
        
        for i, line in enumerate(lines):
            if f"def {function_name}" in line or f"function {function_name}" in line:
                function_start = i
                break
        
        if function_start is not None:
            # Extract function and a few lines of context
            end_line = min(function_start + 20, len(lines))
            function_code = '\n'.join(lines[function_start:end_line])
        
        return {
            'name': function_name,
            'code': function_code,
            'line_number': function_start,
            'language': code_context.language
        }
    
    def _extract_setup_requirements(self, code_context: CodeContext) -> List[str]:
        """Extract setup requirements from code context."""
        requirements = []
        
        # Add framework-specific requirements
        requirements.append(f"{code_context.language}-test-framework")
        
        # Add imports as potential requirements
        for import_name in code_context.imports:
            if not import_name.startswith('.'):  # Skip relative imports
                requirements.append(import_name)
        
        return list(set(requirements))  # Remove duplicates
    
    def _estimate_coverage(self, test_cases: List[TestCase], code_context: CodeContext) -> float:
        """Estimate test coverage percentage."""
        if not test_cases:
            return 0.0
        
        # Simple heuristic: coverage based on number of functions tested
        functions_with_tests = set()
        
        for test_case in test_cases:
            # Extract function name from test name
            for function_name in code_context.functions:
                if function_name in test_case.name:
                    functions_with_tests.add(function_name)
        
        if not code_context.functions:
            return 90.0  # Assume high coverage if no functions detected
        
        coverage = (len(functions_with_tests) / len(code_context.functions)) * 100
        
        # Adjust based on test types
        if any(tc.test_type == TestType.INTEGRATION for tc in test_cases):
            coverage += 10
        if any(tc.test_type == TestType.PERFORMANCE for tc in test_cases):
            coverage += 5
        if any(tc.test_type == TestType.SECURITY for tc in test_cases):
            coverage += 5
        
        return min(100.0, coverage)
    
    async def analyze_test_quality(self, test_suite: TestSuite) -> TestAnalysis:
        """Analyze the quality of generated tests."""
        coverage_analysis = {
            CoverageType.STATEMENT: self._estimate_statement_coverage(test_suite),
            CoverageType.BRANCH: self._estimate_branch_coverage(test_suite),
            CoverageType.FUNCTION: self._estimate_function_coverage(test_suite),
            CoverageType.LINE: self._estimate_line_coverage(test_suite)
        }
        
        test_distribution = {}
        for test_type in TestType:
            count = sum(1 for tc in test_suite.test_cases if tc.test_type == test_type)
            if count > 0:
                test_distribution[test_type] = count
        
        quality_score = self._calculate_quality_score(test_suite, coverage_analysis)
        
        missing_areas = self._identify_missing_coverage(test_suite)
        recommendations = self._generate_test_recommendations(test_suite, coverage_analysis)
        potential_issues = self._identify_potential_issues(test_suite)
        
        return TestAnalysis(
            total_tests=len(test_suite.test_cases),
            coverage_analysis=coverage_analysis,
            test_distribution=test_distribution,
            quality_score=quality_score,
            missing_coverage_areas=missing_areas,
            recommendations=recommendations,
            potential_issues=potential_issues
        )
    
    def _estimate_statement_coverage(self, test_suite: TestSuite) -> float:
        """Estimate statement coverage."""
        return min(100.0, test_suite.total_coverage_estimate)
    
    def _estimate_branch_coverage(self, test_suite: TestSuite) -> float:
        """Estimate branch coverage."""
        return min(100.0, test_suite.total_coverage_estimate * 0.8)
    
    def _estimate_function_coverage(self, test_suite: TestSuite) -> float:
        """Estimate function coverage."""
        return min(100.0, test_suite.total_coverage_estimate * 0.9)
    
    def _estimate_line_coverage(self, test_suite: TestSuite) -> float:
        """Estimate line coverage."""
        return min(100.0, test_suite.total_coverage_estimate * 0.85)
    
    def _calculate_quality_score(self, test_suite: TestSuite, 
                               coverage_analysis: Dict[CoverageType, float]) -> float:
        """Calculate overall test quality score."""
        if not test_suite.test_cases:
            return 0.0
        
        # Base score from coverage
        avg_coverage = sum(coverage_analysis.values()) / len(coverage_analysis)
        score = avg_coverage
        
        # Bonus for test diversity
        test_types = set(tc.test_type for tc in test_suite.test_cases)
        diversity_bonus = len(test_types) * 5
        score += diversity_bonus
        
        # Bonus for assertions
        total_assertions = sum(len(tc.assertions) for tc in test_suite.test_cases)
        avg_assertions = total_assertions / len(test_suite.test_cases)
        assertion_bonus = min(20, avg_assertions * 5)
        score += assertion_bonus
        
        # Penalty for missing setup/teardown where needed
        complex_tests = [tc for tc in test_suite.test_cases 
                        if tc.test_type in [TestType.INTEGRATION, TestType.PERFORMANCE]]
        if complex_tests:
            setup_ratio = sum(1 for tc in complex_tests if tc.setup_code) / len(complex_tests)
            setup_penalty = (1.0 - setup_ratio) * 10
            score -= setup_penalty
        
        return min(100.0, max(0.0, score))
    
    def _identify_missing_coverage(self, test_suite: TestSuite) -> List[str]:
        """Identify areas missing test coverage."""
        missing_areas = []
        
        test_types_present = set(tc.test_type for tc in test_suite.test_cases)
        
        if TestType.UNIT not in test_types_present:
            missing_areas.append("Unit tests")
        if TestType.INTEGRATION not in test_types_present:
            missing_areas.append("Integration tests")
        if TestType.PERFORMANCE not in test_types_present:
            missing_areas.append("Performance tests")
        if TestType.SECURITY not in test_types_present:
            missing_areas.append("Security tests")
        
        # Check for error handling tests
        error_tests = [tc for tc in test_suite.test_cases 
                      if any('exception' in assertion.lower() or 'error' in assertion.lower() 
                            for assertion in tc.assertions)]
        if not error_tests:
            missing_areas.append("Error handling tests")
        
        return missing_areas
    
    def _generate_test_recommendations(self, test_suite: TestSuite, 
                                     coverage_analysis: Dict[CoverageType, float]) -> List[str]:
        """Generate recommendations for improving tests."""
        recommendations = []
        
        avg_coverage = sum(coverage_analysis.values()) / len(coverage_analysis)
        
        if avg_coverage < 70:
            recommendations.append("Increase test coverage by adding more unit tests")
        
        if not any(tc.test_type == TestType.INTEGRATION for tc in test_suite.test_cases):
            recommendations.append("Add integration tests to verify component interactions")
        
        if not any(tc.test_type == TestType.PERFORMANCE for tc in test_suite.test_cases):
            recommendations.append("Consider adding performance tests for critical functions")
        
        # Check assertion density
        total_assertions = sum(len(tc.assertions) for tc in test_suite.test_cases)
        if test_suite.test_cases:
            avg_assertions = total_assertions / len(test_suite.test_cases)
            if avg_assertions < 2:
                recommendations.append("Increase assertion coverage - add more assertions per test")
        
        return recommendations
    
    def _identify_potential_issues(self, test_suite: TestSuite) -> List[str]:
        """Identify potential issues with the test suite."""
        issues = []
        
        if not test_suite.test_cases:
            issues.append("No test cases generated")
            return issues
        
        # Check for tests without assertions
        no_assertion_tests = [tc for tc in test_suite.test_cases if not tc.assertions]
        if no_assertion_tests:
            issues.append(f"{len(no_assertion_tests)} tests have no assertions")
        
        # Check for overly long test names
        long_name_tests = [tc for tc in test_suite.test_cases if len(tc.name) > 80]
        if long_name_tests:
            issues.append(f"{len(long_name_tests)} tests have overly long names")
        
        # Check for duplicate test names
        test_names = [tc.name for tc in test_suite.test_cases]
        if len(test_names) != len(set(test_names)):
            issues.append("Duplicate test names detected")
        
        return issues


# Global instance
ai_test_generator = AITestGenerator()