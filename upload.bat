rem Delete everything inside the dist folder
if exist dist (
    rd /s /q dist
    mkdir dist
)
python -m build
twine upload dist/*
