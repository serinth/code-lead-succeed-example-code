# AI Code Reviewer aka Pull Pal

Uses a local LLM to provide code reviews that focuses on security, readability and testability. See [improvements](#improvements) below for further considerations.

## Getting started
Setup a `.secrets.toml`. Fill it out with values that you get from setting up the webhook in GitHub. See the emplaybook article for examples but it's fairly self explanatory.

```toml
[github]
token = "<your github token with pr r/w access>"
webhook_secret = "<webhook secret>"
```
Then:

```bash
ollama pull <model name>
uv run main.py
```
This will run a service on port 8000 for the incoming webhook.

Otherwise `uv run main.py example` and it'll run the baked in example below just to make sure you have Ollama working or you want to see how different models work. 

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

## Improvements <a name="improvements"></a>
This provides the core scaffolding to get everything working. The review quality itself can be improved by:

- Trying out different models. They're changing almost monthly now so you won't know what you're gonna get
- Customizing and training your own model
- Changing the prompt to focus on different concerns
- Modifying the type of files it looks at so it ignores settings files, project files etc and only looks at pure code diffs.
- Potentially spitting out code suggestions as well.