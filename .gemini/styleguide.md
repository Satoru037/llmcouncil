<!-- @format -->

# Code Review Expectations for This Repository

Perform an **exhaustive, severity-prioritized** review of all pull requests.  
Your review **must always surface Critical and High issues first** before showing Medium or Low issues.

---

## 🔺 Severity-First Ordering (MANDATORY)

When reviewing code:

1. **Always detect and list Critical issues first.**
2. Then list **High** issues.
3. Then **Medium**.
4. Then **Low**.

Do NOT mention Medium or Low issues if **any** Critical or High issues remain unreported.

---

## 📝 Summary Structure (MANDATORY)

Your main PR summary comment must follow this exact structure:

### **Critical Issues**

- list each one with file + line
- include a diff/patch

### **High Issues**

- list each one with file + line
- include a diff/patch

### **Medium Issues**

- list each one with file + line
- include a diff/patch

### **Low Issues**

- list each one with file + line
- include a diff/patch

The summary must always appear in this order, even if some sections are empty.

---

## 🧩 For Every Issue Found

- Label severity explicitly: `[Critical]`, `[High]`, `[Medium]`, or `[Low]`.
- Provide a **one-line explanation** of what is wrong and why.
- Provide a **unified diff or inline code patch** that the maintainer can apply.
- Each suggestion must be **small, targeted, and actionable**.
- Reference **file + line range** for clarity.
- If multiple issues exist in the same file, list each separately.

---

## 🔍 Required Review Coverage Areas

### 1. Correctness

- Bug risks
- Edge cases
- Incorrect logic
- Data validation issues

### 2. Security

- Vulnerabilities
- Injection risks
- Secret leakage
- Unsafe patterns

### 3. Performance

- Inefficient operations
- Redundant work
- Hot-path issues

### 4. Readability & Maintainability

- Naming
- Complexity
- Code smells
- Inconsistent structures

---

## 🧱 Formatting of Suggestions

If multiple fixes apply inside a file:

- List them **individually**
- Provide **separate diffs**
- Include a short explanation for each

---

## 🎯 Review Goal

Your primary goal is to:

- Surface **all severe issues (Critical + High)** in the **first review run**
- Provide the **maximum number of issues** in a single pass
- Make fixes easy to apply directly from the suggestions
