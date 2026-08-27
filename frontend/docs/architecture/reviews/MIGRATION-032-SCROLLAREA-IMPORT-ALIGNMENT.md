# Migration 032 - ScrollArea Import Alignment

## 1. Migration Purpose

Migration 032 removes an obsolete runtime React namespace import from the
canonical ScrollArea UI primitive while preserving its JSX, props, exports,
styling, and runtime behavior.

## 2. Exact Initial Diagnostic

Before migration:

```text
src/components/ui/scroll-area.tsx(3,1): error TS6133: 'React' is declared but its value is never read.
```

Diagnostic classification:

- code: `TS6133`
- file: `frontend/src/components/ui/scroll-area.tsx`
- line: `3`
- unused symbol: `React`
- import kind: runtime namespace import
- other diagnostics in same file: none

## 3. JSX Runtime Configuration

`frontend/tsconfig.app.json` uses:

```json
"jsx": "react-jsx"
```

The automatic JSX runtime is enabled, so files that only use JSX do not require
a runtime `React` import.

`verbatimModuleSyntax` is also enabled, so type-only imports must be explicit
when needed.

## 4. Imports Before Migration

Before:

```typescript
import * as React from "react"
import { ScrollArea as ScrollAreaPrimitive } from "@base-ui/react/scroll-area"
import { cn } from "src/lib/utils"
```

## 5. Imports After Migration

After:

```typescript
import { ScrollArea as ScrollAreaPrimitive } from "@base-ui/react/scroll-area"
import { cn } from "src/lib/utils"
```

## 6. Runtime React Usage Disposition

No runtime React API is used in `scroll-area.tsx`.

The runtime namespace import was removed.

## 7. React Type Usage Disposition

No React namespace types or named React types are used in `scroll-area.tsx`.

No `import type` was required.

The prop contracts continue to use Base UI primitive types:

- `ScrollAreaPrimitive.Root.Props`
- `ScrollAreaPrimitive.Scrollbar.Props`

## 8. Canonical ScrollArea Owner

Canonical owner:

```text
frontend/src/components/ui/scroll-area.tsx
```

No second ScrollArea implementation was found.

## 9. Export Disposition

Exports are unchanged:

```typescript
export { ScrollArea, ScrollBar }
```

No default export was added.

No component barrel change was required.

## 10. Files Inspected

- `frontend/src/components/ui/scroll-area.tsx`
- `frontend/src/components/ui/`
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/tsconfig.app.json`
- `frontend/package.json`
- ADR-008
- ADR-009
- Migration 028
- Migration 031

## 11. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-032-SCROLLAREA-IMPORT-ALIGNMENT.md`

## 12. Files Modified

- `frontend/src/components/ui/scroll-area.tsx`

## 13. Compiler Errors Before

Pre-migration baseline:

```text
105 TypeScript errors
```

## 14. Compiler Errors After

Post-migration result:

```text
104 TypeScript errors
```

## 15. Net Reduction

```text
105 -> 104
```

Net reduction:

```text
1 TypeScript error
```

## 16. ScrollArea Diagnostics Before and After

Before:

- `TS6133`: unused `React` namespace import in `scroll-area.tsx`

After:

- no `scroll-area.tsx`
- no `ScrollArea`
- no `ScrollBar`

diagnostics remain.

## 17. New Diagnostics

No new diagnostics were introduced.

Remaining React-related diagnostics now originate from `src/main.tsx`, not
from ScrollArea.

## 18. Runtime Behavior Confirmation

Runtime JSX is unchanged:

- same `ScrollAreaPrimitive.Root`
- same viewport
- same `ScrollBar`
- same corner
- same scrollbar orientation default
- same thumb
- same classes
- same public props
- same named exports

Only an unused import was removed.

## 19. Invariants Verified

- ScrollArea has one canonical implementation.
- Runtime imports correspond to runtime usage.
- No React type imports are needed.
- Automatic JSX runtime conventions are respected.
- `verbatimModuleSyntax` remains respected.
- Public ScrollArea props are unchanged.
- Public exports are unchanged.
- Styling and rendering behavior are unchanged.
- No unrelated UI primitive was changed.
- No backend file was changed.

## 20. Rollback Boundary

Rollback is limited to:

- `frontend/src/components/ui/scroll-area.tsx`
- this review document

No component barrel, layout, route, provider, store, service, query, navigation,
backend, or DTO rollback is required.

## 21. Recommended Next Migration

Recommended next migration:

```text
Common Mutation Factory Arity Alignment
```

The next top compiler diagnostics are:

```text
src/hooks/queries/common/useCreateEntity.ts(104,26): error TS2554: Expected 4 arguments, but got 3.
src/hooks/queries/common/useDeleteEntity.ts(104,26): error TS2554: Expected 4 arguments, but got 3.
src/hooks/queries/common/useUpdateEntity.ts(114,26): error TS2554: Expected 4 arguments, but got 3.
```
