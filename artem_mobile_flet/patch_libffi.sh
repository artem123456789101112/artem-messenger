#!/bin/bash
echo "Applying libffi patches..."
find . -name "configure.ac" -type f 2>/dev/null | while read f; do
    echo "Patching \"
    sed -i 's/AC_PROG_LD/AC_PROG_LD\\nAC_PROG_LD_GNU/' "\" 2>/dev/null || true
    sed -i 's/AC_TRY_RUN/AC_RUN_IFELSE/' "\" 2>/dev/null || true
    sed -i 's/AC_TRY_LINK/AC_LINK_IFELSE/' "\" 2>/dev/null || true
    sed -i 's/AC_TRY_COMPILE/AC_COMPILE_IFELSE/' "\" 2>/dev/null || true
    sed -i 's/AC_HELP_STRING/AS_HELP_STRING/' "\" 2>/dev/null || true
    echo "m4_ifdef([LT_SYS_SYMBOL_USCORE], [LT_SYS_SYMBOL_USCORE])" >> "\"
done
echo "Patches applied!"
