# Create empty __init__.py if missing
echo. > app\__init__.py
echo. > tasks\__init__.py

git add .
git commit -m "Fix: add missing __init__.py files"
git push