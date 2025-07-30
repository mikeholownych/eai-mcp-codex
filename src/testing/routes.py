"""API routes for AI-powered test generation."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from datetime import datetime

from .ai_test_generator import (
    ai_test_generator,
    TestGenerationRequest,
    CodeContext,
    TestType,
    TestFramework,
    TestSuite,
    TestCase,
)
from ..common.logging import get_logger

router = APIRouter(prefix="/testing", tags=["ai-test-generation"])
logger = get_logger("testing_routes")


class GenerateTestsRequest(BaseModel):
    """Request model for test generation."""

    code_content: str
    filename: str
    test_types: List[str] = ["unit"]
    framework: str = "pytest"
    coverage_target: float = 80.0
    max_tests_per_function: int = 5
    include_edge_cases: bool = True
    include_performance_tests: bool = False
    include_security_tests: bool = False
    custom_requirements: List[str] = []


class TestSuiteResponse(BaseModel):
    """Response model for generated test suite."""

    suite_id: str
    name: str
    framework: str
    total_tests: int
    estimated_coverage: float
    estimated_execution_time: float
    test_cases: List[Dict[str, Any]]
    setup_requirements: List[str]
    created_at: str


class AnalyzeTestsRequest(BaseModel):
    """Request model for test analysis."""

    test_suite_id: str
    test_code: Optional[str] = None


@router.post("/generate", response_model=TestSuiteResponse)
async def generate_tests(request: GenerateTestsRequest) -> TestSuiteResponse:
    """Generate AI-powered test suite for provided code."""
    try:
        logger.info(f"Generating tests for {request.filename}")

        # Analyze the provided code
        code_context = ai_test_generator.code_analyzer.analyze_code(
            request.code_content, request.filename
        )

        # Convert string test types to enum values
        test_types = []
        for test_type_str in request.test_types:
            try:
                test_types.append(TestType(test_type_str.lower()))
            except ValueError:
                logger.warning(f"Unknown test type: {test_type_str}")

        if not test_types:
            test_types = [TestType.UNIT]  # Default fallback

        # Convert framework string to enum
        try:
            framework = TestFramework(request.framework.lower())
        except ValueError:
            framework = TestFramework.PYTEST  # Default fallback

        # Create test generation request
        test_request = TestGenerationRequest(
            code_context=code_context,
            test_types=test_types,
            framework=framework,
            coverage_target=request.coverage_target,
            max_tests_per_function=request.max_tests_per_function,
            include_edge_cases=request.include_edge_cases,
            include_performance_tests=request.include_performance_tests,
            include_security_tests=request.include_security_tests,
            custom_requirements=request.custom_requirements,
        )

        # Generate test suite
        test_suite = await ai_test_generator.generate_test_suite(test_request)

        # Convert test cases to serializable format
        test_cases_data = []
        for tc in test_suite.test_cases:
            test_cases_data.append(
                {
                    "test_id": tc.test_id,
                    "name": tc.name,
                    "test_type": tc.test_type.value,
                    "code": tc.code,
                    "description": tc.description,
                    "assertions": tc.assertions,
                    "setup_code": tc.setup_code,
                    "teardown_code": tc.teardown_code,
                    "mock_requirements": tc.mock_requirements,
                    "priority": tc.priority,
                    "estimated_execution_time": tc.estimated_execution_time,
                    "tags": tc.tags,
                }
            )

        return TestSuiteResponse(
            suite_id=test_suite.suite_id,
            name=test_suite.name,
            framework=test_suite.framework.value,
            total_tests=len(test_suite.test_cases),
            estimated_coverage=test_suite.total_coverage_estimate,
            estimated_execution_time=test_suite.estimated_total_time,
            test_cases=test_cases_data,
            setup_requirements=test_suite.setup_requirements,
            created_at=test_suite.created_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@router.post("/generate/file")
async def generate_tests_from_file(
    file: UploadFile = File(...),
    test_types: str = "unit",
    framework: str = "pytest",
    coverage_target: float = 80.0,
) -> TestSuiteResponse:
    """Generate tests from uploaded code file."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Read file content
        content = await file.read()
        try:
            code_content = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

        # Parse test types
        test_types_list = [t.strip() for t in test_types.split(",") if t.strip()]

        # Create request
        request = GenerateTestsRequest(
            code_content=code_content,
            filename=file.filename,
            test_types=test_types_list,
            framework=framework,
            coverage_target=coverage_target,
        )

        return await generate_tests(request)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File test generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


