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
    import time as t
    t.sleep(240)
    import subprocess
    o = subprocess.run("tail -6 /root/kvboot.log; echo ==; cat /tmp/pinggy.log 2>/dev/null | tail -2; echo ==MARK==; grep -h KVPS /root/kvboot.log 2>/dev/null | tail -3", shell=True, capture_output=True, text=True).stdout
    print(o)
    print("KVPSFINISHED")
    return (t,)


if __name__ == "__main__":
    app.run()
