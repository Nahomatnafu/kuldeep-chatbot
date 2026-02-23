# AI Assistant Prompt: Collective RAG Chatbot Merge

## Context
You are an expert AI coding assistant helping to merge the best features from multiple experimental RAG chatbot branches into a unified, production-ready chatbot with a new Figma-designed frontend.

## Your Mission
Analyze each team member's branch, identify the actual best implementations (not assumptions), and systematically merge them into a new `collective-experiment` branch that combines the strongest features from all approaches.

## Important Guidelines

### 🔍 **Verify, Don't Assume**
- **DO NOT** take the initial analysis in `COLLECTIVE_MERGE_PLAN.md` or `rag_reflection.md` as absolute truth
- **VERIFY** each claimed feature by actually examining the code in each branch
- **CONFIRM** which branch truly has the best implementation before copying code
- **QUESTION** assumptions - what we think is in Dilasha's branch might actually be in Jake's, or vice versa
- **DOCUMENT** what you actually find vs. what was claimed

### 📊 **Systematic Analysis Approach**
For each branch (`rag-experiment-nahom`, `rag-experiment-jake`, `rag-experiment-dilasha`):

1. **Checkout the branch** and examine the actual code
2. **Document the file structure** - what files exist, what's their purpose
3. **Identify key features** by reading the code, not by assumption:
   - How is document upload handled? (if at all)
   - How is the vector database configured? (Chroma? In-memory? Persistent?)
   - What does the frontend look like? (components, styling, features)
   - How are references/sources displayed?
   - What's the prompt engineering approach?
   - How fast is it? (based on code structure, not claims)
4. **Test if possible** - run the code to see what actually works
5. **Rate the implementation** - is this actually the best approach for this feature?

### 🎯 **Feature Verification Checklist**

For each feature, determine:
- ✅ **Which branch(es) actually have this feature?**
- ✅ **Which implementation is cleanest/most robust?**
- ✅ **Are there any hidden gems in branches we didn't expect?**

Key features to verify:
- [ ] Chroma DB with persistence (claimed: Dilasha - verify this!)
- [ ] Document upload interface (claimed: Jake & Dilasha - compare implementations)
- [ ] Sidebar for document management (claimed: Dilasha - confirm it exists)
- [ ] Delete document functionality (claimed: Dilasha - verify)
- [ ] Page number references (claimed: Dilasha - check implementation)
- [ ] Clickable PDF links (claimed: Dilasha - does this actually work?)
- [ ] Strict grounding prompts (claimed: Nahom & Dilasha - compare approaches)
- [ ] Response speed optimization (claimed: Nahom - what makes it faster?)

### 📝 **Documentation Requirements**

As you analyze each branch, create/update `BRANCH_ANALYSIS.md` with:

```markdown
# Branch Analysis - Actual Findings

## rag-experiment-nahom
**Claimed Features:** [list from rag_reflection.md]
**Actual Features Found:** [what you actually discovered]
**File Structure:** [key files and their purposes]
**Standout Implementations:** [what's genuinely good here]
**Potential Issues:** [what might not work well]
**Code Snippets:** [key code worth preserving]

## rag-experiment-jake
[same structure]

## rag-experiment-dilasha
[same structure]

## Comparison Matrix
| Feature | Nahom | Jake | Dilasha | Best Implementation |
|---------|-------|------|---------|---------------------|
| Chroma Persistence | ? | ? | ? | ? |
[etc.]

## Recommendations
Based on actual code analysis, here's what we should merge...
```

### 🚀 **Execution Strategy**

1. **Phase 1: Discovery (Don't Skip This!)**
   - Checkout each branch one by one
   - Read the actual code
   - Run the applications if possible
   - Document what you find vs. what was claimed
   - Update `BRANCH_ANALYSIS.md` with real findings

2. **Phase 2: Plan Refinement**
   - Based on your discoveries, update `COLLECTIVE_MERGE_PLAN.md`
   - Adjust which features come from which branches
   - Identify any features we missed or misattributed
   - Flag any claimed features that don't actually exist

3. **Phase 3: Systematic Merge**
   - Create `collective-experiment` branch
   - Merge features in order of dependency (database → backend → frontend)
   - Test after each major integration
   - Document any deviations from the original plan

4. **Phase 4: Integration & Testing**
   - Integrate the Figma frontend from `Figma-Chatbot-Recreation-codebase/`
   - Connect all pieces together
   - Test the complete workflow
   - Document any issues or improvements needed

### ⚠️ **Red Flags to Watch For**

- Claims in `rag_reflection.md` that don't match the actual code
- Features that exist but don't work as described
- Better implementations in unexpected branches
- Missing dependencies or broken code
- Conflicting approaches that can't be easily merged

### 💡 **Key Questions to Answer**

As you work through this, continuously ask:
1. "Does this feature actually exist in this branch?"
2. "Is this implementation actually better than the alternatives?"
3. "What makes this approach superior?" (speed? code quality? features?)
4. "Are there hidden features we haven't noticed?"
5. "Will these features work well together when merged?"

### 🎯 **Success Criteria**

You've succeeded when:
- ✅ You've verified every claimed feature by examining actual code
- ✅ You've documented what you found vs. what was claimed
- ✅ You've identified the genuinely best implementation for each feature
- ✅ You've created a working `collective-experiment` branch
- ✅ The merged chatbot has all the best features working together
- ✅ The Figma frontend is integrated and functional
- ✅ You can explain why you chose each implementation

### 📂 **Files to Reference**

- `COLLECTIVE_MERGE_PLAN.md` - Initial plan (treat as hypothesis, not fact)
- `rag_reflection.md` - Team observations (verify these claims)
- `Figma-Chatbot-Recreation-codebase/` - Frontend to integrate
- Each branch's actual code - **THE SOURCE OF TRUTH**

### 🗣️ **Communication Style**

As you work:
- **Be transparent** about what you're finding vs. what was expected
- **Ask for confirmation** when you find discrepancies
- **Explain your reasoning** for choosing one implementation over another
- **Flag uncertainties** - if you're not sure which is better, say so
- **Celebrate discoveries** - if you find something better than expected, share it!

---

## Your First Steps

1. Read `COLLECTIVE_MERGE_PLAN.md` to understand the initial hypothesis
2. Read `rag_reflection.md` to see what the team observed
3. Checkout `rag-experiment-jake` and start your investigation
4. Document your findings in `BRANCH_ANALYSIS.md`
5. Continue with the other branches
6. Report back with what you actually found

Remember: **The code is the truth. Everything else is just a hypothesis to be verified.**

Good luck! 🚀

