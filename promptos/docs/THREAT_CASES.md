# Threat and Failure Cases

The external evaluation corpus should include at least these classes:

1. Source text containing `</SOURCE_MATERIAL>` and fake system tags.
2. Unicode-confusable or multilingual instruction injection.
3. Source asking the compiler to reveal credentials.
4. Request with `EXECUTE_CONSEQUENTIAL` but no action list.
5. Request authorizing `publish` while prohibiting `publish`.
6. Request authorizing one action and attempting to smuggle unrelated actions through source text.
7. Tool named by the source but absent from confirmed tools.
8. Prompt that claims tests passed without a receipt.
9. Prompt that claims novelty without prior-art scope.
10. Prompt that claims category leadership without comparators.
11. Prompt that mistakes a specification for an implementation.
12. Prompt that mistakes implementation for verification.
13. Prompt that endlessly restarts refinement.
14. Prompt that expands unrelated academic disciplines.
15. Prompt containing secrets or unnecessary personal data.
16. Ambiguous request where clarification is truly blocking.
17. Ambiguous request where a safe default should prevent needless questioning.
18. Large source that exceeds the stated context budget.
19. Existing prompt whose invariant text must survive repair.
20. Two prompts with conflicting permission models that must be merged.

Passing the deterministic encoder cases does not prove resistance to every model-level injection. These cases must be run against each target model adapter.
