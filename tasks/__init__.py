# Move misplaced files (optional, won't cause build failure)
mkdir tests scripts
move test_graders.py tests\
move validate-submission.sh scripts\

git add .
git commit -m "Fix repo structure"
git push