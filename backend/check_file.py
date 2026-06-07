import modal
import os

app = modal.App("cartoon-backend")
image = modal.Image.debian_slim().add_local_dir(".", remote_path="/root").add_local_dir("../kaggle_notebook", remote_path="/kaggle_notebook")

@app.function(image=image)
def check_file():
    paths = [
        "/kaggle_notebook/notebook.ipynb",
        "../kaggle_notebook/notebook.ipynb",
        "kaggle_notebook/notebook.ipynb"
    ]
    for p in paths:
        print(f"{p}: exists={os.path.exists(p)}")
        
if __name__ == "__main__":
    with app.run():
        check_file.remote()
