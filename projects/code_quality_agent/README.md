# Code Quality Agent

TODO:
- [x] Create subgraph for context analysis
- [x] Create subgraph for code quality
- [x] Consistentout output of context analysis - integration tests passed 20 times
- [ ] Comprehensive scenarios for code quality
- [ ] Consistent output of code quality - integration tests passed 10 times
- [ ] Add human in the loop for code quality
- [ ] Connect context analysis graph to code quality graph
- [ ] Add caching for pull requests
- [ ] Add scoring for overall quality by person
- [ ] Add app DB to store results
- [ ] Add human entrypoint for entire graph
- [ ] Add agent entrypoint for entire graph

## Running tests
This project depends on local LLMs which can take a long time to run.
Specifically choose files to run like this:
```bash
uv run pytest graphs/code_quality_graph_test.py -s -v --log-cli-level=DEBUG
```

Or all of them like this:
```bash
uv run pytest
```

## Improvements

## References
[LangChain Toolkits](https://python.langchain.com/docs/integrations/tools/)
