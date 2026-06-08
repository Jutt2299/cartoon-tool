import modal
app = modal.App("test-diffusers")
@app.function(image=modal.Image.debian_slim().pip_install("diffusers==0.38.0"))
def f():
    import diffusers
    print([x for x in dir(diffusers) if 'ltx' in x.lower() or 'video' in x.lower()])

if __name__ == "__main__":
    with app.run():
        f.remote()
