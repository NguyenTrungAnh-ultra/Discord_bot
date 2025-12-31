# Unused Files

This directory contains files and folders that were identified as unused or legacy during the restructuring of the project to a Modular Monolith architecture.

## Contents

-   **core_old/**: Previous `core` directory containing legacy utilities or configs that were merged into `src/core` and `src/utils`.
-   **BCTC/**: Financial report data/scripts not currently referenced by the main bot modules.
-   **News/**: Legacy news module folder (if present).
-   **No_need/**: Other miscellaneous unused scripts.

## Restoration

If you find that any function is missing, check these folders. You can restore them by moving the file back to `src/modules` or `src/utils` and updating the imports.
