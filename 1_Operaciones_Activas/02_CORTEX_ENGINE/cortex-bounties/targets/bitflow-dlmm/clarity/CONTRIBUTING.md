# Contributing

Thank you for your interest in contributing to the DLMM fuzzing suite! This guide will help you add new fuzz targets, invariants, and improvements.

## Adding a New Fuzz Target

1. **Create a new test file** in `fuzz/`:
   ```typescript
   // fuzz/my-new-target.test.ts
   import { describe, it, expect, beforeEach } from 'vitest';
   import { setupTestEnvironment } from '../tests/helpers/helpers';
   
   describe('My New Fuzz Target', () => {
     beforeEach(async () => {
       setupTestEnvironment();
     });
     
     it('should fuzz my target', async () => {
       // Your fuzzing logic here
     });
   });
   ```

2. **Add npm script** in `package.json`:
   ```json
   "fuzz:my-target": "vitest run fuzz/my-new-target.test.ts"
   ```

3. **Update README.md** to document your new target

## Adding a New Invariant

1. **Add invariant function** in `fuzz/properties/invariants.ts`:
   ```typescript
   export function checkMyNewInvariant(
     beforeState: SomeState,
     afterState: SomeState,
     // ... other parameters
   ): InvariantCheckResult {
     const errors: string[] = [];
     
     // Check your invariant
     if (/* condition violated */) {
       errors.push('Description of violation');
     }
     
     return { passed: errors.length === 0, errors };
   }
   ```

2. **Use in fuzz targets**:
   ```typescript
   import { checkMyNewInvariant } from './properties/invariants';
   
   // In your fuzz test
   const result = checkMyNewInvariant(beforeState, afterState);
   if (!result.passed) {
     // Handle violation
   }
   ```

3. **Document in `fuzz/properties/README.md`**:
   - What the invariant checks
   - Why it matters
   - When it's used

## Code Style

- Use TypeScript with strict type checking
- Follow existing code patterns
- Use descriptive variable names
- Add comments for complex logic
- Keep functions focused and testable

## Testing Your Changes

Before submitting:

1. **Run unit tests**:
   ```bash
   npm run test:unit
   ```

2. **Run your new fuzz target**:
   ```bash
   npm run fuzz:my-target
   ```

3. **Run all fuzz targets**:
   ```bash
   npm run fuzz
   ```

4. **Check for linting errors**:
   ```bash
   npm run lint  # if available
   ```

## File Organization

- **Fuzz targets**: `fuzz/*.test.ts`
- **Invariants**: `fuzz/properties/invariants.ts`
- **Fuzz-specific helpers**: `fuzz/harnesses/`
- **Shared test helpers**: `tests/helpers/`
- **Unit tests**: `tests/core/`, `tests/routers/`

## Commit Messages

Use clear, descriptive commit messages:
- `feat: add new fuzz target for X`
- `fix: correct invariant check for Y`
- `docs: update README with new target`
- `refactor: reorganize helper functions`

## Questions?

- Check existing fuzz targets for examples
- Review `fuzz/properties/invariants.ts` for invariant patterns
- Look at `tests/helpers/helpers.ts` for available utilities

