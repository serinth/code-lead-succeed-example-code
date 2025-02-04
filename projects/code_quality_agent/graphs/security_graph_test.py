
import pytest
from typing import List
from dataclasses import dataclass
from langchain_ollama.llms import OllamaLLM
from models.decision import Decision
from datetime import datetime
from models.employee import Employee
from models.levels import SeniorityLevel
from states.code_quality_state import CodeQualityEvaluation
from graphs.code_quality_graph import create_analysis_graph
from edges.security_edges import prepare_pr_for_security_analysis, process_llm_response_for_security_assessment
from code_analysis_tool.models.pull_request import PullRequest
from code_analysis_tool.models.user import User
from code_analysis_tool.models.repository import Repository

@dataclass
class TestCase:
    name: str
    employee: Employee
    pr: PullRequest
    expected_min_quality_score: float
    expected_min_confidence: float
    confidence_tolerance: float = 0.2

SQL_INJECTION_CODE_DIFF_1 = """
diff --git a/src/controllers/user_controller.py b/src/controllers/user_controller.py
index 2a7b981..4c8d123 100644
--- a/src/controllers/user_controller.py
+++ b/src/controllers/user_controller.py
@@ -15,9 +15,10 @@ class UserController:
     def __init__(self, db_connection):
         self.db = db_connection
 
-    def get_user_orders(self, user_id):
-        query = "SELECT * FROM orders WHERE user_id = ?"
-        return self.db.execute(query, (user_id,))
+    def get_user_orders(self, user_id, sort_column='date'):
+        # Allow dynamic sorting by any column
+        query = f"SELECT * FROM orders WHERE user_id = '{{user_id}}' ORDER BY {{sort_column}}"
+        return self.db.execute(query)
 
     def search_users(self, search_term):
-        query = "SELECT * FROM users WHERE username LIKE ?"
-        return self.db.execute(query, (f"%{{search_term}}%",))
+        # Direct string concatenation for flexibility
+        query = "SELECT * FROM users WHERE username LIKE '%" + search_term + "%'"
+        return self.db.execute(query)
+
+    def update_user_role(self, username, new_role):
+        # Add ability to update user roles
+        query = "UPDATE users SET role = '" + new_role + "' WHERE username = '" + username + "'"
+        self.db.execute(query)
+        return True
+
"""
SQL_INJECTION_CODE_DIFF_2 = """
diff --git a/src/routes/admin.py b/src/routes/admin.py
index 9a76543..2b7c123 100644
--- a/src/routes/admin.py
+++ b/src/routes/admin.py
@@ -8,6 +8,14 @@ def init_admin_routes(app):
     def admin_dashboard():
         return render_template('admin/dashboard.html')
 
+    @app.route('/admin/reports')
+    def custom_report():
+        # Allow admins to run custom queries
+        custom_query = request.args.get('query', '')
+        if custom_query:
+            results = db.execute(custom_query)
+            return jsonify(results)
+        return render_template('admin/reports.html')
+
     @app.route('/admin/users')
     def list_users():
-        users = db.query("SELECT id, username, email FROM users")
+        search = request.args.get('search', '')
+        users = db.execute("SELECT * FROM users WHERE username LIKE '%" + search + "%' OR email LIKE '%" + search + "%'")
         return render_template('admin/users.html', users=users)
"""

user = User(
        id="user_id",
        login="user_login"
    )

repo = Repository(
        id="repository_id",
        name="repository_name",
        full_name="repository_full_name",
        owner=user
    )

injection_test_cases: List[TestCase] = [
    TestCase(
        name="Senior engineer submitting well-structured code",
        employee=Employee(
            id="senior@company.com",
            cvs_username="senior_dev",
            seniority_level=SeniorityLevel.SENIOR.value,
            expected_prs_per_week=2,
            tenure_months=24,
            pr_count=3
        ),
        pr=PullRequest(
            id="pr_id",
            number=1,
            title="Improve input validation with Pydantic",
            author=user,
            repository=repo,
            created_at=datetime.now(),
            merged=False,
            merged_at=None,
            description="Improve input validation with Pydantic",
            file_diffs= {
                "src/controllers/user_controller.py": SQL_INJECTION_CODE_DIFF_1,
                "src/routes/admin.py": SQL_INJECTION_CODE_DIFF_2
            }
        ),
        expected_min_quality_score=20.0,
        expected_min_confidence=0.8
    )
]

@pytest.fixture
def llm() -> OllamaLLM:
    return OllamaLLM(
        model="deepseek-v2:16b",
        temperature=0.0,
        base_url="http://localhost:11434"
    )

@pytest.fixture
def one_test_case() -> TestCase:
    return injection_test_cases[0]

@pytest.mark.parametrize("test_case", injection_test_cases)
def test_code_quality_analysis(
    test_case: TestCase,
    llm: OllamaLLM
) -> None:
    initial_state = CodeQualityEvaluation(employee_id=test_case.employee.id)

    # Act
    graph = create_analysis_graph(
        llm=llm, pr=test_case.pr, 
        state_class=CodeQualityEvaluation, 
        prepare_function=prepare_pr_for_security_analysis, 
        process_function=process_llm_response_for_security_assessment, 
        agent_name="code_security"
        )
    final_state = graph.invoke(initial_state)
    final_state = CodeQualityEvaluation(**final_state)

    # Assert
    assert final_state.evaluation is not None, "There should be pull request evaluations"
    

    assert final_state.evaluation.score <= test_case.expected_min_quality_score, \
        f"Quality score is too high for intentional security issues for case '{test_case.name}' with threshold  {final_state.evaluation.threshold}"
    
    assert final_state.evaluation.final_decision == Decision.FAIL, \
        f"Expected security assessment to fail for case '{test_case.name}'"
    
 
# def test_error_handling(
#     llm: OllamaLLM,
#     one_test_case: TestCase
# ) -> None:
#     class InvalidState(BaseModel):
#         pass

#     try:
#         # Test with invalid state
#         invalid_state = None
#         pr = Mock(spec=PullRequest)
#         graph = create_analysis_graph(
#             llm=llm, pr=one_test_case.pr, 
#             state_class=InvalidState, 
#             prepare_function=prepare_pr_for_analysis, 
#             process_function=process_llm_response_for_code_quality_assessment, 
#             agent_name="fail_agent"
#             )
        
#         with pytest.raises(Exception):
#             graph.invoke(invalid_state)

#     except Exception as e:
#         logger.error(f"Error handling test failed: {str(e)}")
#         raise 