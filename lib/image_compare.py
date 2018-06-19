import sys
import os


def script_data():
    with open(os.path.join(sys.prefix, "share", "image-compare")) as f:
        data = f.read()
    return data


def template_data():
    with open(os.path.join(sys.prefix, "share", "diff.html")) as f:
        data = f.read()
    return data


def compare(img1, img2, outpath):
    """
    Builds the comparison HTML for img1 and img2 at outpath
    """
    tmpl = Template(template_data())
    with codecs.open(outpath, "w", 'utf-8') as out:
        out.write(tmpl.render(script=script_data(), image_1=img1, image_2=img2))


def view_images(img1, img2):
    """
    Create a tempfile and open it in the browser; when the browser exits, delete the file.
    """

    img1 = os.path.abspath(img1)
    img2 = os.path.abspath(img2)

    import tempfile
    _, f = tempfile.mkstemp()
    compare(img1, img2, f)
    import webbrowser
    webbrowser.open("file://" + f)
    raw_input("Press enter to end viewing...")
    os.unlink(f)
