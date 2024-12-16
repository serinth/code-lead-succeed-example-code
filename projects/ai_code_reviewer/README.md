# AI Code Reviewer aka Pull Pal

Uses a local LLM to provide code reviews that focuses on security, readability and testability.

## Getting started
```bash
ollama pull <model name>
uv run main.py
```

## Example diff in Python
```python
@@ -1,5 +1,7 @@
-def process_user_input(data):
+def process_user_input(data: dict) -> bool:
        try:
-        result = eval(data['command'])
-        return result
+        if 'command' in data:
+            result = eval(data['command'])  # nosec
+            return bool(result)
+        return False
        except:
            return False
```

The PR comment looks like this when running the [codeqwen](https://ollama.com/library/codeqwen) model (90+ languages, 7B params):
```
READABILITY:
- The function 'process_user_input' should have a clear docstring explaining its purpose and parameters.

TESTABILITY:
- Add unit tests for the function 'process_user_input' to ensure it works as expected.

SECURITY:
- Use of eval() function can lead to code injection. Consider using safer alternatives like ast.literal_eval().
- The return type of the function should be explicitly defined in its signature and return a boolean value for consistency
```