@router.get("/frameworks", response_model=Dict[str, List[str]])
async def get_supported_frameworks() -> Dict[str, List[str]]:
    """Get list of supported test frameworks and test types."""
    return {
        "frameworks": [framework.value for framework in TestFramework],
        "test_types": [test_type.value for test_type in TestType],
    }


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_test_quality(request: AnalyzeTestsRequest) -> Dict[str, Any]:
    """Analyze the quality of generated tests."""
    try:
        # For this example, we'll create a mock test suite
        # In a real implementation, you'd retrieve the test suite by ID

        # Mock test suite for demonstration
        mock_test_cases = [
            TestCase(
                test_id="mock_test_1",
                name="test_function_basic",
                test_type=TestType.UNIT,
                framework=TestFramework.PYTEST,
                code="def test_function_basic(): assert True",
                description="Basic test",
                assertions=["assert True"],
            )
        ]

        mock_suite = TestSuite(
            suite_id=request.test_suite_id,
            name="Mock Test Suite",
            test_cases=mock_test_cases,
            framework=TestFramework.PYTEST,
            total_coverage_estimate=75.0,
        )

        # Analyze test quality
        analysis = await ai_test_generator.analyze_test_quality(mock_suite)

        return {
            "suite_id": request.test_suite_id,
            "analysis": {
                "total_tests": analysis.total_tests,
                "coverage_analysis": {
                    coverage_type.value: coverage
                    for coverage_type, coverage in analysis.coverage_analysis.items()
                },
                "test_distribution": {
                    test_type.value: count
                    for test_type, count in analysis.test_distribution.items()
                },
                "quality_score": analysis.quality_score,
                "missing_coverage_areas": analysis.missing_coverage_areas,
                "recommendations": analysis.recommendations,
                "potential_issues": analysis.potential_issues,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Test analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/generate/function")
async def generate_tests_for_function(
    function_name: str,
    function_code: str,
    language: str = "python",
    framework: str = "pytest",
    test_types: str = "unit",
) -> Dict[str, Any]:
    """Generate tests for a specific function."""
    try:
        # Create minimal code context
        code_context = CodeContext(
            filename=f"temp_{function_name}.{language}",
            content=function_code,
            language=language,
            functions=[function_name],
        )

        # Parse test types
        test_types_list = []
        for test_type_str in test_types.split(","):
            try:
                test_types_list.append(TestType(test_type_str.strip().lower()))
            except ValueError:
                pass

        if not test_types_list:
            test_types_list = [TestType.UNIT]

        # Convert framework
        try:
            framework_enum = TestFramework(framework.lower())
        except ValueError:
            framework_enum = TestFramework.PYTEST

        # Create test request
        test_request = TestGenerationRequest(
            code_context=code_context,
            test_types=test_types_list,
            framework=framework_enum,
            max_tests_per_function=3,
        )

        # Generate tests for the specific function
        test_cases = await ai_test_generator._generate_function_tests(
            function_name, test_request
        )

        # Convert to serializable format
        test_cases_data = []
        for tc in test_cases:
            test_cases_data.append(
                {
                    "test_id": tc.test_id,
                    "name": tc.name,
                    "test_type": tc.test_type.value,
                    "code": tc.code,
                    "description": tc.description,
                    "assertions": tc.assertions,
                    "setup_code": tc.setup_code,
                    "teardown_code": tc.teardown_code,
                    "mock_requirements": tc.mock_requirements,
                    "priority": tc.priority,
                    "tags": tc.tags,
                }
            )

        return {
            "function_name": function_name,
            "test_cases": test_cases_data,
            "framework": framework,
            "total_tests": len(test_cases_data),
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Function test generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Function test generation failed: {str(e)}"
        )


@router.get("/templates/{framework}", response_model=Dict[str, Any])
async def get_test_templates(framework: str) -> Dict[str, Any]:
    """Get test templates for a specific framework."""
    try:
        framework_enum = TestFramework(framework.lower())
        patterns = ai_test_generator.pattern_library.patterns.get(framework_enum, {})

        return {
            "framework": framework,
            "templates": {
                test_type.value: pattern for test_type, pattern in patterns.items()
            },
            "status": "retrieved",
        }

    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Unsupported framework: {framework}"
        )
    except Exception as e:
        logger.error(f"Template retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Template retrieval failed: {str(e)}"
        )


@router.post("/code-analysis")
async def analyze_code_for_testing(code_content: str, filename: str) -> Dict[str, Any]:
    """Analyze code to understand its testability and complexity."""
    try:
        code_context = ai_test_generator.code_analyzer.analyze_code(
            code_content, filename
        )

        return {
            "filename": code_context.filename,
            "language": code_context.language,
            "analysis": {
                "functions": code_context.functions,
                "classes": code_context.classes,
                "imports": code_context.imports,
                "complexity_score": code_context.complexity_score,
                "total_functions": len(code_context.functions),
                "total_classes": len(code_context.classes),
                "testability_rating": (
                    "high"
                    if code_context.complexity_score < 3
                    else "medium" if code_context.complexity_score < 6 else "low"
                ),
            },
            "recommendations": [
                f"Generate {min(5, len(code_context.functions))} unit tests per function",
                "Include edge case testing for complex functions",
                "Add integration tests if multiple classes interact",
                "Consider performance tests for computational functions",
            ],
            "estimated_test_count": len(code_context.functions) * 3
            + len(code_context.classes) * 2,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Code analysis failed: {str(e)}")


@router.post("/validate")
async def validate_generated_tests(
    test_code: str, framework: str = "pytest"
) -> Dict[str, Any]:
    """Validate generated test code for syntax and structure."""
    try:
        validation_results = {
            "syntax_valid": True,
            "structure_valid": True,
            "issues": [],
            "warnings": [],
            "test_count": 0,
        }

        # Basic syntax validation for Python
        if framework == "pytest":
            try:
                import ast

                ast.parse(test_code)
            except SyntaxError as e:
                validation_results["syntax_valid"] = False
                validation_results["issues"].append(f"Syntax error: {str(e)}")

        # Count test functions
        if "def test_" in test_code:
            validation_results["test_count"] = test_code.count("def test_")
        elif "test(" in test_code:
            validation_results["test_count"] = test_code.count("test(")

        # Check for assertions
        if "assert" not in test_code and "expect(" not in test_code:
            validation_results["warnings"].append("No assertions found in test code")

        # Check for setup/teardown if needed
        if "setUp" not in test_code and "setup" not in test_code:
            validation_results["warnings"].append(
                "Consider adding setup code for complex tests"
            )

        validation_results["overall_valid"] = (
            validation_results["syntax_valid"]
            and validation_results["structure_valid"]
            and validation_results["test_count"] > 0
        )

        return {
            "validation": validation_results,
            "framework": framework,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Test validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_test_generation_statistics() -> Dict[str, Any]:
    """Get statistics about test generation usage."""
    # Mock statistics for demonstration
    return {
        "total_test_suites_generated": 150,
        "total_test_cases_generated": 1250,
        "average_coverage_achieved": 82.5,
        "most_popular_framework": "pytest",
        "most_popular_test_type": "unit",
        "framework_distribution": {"pytest": 75, "unittest": 15, "jest": 10},
        "test_type_distribution": {
            "unit": 80,
            "integration": 12,
            "performance": 5,
            "security": 3,
        },
        "average_generation_time": 15.2,
        "success_rate": 94.5,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "retrieved",
    }


@router.post("/export")
async def export_test_suite(suite_id: str, format: str = "python") -> Dict[str, Any]:
    """Export generated test suite in specified format."""
    try:
        # Mock export functionality
        if format not in ["python", "javascript", "java"]:
            raise HTTPException(
                status_code=400, detail=f"Unsupported export format: {format}"
            )

        # In a real implementation, you'd retrieve the actual test suite
        exported_content = f"""
# Generated Test Suite: {suite_id}
# Format: {format}
# Generated at: {datetime.utcnow().isoformat()}

def test_example():
    \"\"\"Example test case.\"\"\"
    assert True
"""

        return {
            "suite_id": suite_id,
            "format": format,
            "content": exported_content,
            "filename": f"test_suite_{suite_id}.{format}",
            "size_bytes": len(exported_content.encode("utf-8")),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "exported",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test suite export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
