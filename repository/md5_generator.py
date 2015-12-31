import hashlib

with open("addons.xml", "r") as addons_file:
    m = hashlib.md5(addons_file.read()).hexdigest()
    with open("addons.xml.md5", "w") as md5_file:
        md5_file.write(m)