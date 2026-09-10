## 2024-05-15 - Missing Label Associations in Forms
**Learning:** Found a pattern where form fields (like in the Login component) have `<label>` tags that visually look like labels, but lack explicit programmatic association (`htmlFor` linking to an `id` on the `<input>`). This breaks accessibility for screen reader users and reduces the clickable area for all users (clicking a real label should focus the input).
**Action:** When creating or reviewing forms in this app, ensure every `<label>` has an `htmlFor` attribute that exactly matches the `id` of its corresponding input element.
