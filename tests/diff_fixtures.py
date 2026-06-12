MODIFIED_DIFF = """\
diff --git a/app/calc.py b/app/calc.py
index 1111111..2222222 100644
--- a/app/calc.py
+++ b/app/calc.py
@@ -1,5 +1,8 @@
 def add(a, b):
     return a + b

-def sub(a, b):
-    return a + b
+def sub(a, b):
+    return a - b
+
+def mul(a, b):
+    return a * b
"""

NEW_FILE_DIFF = """\
diff --git a/app/util.py b/app/util.py
new file mode 100644
index 0000000..59ce92b
--- /dev/null
+++ b/app/util.py
@@ -0,0 +1,5 @@
+def divide(total, count):
+    return total / count
+
+def is_even(n):
+    return n % 2 == 0
"""

DELETED_DIFF = """\
diff --git a/app/old.py b/app/old.py
deleted file mode 100644
index 59ce92b..0000000
--- a/app/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-x = 1
-y = 2
"""

RENAME_DIFF = """\
diff --git a/app/before.py b/app/after.py
similarity index 90%
rename from app/before.py
rename to app/after.py
index 1111111..2222222 100644
--- a/app/before.py
+++ b/app/after.py
@@ -1,2 +1,2 @@
 x = 1
-y = 2
+y = 3
"""

BINARY_DIFF = """\
diff --git a/logo.png b/logo.png
index 1111111..2222222 100644
Binary files a/logo.png and b/logo.png differ
"""
